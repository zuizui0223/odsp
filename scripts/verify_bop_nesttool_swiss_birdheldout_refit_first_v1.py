#!/usr/bin/env python3
"""Offline original 2024 Swiss RF year-vs-bird comparison first-receipt verifier.

Reads only committed aggregate model metrics and frozen original source
fingerprints. It NEVER fetches or parses the original public RDS/labels.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts.bop_nesttool_swiss_birdheldout_refit_v1 import SEEDS,TARGETS

RECEIPT=ROOT/"BOP_NESTTOOL_SWISS_BIRD_HELDOUT_REFIT_V1_FIRST_RECEIPT.json"
CONTRACT=ROOT/"research/BOP_NESTTOOL_SWISS_BIRD_HELDOUT_REFIT_V1_CONTRACT.json"

METRICS=(
    "train_n","test_n","train_unique_bird_ids","test_unique_bird_ids",
    "overlapping_bird_ids","test_positive_fraction","test_accuracy",
    "test_balanced_accuracy","test_roc_auc","test_log_loss","test_brier",
    "test_mean_log_score_gain_vs_training_prevalence"
)
EXPECTED={
    ("HR","year_id"):(.968301,.029506,.546518,120.375),
    ("HR","bird_id"):(.962320,.030738,.573996,0),
    ("nest","year_id"):(.947368,.046422,.523484,120.375),
    ("nest","bird_id"):(.940192,.048585,.516542,0),
}
def verify_first(receipt:dict,contract:dict,*,raw:bytes|None=None)->dict:
    actions=receipt["actions"]
    schema=receipt["first_schema_result"]
    actual=receipt["frozen_first_source_and_model_result"]
    limits=receipt["scientific_limit"]
    model_json_sha="94f33235c21bdfcb0fb65dcb12a9d8ddc1f3bccc38ae4f172a6a2e05f4fe8ff2"
    if (
        receipt.get("receipt_id")!="bop-nesttool-Swiss-prepared-2024-year-vs-bird-holdout-first-v1"
        or receipt.get("pre_outcome_contract_first_commit")!="ed22ef9722f3440db5f44c0201204b4849ec06a2"
        or receipt.get("pre_outcome_contract_corrected_code_citation_commit")!="e2fd57ea054eef2ab4280baeb2c5c54f4517d1c9"
        or contract.get("contract_id")!="bop-nesttool-swiss-prepared-source-bird-heldout-refit-v1"
        or actions.get("run_id")!=44462371738
        or actions.get("first_head_sha")!="903c17931c6da54f108652bd0b8bfbd5e09ee625"
        or actions.get("python_safety_success_3_10_3_12_3_13") is not True
        or actions.get("source_schema_job_id")!=135352277285
        or actions.get("source_schema_job_status")!="success"
        or actions.get("model_job_id")!=135352626472
        or actions.get("model_job_status")!="success"
        or actions.get("first_schema_artifact_id")!=14499344988
        or actions.get("first_schema_artifact_zip_sha256")!="3cdca6d81a94d5a21268e1419b12fb9e6568c99136e35ae0e4123ddaa7dbd9f0"
        or actions.get("first_schema_json_bytes")!=572
        or actions.get("first_schema_json_sha256")!="f6d267261433655512cb131b7d935f78a51c4d0d1e29fa9d74b606bf67b310fc"
        or actions.get("first_model_artifact_id")!=14500588048
        or actions.get("first_model_artifact_zip_sha256")!="e89369281ff48136b8f367e1b65601fa03f3f42cc6cee6c3a489e972d6d10083"
        or actions.get("first_model_json_bytes")!=25955
        or actions.get("first_model_json_sha256")!=model_json_sha
        or actions.get("frozen_contract_sha256")!="f14ed4ee792681ec5bcd7a4fe65c627680af6910fd8d10fa63da73f28ff98c28"
        or actions.get("frozen_contract_sha256")!=hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    ):
        raise ValueError("original first 2024 RDS schema/refit source/provenance drifted")
    if (
        schema.get("status")!="PREPARED_SOURCE_SCHEMA_AND_697_258_HISTOGRAM_PASS"
        or schema.get("summary_seasons")!=697
        or schema.get("distinct_year_ID_strings")!=697
        or schema.get("distinct_bird_ID_strings")!=258
        or schema.get("source_file_bytes")!=53709803
        or schema.get("source_git_blob_sha1")!="fab942c0df8d6f77dc1db2bd2e2717681b9a3632"
        or schema.get("histogram_1_to_7")!=[66,51,62,56,20,2,1]
        or schema.get("predictor_names_present_count")!=34
        or schema.get("outcome_label_values_inspected") is not False
        or schema.get("model_fit_run") is not False
        or schema.get("original_2024_training_roster_certified") is not False
    ):
        raise ValueError("source-only schema and outcome access gate altered")
    encoded=(json.dumps(actual,sort_keys=True,indent=2,allow_nan=False)+"\n").encode("utf-8")
    if len(encoded)!=25955 or hashlib.sha256(encoded).hexdigest()!=model_json_sha:
        raise ValueError("source model metrics do not byte-reproduce first official fixed-analysis JSON")
    if raw is not None and (len(raw)!=25955 or hashlib.sha256(raw).hexdigest()!=model_json_sha):
        raise ValueError("offered rerun differs from original predeclared model result")
    if (
        actual.get("status")!="SWISS_SAME_SOURCE_BIRD_DISJOINT_RF_REFIT_COMPARISON"
        or actual.get("frozen_contract_sha256")!=actions["frozen_contract_sha256"]
        or actual.get("source_prepublication_RDS_Git_blob_SHA1_verified_by_CI") is not True
        or actual.get("verified_RDS_schema_697_seasons_258_bird_ID_strings") is not True
        or actual.get("outcomes_used")!=["HR","nest"]
        or actual.get("success_outcome_not_read") is not True
        or actual.get("model")!="scikit_learn_500_tree_RF_5_mtry_refit_NOT_exact_2024_ranger"
        or actual.get("eight_precommitted_seeds")!=list(SEEDS)
        or actual.get("source_histogram")!={"1":66,"2":51,"3":62,"4":56,"5":20,"6":2,"7":1}
        or actual.get("no_event_data_or_real_bird_or_year_IDs_exported") is not True
        or actual.get("not_original_2024_random_split_or_model") is not True
        or actual.get("no_formal_claim_about_original_accuracy_inflation_or_future_group_coverage") is not True
        or actual.get("BOP_original_terminal")!="empirical_state_prediction_mixed"
        or actual.get("redkite_external_terminal")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    ):
        raise ValueError("prepared source model result overstates original 2024 study or score interpretation")
    panels=actual["model_metrics_per_seed_aggregate_only"]
    if len(panels)!=32:
        raise ValueError("a seed, target or split mode was omitted")
    keys=Counter((p["target"],p["seed"],p["split_mode"]) for p in panels)
    if keys!=Counter({(tar,s,mode):1 for tar in TARGETS for s in SEEDS for mode in ("year_id","bird_id")}):
        raise ValueError("source model panel run not complete or duplicate")
    for p in panels:
        if (
            set(p)!={"target","seed","split_mode",*METRICS}
            or p["train_n"]!=488
            or p["test_n"]!=209
            or not 0<=p["test_accuracy"]<=1
            or not 0<=p["test_brier"]<=1
            or not 0<=p["test_positive_fraction"]<=1
            or not 0<=p["test_log_loss"]
            or p["split_mode"]=="bird_id" and p["overlapping_bird_ids"]!=0
            or p["split_mode"]=="year_id" and not 0<=p["overlapping_bird_ids"]<=258
        ):
            raise ValueError("year-level or animal-level groups, target metrics, or sample size drifted")
    report=actual["mode_by_target_summary"]
    if len(report)!=4:
        raise ValueError("no frozen year/bird metric comparison")
    for s in report:
        key=(s["target"],s["split_mode"])
        if key not in EXPECTED or s["frozen_eight_seeds_reported"]!=8:
            raise ValueError("nonfrozen target or split mode in summary")
        subset=[p for p in panels if (p["target"],p["split_mode"])==key]
        for metric in METRICS:
            v=[p[metric] for p in subset if p[metric] is not None]
            reference=s["summary"][metric]
            if not v:
                if reference is not None:
                    raise ValueError("missing-class metric summary invalid")
                continue
            target={"mean":round(statistics.mean(v),6),
                "median":round(statistics.median(v),6),
                "min":round(min(v),6),"max":round(max(v),6)}
            if reference!=target:
                raise ValueError("first official model aggregate cannot be recomputed from 8 fixed splits")
        expected=EXPECTED[key]
        actual_mean=(
            s["summary"]["test_accuracy"]["mean"],
            s["summary"]["test_brier"]["mean"],
            s["summary"]["test_mean_log_score_gain_vs_training_prevalence"]["mean"],
            s["summary"]["overlapping_bird_ids"]["mean"]
        )
        if actual_mean!=expected:
            raise ValueError("first performance comparison reclassified or rounded differently")
    if not all(limits.get(k) is True for k in (
        "source_is_prepublication_2024_prepared_GitHub_RDS_not_2024_Zenodo_CSV",
        "experimental_RF_is_sklearn_not_original_tuned_ranger",
        "source_individual_ID_strings_not_canonical_identity_crosswalk",
        "original_2024_RF_training_test_random_assignment_not_recovered",
        "repeated_eight_splits_not_independent_studies",
        "no_formal_adjustment_to_original_paper_accuracy",
        "no_new_Swiss_German_transfer_validation",
        "test_source_matched_488_train_209_test_year_ID_rows_for_both_modes",
        "group_split_zero_bird_ID_overlap_in_all_eight_seeds"
    )) or limits.get("original_BOP_status")!="empirical_state_prediction_mixed" or limits.get("redkite_real_external_gain_status")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER":
        raise ValueError("inference ceiling or matching-size design reclassified")
    return {
        "first_real_prepared_source_verified":True,
        "result_status":"MATCHED_TEST_SIZE_SEASON_VS_BIRD_RF_DESIGN_SENSITIVITY",
        "predeclared_eight_seed_panels":32,
        "year_split_mean_overlapping_birds":120.375,
        "bird_split_mean_overlapping_birds":0,
        "HR_year_vs_bird_test_accuracy":[.968301,.962320],
        "nest_year_vs_bird_test_accuracy":[.947368,.940192],
        "HR_year_vs_bird_brier":[.029506,.030738],
        "nest_year_vs_bird_brier":[.046422,.048585],
        "not_replication_of_original_2024_random_seed_or_original_ranger":True,
        "original_BOP":"empirical_state_prediction_mixed",
        "redkite_future_animal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    }

def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result",type=Path)
    args=p.parse_args()
    raw=args.result.read_bytes() if args.result else None
    output=verify_first(
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        json.loads(CONTRACT.read_text(encoding="utf-8")),
        raw=raw
    )
    print(json.dumps(output,sort_keys=True))

if __name__=="__main__":
    main()
