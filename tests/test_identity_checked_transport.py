"""Executable synthetic end-to-end acceptance of BOP's merged method spine.

Unlike the existing separate provenance, identity and group-gain unit tests,
these checks actually run their combined public APIs in order, with a real
training-only *managed categorical fit* on generated source-schema rows.
Never request or read any real BOP/Dryad tracking data.
"""
from __future__ import annotations

from dataclasses import replace
import json

import pytest

from odsp.common_input_transport import (
    CLASSES, freeze_common_input_transport
)
from odsp.identity_checked_transport import (
    calibrate_identity_checked_transport,
    freeze_identity_checked_transport,
    validate_identity_checked_transport,
)


SPECIES=("Buteo buteo", "Circus aeruginosus")
SOURCE={"training":"BOP","calibration":"DRYAD","validation":"DRYAD"}


def _sources(cal_count=9):
    training=[]
    calibration=[]
    validation=[]
    for si,species in enumerate(SPECIES):
        for group_index in range(3):
            for event in range(8):
                training.append({
                    "row_id":f"T_{si}_{group_index}_{event}",
                    "individual-local-identifier":f"train_{si}_{group_index}",
                    "individual-taxon-canonical-name":species,
                    "timestamp":f"2025-06-08T{'11' if event%2 else '23'}:{(event*3)%60:02d}:00Z",
                    "location-long":4.35,
                    "height-above-msl":(
                        10.0,110.0,310.0,750.0
                    )[(event+group_index)%4],
                })
        for role,n,store in (
            ("calibration",cal_count,calibration),
            ("validation",2,validation),
        ):
            for group_index in range(n):
                for event in range(4):
                    store.append({
                        "row_id":f"{role}_{si}_{group_index}_{event}",
                        "individual.global.identifier":f"{role}_{si}_{group_index}",
                        "individual.taxon.canonical.name":species,
                        "timestamp":f"2025-06-08T{'11' if event%2 else '23'}:{(event*5)%60:02d}:00Z",
                        "location.long.rnd":4.3,
                    })
    return training,calibration,validation


def _identity_from_frozen(transport):
    """An artificial cross-source crosswalk; not a real biological attestation."""
    train={}
    for row in transport.forecast.training_rows:
        train[row.group_id]=row.stratum
    calib={r.group_id:r.stratum for r in transport.forecast.plan.calibration_rows}
    valida={r.group_id:r.stratum for r in transport.forecast.plan.validation_rows}
    out={}
    for role,group_map in (
        ("training",train),("calibration",calib),("validation",valida)
    ):
        out[role]=[
            {
                "group_id":g,
                "entity_key":f"SYNTHETIC_CANONICAL_ANIMAL/{role}/{g}",
                "stratum":species,
                "source":SOURCE[role],
                "study_cluster":"SYNTHETIC_TRAINING_STUDY"
                    if role=="training" else "SYNTHETIC_TARGET_STUDY",
            }
            for g,species in sorted(group_map.items())
        ]
    return out


def _freeze(cal_count=9):
    train,cal,val=_sources(cal_count)
    transport=freeze_common_input_transport(
        training_BOP_rows=train,
        calibration_Dryad_features=cal,
        validation_Dryad_features=val,
        evidence_role="known_truth_synthetic_only",
    )
    return transport,_identity_from_frozen(transport),cal,val


def _admit(transport,metadata,role="known_truth_synthetic_only"):
    return freeze_identity_checked_transport(
        transport,
        training_metadata=metadata["training"],
        calibration_metadata=metadata["calibration"],
        validation_metadata=metadata["validation"],
        evidence_role=role,
    )


def _states(rows):
    return {
        row["row_id"]:CLASSES[0 if "T11:" in row["timestamp"] else 3]
        for row in rows
    }


def test_actual_training_fit_identity_gate_calibration_then_untouched_validation():
    transport,metadata,cal,val=_freeze()
    checked=_admit(transport,metadata)
    manifest=checked.as_public_dict()
    assert manifest["status"]=="COUNT_GATE_PASSED_EXCHANGEABILITY_NOT_PROVED"
    assert manifest["identity_evidence_role"]=="known_truth_synthetic_only"
    assert manifest["training_source_species_reconciled"] is True
    assert manifest["training_model_and_holdout_forecasts_replayed"] is True
    assert manifest["calibration_group_count"]==18
    assert manifest["untouched_validation_group_count"]==4
    assert len(manifest["strata"])==2
    assert all(s["one_sided_lower_rank"]==1 for s in manifest["strata"])
    assert all(s["training_animals"]==3 for s in manifest["strata"])
    assert all(s["calibration_animals"]==9 for s in manifest["strata"])
    assert all(s["untouched_validation_animals"]==2 for s in manifest["strata"])
    assert manifest["exchangeability_proven_by_software"] is False
    assert manifest["real_Dryad_candidate_admitted"] is False
    assert manifest["original_bop_empirical_terminal"]=="empirical_state_prediction_mixed"
    assert "SYNTHETIC_CANONICAL_ANIMAL" not in json.dumps(manifest)
    assert "SYNTHETIC_TARGET_STUDY" not in json.dumps(manifest)
    assert "train_0_0" not in json.dumps(manifest)

    frozen_plan=transport.forecast.plan.digest
    calibrated=calibrate_identity_checked_transport(checked,_states(cal))
    scored=validate_identity_checked_transport(checked,calibrated,_states(val))
    assert scored.plan_sha256==frozen_plan
    assert scored.calibration_sha256==calibrated.calibration_sha256
    assert scored.validation_group_count==4
    assert len(scored.strata)==2
    assert all(s.finite_rank==1 and not s.vacuous for s in scored.strata)
    assert scored.as_public_dict()["historical_bop_terminal_changed"] is False
    assert transport.forecast.plan.digest==frozen_plan


