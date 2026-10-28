"""Outcome-blind, cross-source canonical-entity admission gate for ODSP.

A grouped prediction plan freezes source model/reference and forecast rows,
but source-prefixed animal IDs DO NOT establish biological nonoverlap between
studies. This extra preflight requires one distinct externally mapped
*canonical animal identity* for each planned independent group. It catches
reused/duplicated entities, absent model support and vacuous within-stratum
rank inference using no observed altitude, GPS or validation scores.

It does NOT prove the supplied crosswalk authentic, independent sampling,
target calibration/test score exchangeability, or positive predictor gain.
The real Dryad sample remains NOT_ADMITTED.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from .fixed_group_gain_protocol import FrozenGroupForecastPlan

_FIELDS=frozenset({"group_id","entity_key","stratum","source","study_cluster"})
_ROLES=("training","calibration","validation")
_ATTESTATIONS=frozenset({
    "synthetic_known_truth",
    "externally_attested_identity_crosswalk",
    "unverified",
})


@dataclass(frozen=True)
class GroupIdentityRecord:
    group_id:str
    entity_key:str
    stratum:str
    source:str
    study_cluster:str


@dataclass(frozen=True)
class StratumIdentitySupport:
    stratum:str
    training_animals:int
    calibration_animals:int
    untouched_validation_animals:int
    one_sided_lower_rank:int
    nonvacuous_group_lower_bound_possible:bool
    sufficient_training_animal_groups:bool
    training_study_clusters:int
    target_calibration_study_clusters:int
    target_validation_study_clusters:int
    target_shared_calibration_validation_study_clusters:int

    def public(self)->dict[str,object]:
        return {
            "stratum":self.stratum,
            "training_animals":self.training_animals,
            "calibration_animals":self.calibration_animals,
            "untouched_validation_animals":self.untouched_validation_animals,
            "one_sided_lower_rank":self.one_sided_lower_rank,
            "nonvacuous_group_lower_bound_possible":
                self.nonvacuous_group_lower_bound_possible,
            "sufficient_training_animal_groups":
                self.sufficient_training_animal_groups,
            "training_study_clusters":self.training_study_clusters,
            "target_calibration_study_clusters":
                self.target_calibration_study_clusters,
            "target_validation_study_clusters":
                self.target_validation_study_clusters,
            "target_shared_calibration_validation_study_clusters":
                self.target_shared_calibration_validation_study_clusters,
        }


@dataclass(frozen=True)
class IdentityAdmissionGate:
    """Counts-only evidence; never serializes IDs, metadata rows or GPS."""

    frozen_forecast_plan_sha256:str
    group_identity_attestation:str
    expected_source_by_role:tuple[tuple[str,str],...]
    strata:tuple[StratumIdentitySupport,...]
    status:str
    calibration_group_count:int
    untouched_validation_group_count:int
    miscoverage:float

    def as_public_dict(self)->dict[str,object]:
        return {
            "schema_version":1,
            "evidence_role":"outcome_blind_entity_identity_and_rank_count_preflight",
            "frozen_forecast_plan_sha256":self.frozen_forecast_plan_sha256,
            "group_identity_attestation":self.group_identity_attestation,
            "expected_source_by_role":dict(self.expected_source_by_role),
            "strata":[s.public() for s in self.strata],
            "status":self.status,
            "calibration_group_count":self.calibration_group_count,
            "untouched_validation_group_count":
                self.untouched_validation_group_count,
            "miscoverage":self.miscoverage,
            "canonical_entity_collision_count":0,
            "raw_group_or_animal_identifiers_exposed":False,
            "original_bop_empirical_terminal":"empirical_state_prediction_mixed",
            "historical_BOP_RF_direct_Dryad_validation_performed":False,
            "BOP_same_study_2026_count_gate_reopened":False,
            "real_Dryad_candidate_admitted":False,
            "exchangeability_proven_by_software":False,
            "identity_crosswalk_proven_by_software":False,
            "biological_independence_proven_by_software":False,
        }


def _id(value:object)->str:
    if not isinstance(value,str) or not value or value!=value.strip():
        raise ValueError("all identity metadata keys must be nonempty stripped strings")
    return value


def _parse(
    role:str, items:Sequence[Mapping[str,object]], expected_source:str,
)->tuple[GroupIdentityRecord,...]:
    if isinstance(items,(str,bytes)) or not items:
        raise ValueError("identity metadata must contain one record per group")
    result=[]
    for row in items:
        if not isinstance(row,Mapping) or set(row)!=_FIELDS:
            raise ValueError("identity record schema must exclude outcomes and extra fields")
        x={k:_id(row[k]) for k in _FIELDS}
        if x["source"]!=expected_source:
            raise ValueError("unexpected source for frozen role")
        result.append(GroupIdentityRecord(
            x["group_id"],x["entity_key"],x["stratum"],
            x["source"],x["study_cluster"],
        ))
    return tuple(result)


def audit_frozen_group_identity_support(
    plan:FrozenGroupForecastPlan,
    *,
    training_metadata:Sequence[Mapping[str,object]],
    calibration_metadata:Sequence[Mapping[str,object]],
    validation_metadata:Sequence[Mapping[str,object]],
    model_artifact:bytes,
    reference_artifact:bytes,
    expected_source_by_role:Mapping[str,str],
    group_identity_attestation:str,
)->IdentityAdmissionGate:
    """Check exact frozen group rosters and same-animal identity collisions.

    Minimum nonvacuous one-sided rank requires k=floor((n_cal+1)*alpha)>=1.
    For alpha=0.10 that requires >=9 independent calibration animal IDs,
    plus >=1 disjoint untouched validation ID in each stratum. This only
    certifies count *possibility*, never true score exchangeability.
    """
    if not isinstance(plan,FrozenGroupForecastPlan):
        raise ValueError("immutable FrozenGroupForecastPlan is required")
    plan.assert_unchanged(
        model_artifact=model_artifact,reference_artifact=reference_artifact,
    )
    if group_identity_attestation not in _ATTESTATIONS:
        raise ValueError("explicit identity attestation role required")
    if not isinstance(expected_source_by_role,Mapping) or set(expected_source_by_role)!=set(_ROLES):
        raise ValueError("all three role-specific source names must be declared")
    sources={role:_id(expected_source_by_role[role]) for role in _ROLES}

    metadata={
        "training":_parse("training",training_metadata,sources["training"]),
        "calibration":_parse("calibration",calibration_metadata,sources["calibration"]),
        "validation":_parse("validation",validation_metadata,sources["validation"]),
    }
    expected_rosters={
        "training":set(plan.training_group_ids),
        "calibration":{r.group_id for r in plan.calibration_rows},
        "validation":{r.group_id for r in plan.validation_rows},
    }
    observed_rosters={}
    canonical_entities=[]
    for role,rows in metadata.items():
        ids=[r.group_id for r in rows]
        if len(ids)!=len(set(ids)) or set(ids)!=expected_rosters[role]:
            raise ValueError("identity metadata group roster differs from frozen plan")
        observed_rosters[role]=set(ids)
        canonical_entities.extend(r.entity_key for r in rows)
    if any(
        observed_rosters[_ROLES[i]] & observed_rosters[_ROLES[j]]
        for i in range(3) for j in range(i+1,3)
    ):
        raise ValueError("one source group appears in multiple frozen roles")
    # Critically, group names prefixed by their source may differ while the
    # biological individual is the SAME animal across both studies.
    if len(set(canonical_entities))!=len(canonical_entities):
        raise ValueError("canonical animal entity reused in multiple groups or roles")

    for role,forecast in (
        ("calibration",plan.calibration_rows),
        ("validation",plan.validation_rows),
    ):
        declared={r.group_id:r.stratum for r in metadata[role]}
        if any(declared[r.group_id]!=r.stratum for r in forecast):
            raise ValueError("frozen model forecast stratum conflicts with animal identity metadata")
    n_train=Counter(r.stratum for r in metadata["training"])
    n_cal=Counter(r.stratum for r in metadata["calibration"])
    n_val=Counter(r.stratum for r in metadata["validation"])
    strata=sorted(set(n_cal)|set(n_val))
    if not strata:
        raise ValueError("frozen design lacks target groups")
    output=[]
    alpha=plan.miscoverage
    if not math.isfinite(alpha) or not 0<alpha<1:
        raise ValueError("frozen miscoverage must be strictly between zero and one")
    for name in strata:
        ca=n_cal[name]
        va=n_val[name]
        rank=math.floor((ca+1)*alpha)
        clusters={
            role:{r.study_cluster for r in metadata[role] if r.stratum==name}
            for role in _ROLES
        }
        output.append(StratumIdentitySupport(
            stratum=name,
            training_animals=n_train[name],
            calibration_animals=ca,
            untouched_validation_animals=va,
            one_sided_lower_rank=rank,
            nonvacuous_group_lower_bound_possible=(rank>=1 and va>=1),
            sufficient_training_animal_groups=(n_train[name]>=2),
            training_study_clusters=len(clusters["training"]),
            target_calibration_study_clusters=len(clusters["calibration"]),
            target_validation_study_clusters=len(clusters["validation"]),
            target_shared_calibration_validation_study_clusters=len(
                clusters["calibration"] & clusters["validation"]
            ),
        ))
    if group_identity_attestation=="unverified":
        status="HOLD_IDENTITY_EVIDENCE_UNVERIFIED"
    elif any(
        not s.nonvacuous_group_lower_bound_possible
        or not s.sufficient_training_animal_groups
        for s in output
    ):
        status="HOLD_SOME_STRATA_HAVE_VACUOUS_RANK"
    else:
        status="COUNT_GATE_PASSED_EXCHANGEABILITY_NOT_PROVED"
    return IdentityAdmissionGate(
        frozen_forecast_plan_sha256=plan.digest,
        group_identity_attestation=group_identity_attestation,
        expected_source_by_role=tuple((role,sources[role]) for role in _ROLES),
        strata=tuple(output),status=status,
        calibration_group_count=sum(n_cal.values()),
        untouched_validation_group_count=sum(n_val.values()),
        miscoverage=alpha,
    )
