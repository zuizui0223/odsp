from __future__ import annotations

from dataclasses import replace
import json

import pytest

from odsp.fixed_group_gain_protocol import freeze_fixed_group_forecasts
from odsp.group_identity_gate import audit_frozen_group_identity_support


MODEL=b"opaque frozen synthetic training-only model bytes"
REF=b"opaque synthetic training-only reference bytes"
SOURCE_SHA="a"*64
SOURCES={"training":"BOP","calibration":"DRYAD","validation":"DRYAD"}


def _fixture(
    *,
    A=(3,9,2),
    B=(3,9,2),
    identity_role="externally_attested_identity_crosswalk",
):
    """Only artificial metadata, never GPS, altitude or model outcomes."""
    strata={"Buteo buteo":A,"Circus aeruginosus":B}
    allmetadata={role:[] for role in SOURCES}
    forecasts={"calibration":[],"validation":[]}
    for stratum,counts in strata.items():
        for role,n in zip(("training","calibration","validation"),counts):
            for i in range(n):
                group=f"{SOURCES[role]}/{role}/{stratum}/{i}"
                allmetadata[role].append({
                    "group_id":group,
                    "entity_key":f"CANONICAL_ANIMAL/{role}/{stratum}/{i}",
                    "stratum":stratum,
                    "source":SOURCES[role],
                    "study_cluster":"SOURCE_STUDY_A" if role=="training" else "SOURCE_STUDY_B",
                })
                if role!="training":
                    forecasts[role].append({
                        "row_id":f"{group}/synthetic_event0",
                        "group_id":group,"stratum":stratum,
                        "conditional":[0.7,0.3],
                        "reference":[0.5,0.5],
                    })
    plan=freeze_fixed_group_forecasts(
        training_group_ids=[r["group_id"] for r in allmetadata["training"]],
        calibration_forecasts=forecasts["calibration"],
        validation_forecasts=forecasts["validation"],
        classes=["state_0","state_1"],
        model_artifact=MODEL,
        reference_artifact=REF,
        training_source_sha256=SOURCE_SHA,
        miscoverage=0.1,
    )
    return plan,allmetadata,identity_role


def _audit(plan,meta,role="externally_attested_identity_crosswalk"):
    return audit_frozen_group_identity_support(
        plan,
        training_metadata=meta["training"],
        calibration_metadata=meta["calibration"],
        validation_metadata=meta["validation"],
        model_artifact=MODEL,
        reference_artifact=REF,
        expected_source_by_role=SOURCES,
        group_identity_attestation=role,
    )


def test_study_namespaces_not_evidence_but_external_canonical_ids_checked():
    plan,meta,role=_fixture()
    out=_audit(plan,meta,role)
    view=out.as_public_dict()
    assert out.status=="COUNT_GATE_PASSED_EXCHANGEABILITY_NOT_PROVED"
    assert view["calibration_group_count"]==18
    assert view["untouched_validation_group_count"]==4
    assert view["canonical_entity_collision_count"]==0
    assert view["exchangeability_proven_by_software"] is False
    assert view["identity_crosswalk_proven_by_software"] is False
    assert view["biological_independence_proven_by_software"] is False
    assert view["real_Dryad_candidate_admitted"] is False
    assert view["original_bop_empirical_terminal"]=="empirical_state_prediction_mixed"
    assert len(view["strata"])==2
    assert all(x["one_sided_lower_rank"]==1 for x in view["strata"])
    assert all(x["nonvacuous_group_lower_bound_possible"] for x in view["strata"])
    assert all(x["target_shared_calibration_validation_study_clusters"]==1
               for x in view["strata"])
    # Public output is intentionally aggregate only: no animal or study IDs.
    exposed=json.dumps(view)
    assert "CANONICAL_ANIMAL" not in exposed
    assert "SOURCE_STUDY_A" not in exposed
    assert "BOP/training/" not in exposed


def test_eight_calibration_animals_are_vacuous_in_one_species_even_if_pooled_is_large():
    plan,meta,_=_fixture(A=(3,19,2),B=(3,8,2))
    out=_audit(plan,meta)
    assert out.status=="HOLD_SOME_STRATA_HAVE_VACUOUS_RANK"
    grouped={x.stratum:x for x in out.strata}
    assert grouped["Buteo buteo"].one_sided_lower_rank==2
    assert grouped["Circus aeruginosus"].one_sided_lower_rank==0
    assert not grouped["Circus aeruginosus"].nonvacuous_group_lower_bound_possible
    assert out.calibration_group_count==27