def test_one_bird_reused_under_different_provider_names_rejected_before_scores():
    transport,metadata,_,_=_freeze()
    metadata["validation"][0]["entity_key"]=metadata["training"][0]["entity_key"]
    with pytest.raises(ValueError,match="canonical animal entity reused"):
        _admit(transport,metadata)


def test_training_source_stratum_must_be_the_ACTUAL_fitted_stratum_not_metadata():
    transport,metadata,_,_=_freeze()
    # The generic frozen prediction plan stores training group IDs but not
    # training species. Only the executable training source resolves this.
    metadata["training"][0]["stratum"]=SPECIES[1]
    with pytest.raises(ValueError,match="differs from fitted training source"):
        _admit(transport,metadata)


def test_rank_count_eight_calibration_animals_is_hold_not_positive_endpoint():
    transport,metadata,_,_=_freeze(cal_count=8)
    with pytest.raises(ValueError,match="identity/rank count gate HOLD"):
        _admit(transport,metadata)


def test_metadata_source_mutations_after_freeze_cannot_rewrite_snapshot():
    transport,metadata,cal,val=_freeze()
    checked=_admit(transport,metadata)
    metadata["calibration"][0]["entity_key"]="MUTATED_SINCE_FREEZE"
    metadata["training"].pop()
    # Snapshot remains exactly what was admitted; it does not alias the
    # caller's editable list or dictionaries.
    checked.assert_replayed()
    s=validate_identity_checked_transport(
        checked,calibrate_identity_checked_transport(checked,_states(cal)),
        _states(val),
    )
    assert s.validation_group_count==4


def test_private_crosswalk_or_gate_tampering_is_detected_before_calibration():
    transport,metadata,cal,_=_freeze()
    checked=_admit(transport,metadata)
    rosters=list(checked.group_records_by_role)
    name,training=rosters[0]
    rosters[0]=(name,(
        replace(training[0],entity_key="UNREGISTERED_ANIMAL"),
        *training[1:],
    ))
    attacked=replace(checked,group_records_by_role=tuple(rosters))
    with pytest.raises(ValueError,match="snapshot changed"):
        calibrate_identity_checked_transport(attacked,_states(cal))

    fake_gate=replace(
        checked.admission,status="HOLD_IDENTITY_EVIDENCE_UNVERIFIED"
    )
    attacked_gate=replace(checked,admission=fake_gate)
    with pytest.raises(ValueError,match="previously admitted"):
        calibrate_identity_checked_transport(attacked_gate,_states(cal))


def test_forecast_or_model_tampering_blocked_at_rechecked_identity_layer():
    transport,metadata,cal,val=_freeze()
    checked=_admit(transport,metadata)
    altered_plan=replace(
        transport.forecast.plan,
        calibration_rows=(
            replace(transport.forecast.plan.calibration_rows[0],
                    conditional=(0.4,0.3,0.2,0.1)),
            *transport.forecast.plan.calibration_rows[1:],
        ),
    )
    attacked=replace(
        checked,transport=replace(
            transport,forecast=replace(
                transport.forecast,plan=altered_plan
            )
        )
    )
    with pytest.raises(ValueError,match="frozen forecast plan|model/source retraining"):
        calibrate_identity_checked_transport(attacked,_states(cal))
    attacked_model=replace(
        checked,transport=replace(
            transport,forecast=replace(
                transport.forecast,
                model_artifact=transport.forecast.model_artifact+b"tampered",
            ),
        ),
    )
    with pytest.raises(ValueError,match="retraining replay"):
        validate_identity_checked_transport(
            attacked_model,
            calibrate_identity_checked_transport(checked,_states(cal)),
            _states(val),
        )


def test_calibration_and_validation_state_rosters_never_cross_roles():
    transport,metadata,cal,val=_freeze()
    checked=_admit(transport,metadata)
    with pytest.raises(ValueError,match="only exact frozen Dryad role outcome IDs"):
        calibrate_identity_checked_transport(
            checked,{**_states(cal),**_states(val)}
        )
    calibrated=calibrate_identity_checked_transport(checked,_states(cal))
    with pytest.raises(ValueError,match="only exact frozen Dryad role outcome IDs"):
        validate_identity_checked_transport(checked,calibrated,_states(cal))


def test_real_source_admission_cannot_be_inferred_from_synthetic_example():
    transport,metadata,cal,_=_freeze()
    with pytest.raises(ValueError,match="NOT_ADMITTED"):
        _admit(transport,metadata,role="claimed_real_cross_study_validation")
    bad_transport=replace(transport,protocol="externally_admitted")
    with pytest.raises(ValueError,match="NOT_ADMITTED"):
        _admit(bad_transport,metadata)
    checked=_admit(transport,metadata)
    assert checked.as_public_dict()["real_BOP_or_Dryad_empirical_assessment"] is False
    assert checked.as_public_dict()["identity_crosswalk_proven_by_software"] is False


def test_sample_source_namespaces_are_explicit_but_not_biological_proof():
    transport,metadata,_,_=_freeze()
    checked=_admit(transport,metadata)
    assert metadata["training"][0]["group_id"].startswith("BOP:")
    assert metadata["calibration"][0]["group_id"].startswith("DRYAD:")
    assert checked.as_public_dict()["biological_independence_proven_by_software"] is False
