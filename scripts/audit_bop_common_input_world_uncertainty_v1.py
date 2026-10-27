"""Post-result *world-level* Monte Carlo uncertainty for frozen BOP transport.

24 simulated worlds (not 2,880 iid observations) are the independent
Monte Carlo replication units. Every world shares one upstream trained
predictor, one target group calibrator and one lower-rank threshold across
120 synthetic validation animals. Thus the old 2,880 group coverage
fraction is descriptive, but a naive binomial confidence interval over
2,880 pooled groups would disregard common-model/calibrator dependence.

This is explicitly a POST-RESULT descriptive uncertainty calculation.
It neither changes the pre-frozen contract/acceptance nor provides
conditional coverage for each trained model or real BOP/Dryad birds.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from statistics import mean, stdev
from typing import Mapping

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"research/BOP_COMMON_INPUT_V1_WORLD_COUNT_AUDIT_SOURCE.json"
RECEIPT=ROOT/"BOP_COMMON_INPUT_TRANSPORT_V1_VALIDATION_RECEIPT.json"
ORIGINAL_CONTRACT=ROOT/"research/BOP_COMMON_INPUT_TRANSPORT_V1_CONTRACT.json"
_FIXED_COUNTS_SHA256="5efeb87b3a2ec78f6f59f2939048b6b8e71623e1ff58f340fc4ea40afb68dc38"
_T_CRITICAL_DF23_95=2.0686576104190406


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_world_count_digest(worlds:list[dict])->str:
    raw=json.dumps(worlds,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
    return _sha(raw)


def _validate_source(source:Mapping,receipt:Mapping,contract_bytes:bytes)->list[dict]:
    first=receipt["first_execution"]
    design=receipt["design"]
    outcome=receipt["first_result"]
    if (
        source.get("schema_version") != 1
        or source.get("role") != "POST_RESULT_DESCRIPTIVE_WORLD_LEVEL_MONTE_CARLO_AUDIT_NOT_NEW_PRECOMMITTED_TEST"
        or source.get("original_bop_terminal") != "empirical_state_prediction_mixed"
        or source.get("real_bop_or_dryad_gps_accessed") is not False
        or source.get("world_count") != 24
        or source.get("nominal_target_coverage") != 0.9
        or receipt["scientific_boundary"]["real_Dryad_candidate_admitted"] is not False
        or receipt["scientific_boundary"]["original_BOP_RF_direct_external_scoring_validated"] is not False
        or _sha(contract_bytes) != receipt["frozen_contract"]["contract_sha256"]
    ):
        raise ValueError("frozen first-run science or world-count audit role drifted")
    origin=source.get("original_actions")
    if not isinstance(origin,dict) or any(origin.get(k) != first.get(v) for k,v in (
        ("workflow_run_id","workflow_run_id"),
        ("artifact_id","artifact_id"),
        ("artifact_zip_sha256","artifact_zip_sha256"),
        ("original_json_sha256","original_result_json_sha256"),
        ("first_world_audit_sha256","original_result_world_audit_sha256"),
    )):
        raise ValueError("source counts lost original first-run provenance")
    worlds=source.get("worlds")
    if not isinstance(worlds,list) or len(worlds) != design["worlds"]:
        raise ValueError("expected exactly 24 original independent worlds")
    if any(set(row) != {"world","n","same","shift"} for row in worlds):
        raise ValueError("world-count source has extra fields or missing count fields")
    for index,row in enumerate(worlds):
        if (
            any(isinstance(row[k],bool) or not isinstance(row[k],int) for k in row)
            or row["world"] != index or row["n"] != 120
            or not 0 <= row["same"] <= 120
            or not 0 <= row["shift"] <= 120
        ):
            raise ValueError("world row is not a frozen independent group-count record")
    if _canonical_world_count_digest(worlds) != _FIXED_COUNTS_SHA256:
        raise ValueError("24-world group-count trace changed from original archive")
    if (
        sum(r["n"] for r in worlds) != design["validation_independent_animals_per_condition"]
        or sum(r["same"] for r in worlds) != outcome["covered_target_individuals"]
        or sum(r["shift"] for r in worlds) != outcome["covered_validation_shift_individuals"]
        or sum(r["same"] for r in worlds)/2880 != outcome["stable_target_source_group_coverage"]
        or sum(r["shift"] for r in worlds)/2880 != outcome["validation_only_distribution_shift_group_coverage"]
    ):
        raise ValueError("world-count source disagrees with frozen first-run aggregate")
    return worlds


def _world_summary(values:list[float])->dict[str,float]:
    if len(values)!=24 or any(not math.isfinite(x) for x in values):
        raise ValueError("24 independent, finite world rates are required")
    estimate=mean(values)
    sd=stdev(values)
    se=sd/math.sqrt(len(values))
    return {
        "mean":estimate,
        "between_world_sample_sd":sd,
        "independent_world_monte_carlo_se":se,
        "t95_lower":estimate-_T_CRITICAL_DF23_95*se,
        "t95_upper":estimate+_T_CRITICAL_DF23_95*se,
        "min_world":min(values),
        "max_world":max(values),
    }


def audit_world_uncertainty(
    source:Mapping,receipt:Mapping,contract_bytes:bytes,
)->dict[str,object]:
    worlds=_validate_source(source,receipt,contract_bytes)
    stable=[r["same"]/r["n"] for r in worlds]
    shifted=[r["shift"]/r["n"] for r in worlds]
    paired=[a-b for a,b in zip(stable,shifted)]
    p_stable=mean(stable)
    p_shifted=mean(shifted)
    naive_stable=math.sqrt(p_stable*(1-p_stable)/2880)
    naive_shifted=math.sqrt(p_shifted*(1-p_shifted)/2880)
    return {
        "schema_version":1,
        "evidence_role":"POST_RESULT_DESCRIPTIVE_WORLD_LEVEL_PRECISION_AUDIT_NOT_PREREGISTERED",
        "original_source_workflow_run":source["original_actions"]["workflow_run_id"],
        "original_world_count_digest":_FIXED_COUNTS_SHA256,
        "original_24world_first_result_preserved":True,
        "independent_monte_carlo_world_count":24,
        "groups_per_world_sharing_fitted_model_and_calibrator":120,
        "total_validation_animal_scores_per_condition":2880,
        "nominal_one_sided_group_gain_bound_coverage":0.90,
        "confidence_interval_interpretation":(
            "approximate 95% Student-t Monte Carlo interval over 24 independent "
            "synthetic worlds, for mean validation coverage across retrained "
            "model/calibrator worlds; NOT 90% conformal gain bound, not "
            "conditional model coverage, not an empirical-BOP interval"
        ),
        "source_target_group_coverage":_world_summary(stable),
        "validation_only_shift_group_coverage":_world_summary(shifted),
        "paired_coverage_difference":_world_summary(paired),
        "naive_2880_iid_binomial_se_invalid_for_shared_worlds":{
            "source_target":naive_stable,
            "validation_only_shift":naive_shifted,
            "warning":"diagnostic comparison only: ignores shared model/calibrator across 120 groups",
        },
        "new_external_BOP_or_Dryad_measurements":False,
        "original_BOP_empirical_terminal":"empirical_state_prediction_mixed",
        "original_frozen_method_pass_reclassified":False,
        "new_confirmatory_hypothesis_test_performed":False,
    }


def main()->None:
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    ans=audit_world_uncertainty(
        json.loads(SOURCE.read_text(encoding="utf-8")),
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        ORIGINAL_CONTRACT.read_bytes(),
    )
    content=json.dumps(ans,indent=2,sort_keys=True,allow_nan=False)+"\n"
    if args.out:
        if args.out.resolve() in (SOURCE.resolve(),RECEIPT.resolve(),ORIGINAL_CONTRACT.resolve()):
            raise ValueError("post-result report cannot replace first-source evidence")
        args.out.write_text(content,encoding="utf-8")
    print(json.dumps({
        "source_target_coverage":ans["source_target_group_coverage"],
        "shifted_coverage":ans["validation_only_shift_group_coverage"],
        "paired_difference":ans["paired_coverage_difference"],
        "independent_worlds":ans["independent_monte_carlo_world_count"],
        "new_confirmatory_test":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
