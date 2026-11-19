#!/usr/bin/env python3
"""Verify original same-test Swiss 2024 ranger data/design result offline.

No original RDS, GPS, animal IDs, HR/nest raw labels or model is accessed.
The first official ZIP/JSON hashes are immutable; the committed receipt
stores compact per-seed aggregate paired differences and means.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_SWISS_RANGER_PAIRED_OTHER_YEAR_EXPOSURE_V1_CONTRACT.json"
RECEIPT=ROOT/"BOP_SWISS_RANGER_PAIRED_OTHER_YEAR_EXPOSURE_V1_FIRST_RECEIPT.json"
FIELDS=("seed","log_loss_diff","brier_diff","accuracy_diff","log_score_gain_diff")
SCORES={
    ("HR","disjoint_other_birds"):(.970000,.121264,.028638,.988142,.588366),
    ("HR","same_bird_other_year_exposure"):(.970000,.143140,.029346,.982926,.560545),
    ("nest","disjoint_other_birds"):(.947500,.100935,.031082,.994950,.553231),
    ("nest","same_bird_other_year_exposure"):(.947500,.100025,.031009,.994688,.547666),
}
PAIRED={
    "HR":(.021876,.000709,0,-.027821,14),
    "nest":(-.000909,-.000073,0,-.005565,7),
}

def _git_blob_sha256_sha1(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def verify_first(receipt:dict,contract:dict,*,raw_zip:bytes|None=None)->dict:
    freeze=receipt["original_freeze"]
    first=receipt["first_actions"]
    schema=receipt["original_source_schema"]
    model=receipt["first_model"]
    lim=receipt["scientific_limits"]
    source=contract["immutable_source"]
    design=contract["paired_fixed_design"]
    fit=contract["fixed_R_ranger_model"]
    if (
        receipt.get("receipt_id")!="bop-swiss-ranger-paired-same-test-first-official-v1"
        or receipt.get("evidence_role")!="PROSPECTIVELY_FROZEN_SAME_TEST_WITHIN_SWISS_PREPARED_RDS_RANGER_SOURCE_RESULT"
        or contract.get("contract_id")!="bop-swiss-ranger-same-test-bird-other-year-exposure-v1"
        or freeze.get("pre_source_contract_commit")!="0ff935d43624ad6f0efbcfd344a695f0e4f80279"
        or freeze.get("frozen_date")!="2026-11-19"
        or _git_blob_sha256_sha1(CONTRACT.read_bytes())!="daefd6e394a0d38a24045b406e4313802f5d4fbc"
        or freeze.get("historical_source_repo_commit")!="Vogelwarte/NestTool@8fdf3884b5f6079afdffdc5c563c9050766670a4"
        or freeze.get("original_prepared_RDS_git_blob_sha1")!="fab942c0df8d6f77dc1db2bd2e2717681b9a3632"
        or source.get("git_blob_sha1")!=freeze.get("original_prepared_RDS_git_blob_sha1")
        or freeze.get("original_prepared_RDS_bytes")!=53709803
        or first.get("workflow_run_id")!=44476326291
        or first.get("source_job_id")!=135398733458
        or first.get("first_source_branch_head")!="390900023570db800b375b67d86c00c24d7ba13b"
        or first.get("source_job_status")!="success"
        or first.get("python_known_truth_3_10_3_12_3_13_all_success") is not True
        or first.get("R_synthetic_source_free_gate_success") is not True
        or first.get("original_artifact_id")!=14506357960
        or first.get("original_zip_bytes")!=5644
        or first.get("original_zip_sha256")!="5baf70031cabeb1d97dbf563e658a721f0fb6b6a4090482c48f5590993c02731"
        or first.get("schema_member")!="bop-ranger-paired-schema-first.json"
        or first.get("schema_bytes")!=572
        or first.get("schema_sha256")!="f6d267261433655512cb131b7d935f78a51c4d0d1e29fa9d74b606bf67b310fc"
        or first.get("model_member")!="bop-ranger-paired-model-first.json"
        or first.get("model_bytes")!=57153
        or first.get("model_sha256")!="4e705cb469e53812cd53b375636f43e3696f17cbbf977c7f8c068b31d17dfcff"
    ):
        raise ValueError("original source or Actions first artifact identity changed")
    if (
        schema.get("status")!="PREPARED_SOURCE_SCHEMA_AND_697_258_HISTOGRAM_PASS"
        or schema.get("seasons")!=697
        or schema.get("bird_ID_strings")!=258
        or schema.get("exactly_two_season_bird_pool")!=51
        or schema.get("source_histogram_1_to_7")!=[66,51,62,56,20,2,1]
        or schema.get("original_34_predictors_present") is not True
        or schema.get("first_gate_outcome_values_inspected") is not False
        or schema.get("RDS_and_exact_source_hash_verified") is not True
    ):
        raise ValueError("source schema prior to outcome use altered")
    if (
        model.get("status")!="PAIRED_SAME_TEST_2024_RANGER_SOURCE_REFIT"
        or model.get("family")!="R_ranger_fixed_500_trees_mtry_5_node_10_not_original_tuned_RF"
        or model.get("ranger_version")!="0.18.0"
        or model.get("R_version")!="R version 4.4.3 (2025-02-28)"
        or model.get("seeds")!=list(range(20261119,20261135))
        or model.get("seeds")!=design.get("seeds")
        or model.get("responses")!=["HR","nest"]
        or model.get("source_seasons")!=697
        or model.get("source_bird_ID_strings")!=258
        or model.get("test_rows_per_seed_mode")!=50
        or model.get("training_rows_per_seed_mode")!=488
        or model.get("identical_test_rows_within_seed_for_both_modes") is not True
        or model.get("common_training_rows_between_modes")!=438
        or model.get("disjoint_mode_test_bird_ID_overlap")!=0
        or model.get("exposed_mode_test_bird_ID_overlap")!=50
        or model.get("number_of_original_fixed_model_panels")!=64
        or model.get("number_of_paired_seed_target_comparisons")!=32
        or fit.get("n_trees")!=500 or fit.get("mtry")!=5 or fit.get("minimum_terminal_node_size")!=10
    ):
        raise ValueError("same-test 2024 ranger design/seed source or panel counts drifted")
    summaries=model.get("mean_metrics_by_target_and_mode")
    if not isinstance(summaries,list) or len(summaries)!=4:
        raise ValueError("all four original model panels are required")
    seen=set()
    for q in summaries:
        key=(q.get("target"),q.get("mode"))
        vals=(q.get("test_accuracy"),q.get("test_log_loss"),
              q.get("test_brier"),q.get("test_auc"),
              q.get("test_mean_log_score_gain_vs_train_prevalence"))
        if key not in SCORES or key in seen or vals!=SCORES[key]:
            raise ValueError("immutable first model performance value changed")
        seen.add(key)
    if seen!=set(SCORES):
        raise ValueError("not all two-outcome paired models are included")

    pairs=model.get("per_seed_paired_delta_by_target")
    assert isinstance(pairs,dict)
    if set(pairs)!={"HR","nest"} or model.get("per_seed_paired_delta_fields")!=list(FIELDS):
        raise ValueError("first paired seed rows or order omitted")
    fixed_deltas=model.get("paired_mean_differences_exposed_minus_disjoint")
    if len(fixed_deltas)!=2:
        raise ValueError("original two paired target results missing")
    for target in ("HR","nest"):
        rows=pairs[target]
        if len(rows)!=16 or [r[0] for r in rows]!=model["seeds"] or any(len(r)!=5 for r in rows):
            raise ValueError("frozen original paired seed count/order or column count invalid")
        if any(r[3]!=0 or not isinstance(r[0],int) for r in rows):
            raise ValueError("observed same-test accuracy difference or seed index changed")
        computed=(round(statistics.mean(r[1] for r in rows),6),
                  round(statistics.mean(r[2] for r in rows),6),
                  round(statistics.mean(r[3] for r in rows),6),
                  round(statistics.mean(r[4] for r in rows),6),
                  sum(r[1]>0 for r in rows))
        if computed!=PAIRED[target]:
            raise ValueError("per-seed paired result no longer reproduces original scientific finding")
        q=next(x for x in fixed_deltas if x["target"]==target)
        if (q["log_loss"],q["brier"],q["accuracy"],
            q["log_score_gain"],q["log_loss_higher_in_number_of_16_seeds"])!=computed:
            raise ValueError("paired summary inconsistent with frozen seed-level deltas")
    for k,v in {
        "same_test_50_seasons_used_for_both_training_modes_per_seed":True,
        "only_exactly_two_season_bird_ID_pool_selected":True,
        "the_other_year_could_be_future_not_prior_year":True,
        "training_replacement_changes_both_feature_and_label_distribution":True,
        "this_is_not_a_pure_causal_effect_of_individual_identity":True,
        "all_16_seeds_from_one_reused_Swiss_study_not_independent_validation_sets":True,
        "original_NestTool_tuned_RF_and_2024_random_split_not_reproduced":True,
        "no_actual_future_out_of_population_external_model_gain":True,
        "no_raw_animal_identifiers_or_GPS_coordinates_or_per_record_predictions_emitted":True,
        "breeder_success_response_not_read":True,
        "original_ODSP_BOP_terminal":"empirical_state_prediction_mixed",
        "redkite_external_new_group_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "original_Dryad":"NOT_ADMITTED",
    }.items():
        if lim.get(k)!=v:
            raise ValueError("experimental same-test study falsely promoted to causal/external result")
    if raw_zip is not None:
        if len(raw_zip)!=first["original_zip_bytes"] or hashlib.sha256(raw_zip).hexdigest()!=first["original_zip_sha256"]:
            raise ValueError("offered original Actions artifact ZIP is not identical to first result")
        from io import BytesIO
        with zipfile.ZipFile(BytesIO(raw_zip)) as z:
            if set(z.namelist())!={first["schema_member"],first["model_member"]}:
                raise ValueError("unexpected individual/GPS artifacts found in source ZIP")
            for key,expected_len,expected_sha in (
                (first["schema_member"],first["schema_bytes"],first["schema_sha256"]),
                (first["model_member"],first["model_bytes"],first["model_sha256"]),
            ):
                body=z.read(key)
                if len(body)!=expected_len or hashlib.sha256(body).hexdigest()!=expected_sha:
                    raise ValueError("original artifact member bytes do not match immutable first source result")
            full=json.loads(z.read(first["model_member"]))
            if full["status"]!=model["status"] or len(full["aggregate_score_panels"])!=64 or len(full["aggregate_pairwise_differences"])!=32:
                raise ValueError("archived original 64-model output is not the registered source")
            for mode in summaries:
                matched=next((x for x in full["source_summary_by_target_and_mode"]
                    if x["target"]==mode["target"] and x["mode"]==mode["mode"]),None)
                if matched is None:
                    raise ValueError("missing source model summary")
                for src,rc in (
                    ("test_accuracy","test_accuracy"),
                    ("test_log_loss","test_log_loss"),
                    ("test_brier","test_brier"),
                    ("test_auc","test_auc"),
                    ("test_mean_log_score_gain_vs_train_prevalence",
                     "test_mean_log_score_gain_vs_train_prevalence")
                ):
                    if matched["all_metrics"][src]["mean"]!=mode[rc]:
                        raise ValueError("first GitHub Actions numerical means differ from receipt")
    return {
        "status":"FIRST_PAIRED_RANGER_SOURCE_AND_AGGREGATES_VERIFIED",
        "run_id":first["workflow_run_id"],
        "first_artifact_id":first["original_artifact_id"],
        "heldout_50_birds_on_identical_test_rows":True,
        "disjoint_bird_overlap":0,
        "exposed_other_year_bird_overlap":50,
        "paired_fits":64,
        "HR_exposed_minus_disjoint_log_loss":.021876,
        "nest_exposed_minus_disjoint_log_loss":-.000909,
        "no_season_or_bird_ID_values_read":True,
        "no_external_new_group_generalization_certified":True,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--first-artifact-zip",type=Path)
    a=p.parse_args()
    raw=a.first_artifact_zip.read_bytes() if a.first_artifact_zip else None
    output=verify_first(
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        json.loads(CONTRACT.read_text(encoding="utf-8")),
        raw_zip=raw
    )
    print(json.dumps(output,sort_keys=True))

if __name__=="__main__":
    main()