def test_no_attribution_of_cross_study_independence_without_attestation():
    plan,meta,_=_fixture()
    out=_audit(plan,meta,role="unverified")
    assert out.status=="HOLD_IDENTITY_EVIDENCE_UNVERIFIED"
    assert out.as_public_dict()["real_Dryad_candidate_admitted"] is False


def test_correct_source_prefixed_group_ids_can_hide_the_same_real_animal():
    plan,meta,_=_fixture()
    same=meta["training"][0]["entity_key"]
    # Target has a distinct group name, but supplied external crosswalk
    # says this is the *same tagged animal* reused in target validation.
    meta["validation"][0]["entity_key"]=same
    with pytest.raises(ValueError,match="canonical animal entity reused"):
        _audit(plan,meta)


def test_two_tag_deployments_of_one_animal_are_not_two_independent_groups():
    plan,meta,_=_fixture()
    meta["calibration"][1]["entity_key"]=meta["calibration"][0]["entity_key"]
    with pytest.raises(ValueError,match="canonical animal entity reused"):
        _audit(plan,meta)


@pytest.mark.parametrize("attack, message", [
    ("missing_group","group roster differs"),
    ("duplicate_group","group roster differs"),
    ("new_unplanned_group","group roster differs"),
    ("leaked_outcome","schema must exclude outcomes"),
    ("leaked_altitude","schema must exclude outcomes"),
    ("source_wrong","unexpected source"),
    ("stratum_wrong","forecast stratum conflicts"),
    ("empty_identity","nonempty stripped"),
    ("extra_metadata","schema must exclude outcomes"),
])
def test_unsupported_or_outcome_leaking_metadata_rejected(attack,message):
    plan,meta,_=_fixture()
    if attack=="missing_group":
        meta["calibration"].pop()
    elif attack=="duplicate_group":
        meta["calibration"].append(dict(meta["calibration"][0]))
    elif attack=="new_unplanned_group":
        meta["calibration"][0]["group_id"]="DRYAD/unplanned"
    elif attack=="leaked_outcome":
        meta["validation"][0]["outcome"]="secret_class"
    elif attack=="leaked_altitude":
        meta["validation"][0]["height.above.msl"]=120
    elif attack=="source_wrong":
        meta["calibration"][0]["source"]="BOP"
    elif attack=="stratum_wrong":
        meta["validation"][0]["stratum"]="Circus cyaneus"
    elif attack=="empty_identity":
        meta["validation"][0]["entity_key"]=""
    elif attack=="extra_metadata":
        meta["training"][0]["timestamp"]="2025-01-01T00:00:00Z"
    with pytest.raises(ValueError,match=message):
        _audit(plan,meta)


def test_model_and_reference_mutation_or_unfrozen_forecast_fail():
    plan,meta,_=_fixture()
    with pytest.raises(ValueError,match="frozen model artifact"):
        audit_frozen_group_identity_support(
            plan,
            training_metadata=meta["training"],
            calibration_metadata=meta["calibration"],
            validation_metadata=meta["validation"],
            model_artifact=MODEL+b"_TUNED",reference_artifact=REF,
            expected_source_by_role=SOURCES,
            group_identity_attestation="synthetic_known_truth",
        )
    changed_plan=replace(
        plan,validation_rows=(replace(
            plan.validation_rows[0],conditional=(0.8,0.2)
        ),*plan.validation_rows[1:])
    )
    with pytest.raises(ValueError,match="frozen forecast plan"):
        _audit(changed_plan,meta)


def test_one_training_animal_per_stratum_cannot_create_a_supported_fitted_learner():
    plan,meta,_=_fixture(A=(1,9,2),B=(3,9,2))
    out=_audit(plan,meta)
    assert out.status=="HOLD_SOME_STRATA_HAVE_VACUOUS_RANK"
    assert not {x.stratum:x for x in out.strata}["Buteo buteo"].sufficient_training_animal_groups


@pytest.mark.parametrize("role",["", "this_establishes_independence",None])
def test_unrecognized_attestation_roles_are_rejected(role):
    plan,meta,_=_fixture()
    with pytest.raises(ValueError,match="explicit identity attestation"):
        _audit(plan,meta,role=role)
