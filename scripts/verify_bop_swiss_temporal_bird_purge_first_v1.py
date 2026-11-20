#!/usr/bin/env python3
"""Offline verify first original 2024 Swiss global-forward bird purge result.

No RDS, individual identifiers, GPS, or outcome records are accessed.
The first official ZIP plus all three member hashes are fixed in the receipt;
when supplied, the original Actions artifact's 96 model results are cross-
verified against each of the frozen 12 source-wide mean panels.
"""
from __future__ import annotations
import argparse
from collections import Counter
from io import BytesIO
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_FIRST_RECEIPT.json"
CONTRACT=ROOT/"research/BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_CONTRACT.json"

SOURCE_BLOB="fab942c0df8d6f77dc1db2bd2e2717681b9a3632"
ZIP_SHA="04df9081e71d497c2e8c394e0fd79bfbb72524eb765dd019fdd4dc1f08be04ff"
MEMBERS={
"bop-swiss-forward-original-schema-first.json":(572,"f6d267261433655512cb131b7d935f78a51c4d0d1e29fa9d74b606bf67b310fc"),
"bop-swiss-forward-chronology-cohort-first.json":(2116,"3153b930d19738585c0d6b1f7eb2869e7e5d6ba856e28f0253321ff662911aa4"),
"bop-swiss-forward-bird-purge-ranger-first.json":(84103,"7f566d36f1d01596289c89b1c29b04b4d07ff9e8f1762c081808e7a3271b10db")
}
EXPECTED_ROWS={
2020:(405,98,292,220,64,194,156),
2021:(580,396,117,240,166,92,74),
2022:(665,555,32,258,226,32,32)
}
MEAN_KEYS=("accuracy_mean","brier_mean","logloss_mean",
    "gain_over_training_prevalence_mean","auc_mean","auc_min","auc_max",
    "test_positive_fraction","train_positive_fraction")
MEAN_EXPECT={
(2020,"HR","full_forward"):(.947346,.037978,.250886,.504099,.967915,.966099,.970820,.650685,.419753),
(2020,"HR","bird_purged_forward"):(.957620,.036055,.204032,.662324,.966780,.963442,.970150,.650685,.326531),
(2020,"nest","full_forward"):(.883990,.090544,.359115,.368822,.944024,.941265,.945886,.500000,.370370),
(2020,"nest","bird_purged_forward"):(.878853,.085944,.276368,.553932,.949099,.948020,.950647,.500000,.255102),
(2021,"HR","full_forward"):(.940171,.054092,.430515,.266383,.934495,.930861,.937461,.632479,.493103),
(2021,"HR","bird_purged_forward"):(.941239,.053654,.432852,.267306,.933179,.931647,.937461,.632479,.487374),
(2021,"nest","full_forward"):(.846154,.117124,.475423,.244245,.891192,.888173,.893443,.521368,.405172),
(2021,"nest","bird_purged_forward"):(.833333,.129345,.498379,.225660,.881147,.879098,.884660,.521368,.396465),
(2022,"HR","full_forward"):(.875000,.128858,1.278376,-.584100,.415736,.366071,.491071,.875000,.499248),
(2022,"HR","bird_purged_forward"):(.875000,.127684,1.391647,-.609657,.373884,.357143,.397321,.875000,.445045),
(2022,"nest","full_forward"):(.789062,.172999,.691297,.168385,.320312,.285714,.366071,.875000,.403008),
(2022,"nest","bird_purged_forward"):(.750000,.197332,.797262,.184597,.313616,.285714,.366071,.875000,.345946),
}

def _blob_sha(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def verify_first(r:dict,c:dict,raw_zip:bytes|None=None)->dict:
    a=r["first_actions"]; f=r["original_provenance"]; source=r["source_gate"]
    model=r["first_models"]; limits=r["scientific_ceiling"]
    if (
        r.get("receipt_id")!="bop-swiss-temporal-bird-purge-original-first-v1"
        or c.get("contract_id")!="bop-swiss-temporal-forward-bird-purged-ranger-v1"
        or f["pre_source_method_contract_commit"]!="8579e6d0260b1fc89f3047e6c6836a1542846cbe"
        or f["frozen_contract_git_blob"]!="e98664de442a7432f25b82d4004c108691fe6242"
        or _blob_sha(CONTRACT.read_bytes())!=f["frozen_contract_git_blob"]
        or f["original_2024_prepared_RDS_git_blob_sha1"]!=SOURCE_BLOB
        or f["original_source_bytes"]!=53709803
        or f["original_source_outcomes_previously_opened_in_PRS"]!=[295,296,297]
        or f["source_IDs_697_seasons_258_birds_and_years_2016_to_2022_verified"] is not True
        or a["run_id"]!=44746545177 or a["source_job_id"]!=136323453061
        or a["source_run_branch_head_sha"]!="c69df9e0e3f81c19b11c5955bd6bbf1684272e36"
        or a["source_job_conclusion"]!="success"
        or a["python_synthetic_3_10_3_12_3_13_success"] is not True
        or a["R_source_free_synthetic_success"] is not True
        or a["artifact_id"]!=14633317139
        or a["artifact_name"]!="bop-swiss-temporal-bird-purge-first"
        or a["original_zip_bytes"]!=8041 or a["original_zip_sha256"]!=ZIP_SHA
    ):
        raise ValueError("first source/run provenance or pre-access freeze was changed")
    first_members={x["path"]:(x["bytes"],x["sha256"]) for x in a["original_artifact_members"]}
    if first_members!=MEMBERS or len(a["original_artifact_members"])!=3:
        raise ValueError("first artifact three safe source member digests changed")
    if (
        source["original_697_seasons_258_bird_ID_strings_verified"] is not True
        or source["original_2016_to_2022_source_years_verified"] is not True
        or source["no_source_HR_nest_values_accessed_during_source_gate"] is not True
        or source["all_train_years_precede_all_test_years_for_all_cutoffs"] is not True
        or source["zero_bird_ID_overlap_purged_arm_all_cutoffs"] is not True
        or source["same_test_rows_in_both_train_arms_each_cutoff"] is not True
        or source["cutoffs_all_predeclared"]!=[2020,2021,2022]
        or source["primary_cutoff"]!=2021
    ):
        raise ValueError("original source temporal/biological group admission changed")
    counts=source["row_counts_by_cutoff"]
    if len(counts)!=3:
        raise ValueError("source cohort cutoff omitted")
    for x in counts:
        year=x["cutoff"]
        got=(x["full_train_rows"],x["purged_train_rows"],x["test_rows"],
             x["full_train_birds"],x["purged_train_birds"],x["test_birds"],
             x["full_train_test_overlap_birds"])
        if year not in EXPECTED_ROWS or got!=EXPECTED_ROWS[year] or x["purged_train_test_overlap_birds"]!=0:
            raise ValueError("first provider year/bird count or strict purge changed")
        if x["full_train_rows"]+x["test_rows"]!=697:
            raise ValueError("the whole source cohort was not partitioned")
    if set(x["cutoff"] for x in counts)!={2020,2021,2022}:
        raise ValueError("frozen source-year cutoff not exhaustive")
    if (
        model["status"]!="RETROSPECTIVE_SWISS_CALENDAR_FORWARD_BIRD_PURGED_SOURCE_REFIT"
        or model["original_R_version"]!="R version 4.4.3 (2025-02-28)"
        or model["original_ranger_version"]!="0.18.0"
        or model["model_is_fixed_ranger_500trees_mtry5_node10_not_2024_tuned"] is not True
        or model["predeclared_cutoffs"]!=[2020,2021,2022]
        or model["primary_cutoff"]!=2021
        or model["target_names"]!=["HR","nest"]
        or model["model_modes"]!=["full_forward","bird_purged_forward"]
        or model["frozen_model_seeds"]!=list(range(20261221,20261229))
        or model["original_models_scored"]!=96 or model["held_panels"]!=0
        or model["metric_columns"]!=["cutoff","target","mode",*MEAN_KEYS]
        or model["source_2022_test_HR_positives"]!=28 or model["source_2022_test_HR_negatives"]!=4
        or model["source_2022_test_nest_positives"]!=28 or model["source_2022_test_nest_negatives"]!=4
    ):
        raise ValueError("source model, 2022 rare class or original 96 panels rewritten")
    pairs=model["all_twelve_cell_means"]
    if len(pairs)!=12:
        raise ValueError("prespecified all 12 temporal model cells absent")
    seen=set()
    for row in pairs:
        if len(row)!=12:
            raise ValueError("first source model mean row shape changed")
        year,target,mode=row[:3]
        key=(year,target,mode)
        if key not in MEAN_EXPECT or key in seen or tuple(row[3:])!=MEAN_EXPECT[key]:
            raise ValueError("source mean, AUC range, prevalence or log score rewritten")
        seen.add(key)
    if seen!=set(MEAN_EXPECT):
        raise ValueError("not all 12 fixed model cells accounted for")
    required={
        "global_training_calendar_year_before_all_test_years":True,
        "bird_purged_train_test_bird_ID_overlap_zero_at_all_cutoffs":True,
        "identical_test_rows_purged_and_full_train_per_cutoff":True,
        "train_N_differs_between_two_modes_not_pure_causal_identity_effect":True,
        "cutoffs_2020_2021_2022_required_no_cherry_pick":True,
        "source_HR_nest_outcomes_previously_accessed_not_untouched_validation":True,
        "same_8_model_seeds_and_test_rows_not_8_independent_populations":True,
        "small_2022_sample_with_only_4_negatives_no_mechanism_established":True,
        "no_original_2024_tuned_ranger_reproduction":True,
        "no_independent_German_or_future_population_external_validation":True,
        "no_individual_projections_GPS_bird_IDs_or_success_outcomes_exported":True,
        "no_one_sided_unseen_group_rank_coverage_admitted":True,
        "original_BOP":"empirical_state_prediction_mixed",
        "redkite_external":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "Dryad":"NOT_ADMITTED"
    }
    if any(limits.get(k)!=v for k,v in required.items()):
        raise ValueError("first source model scoring promoted beyond within-Swiss retrospective inference")
    if raw_zip is not None:
        if len(raw_zip)!=8041 or hashlib.sha256(raw_zip).hexdigest()!=ZIP_SHA:
            raise ValueError("offered ZIP does not match original official source artifact")
        with zipfile.ZipFile(BytesIO(raw_zip)) as z:
            if set(z.namelist())!=set(MEMBERS):
                raise ValueError("unexpected raw source/animal-level artifact member included")
            got={}
            for path,(n,sha) in MEMBERS.items():
                data=z.read(path)
                if len(data)!=n or hashlib.sha256(data).hexdigest()!=sha:
                    raise ValueError("original source artifact byte hash/member mismatch")
                got[path]=json.loads(data)
            pre=got["bop-swiss-forward-chronology-cohort-first.json"]
            output=got["bop-swiss-forward-bird-purge-ranger-first.json"]
            if (
                pre["status"]!="ORIGINAL_PREPARED_SOURCE_GLOBAL_YEAR_BIRD_PURGE_SCHEMA_CHECKED"
                or pre["outcome_values_accessed"] is not False
                or pre["source_calendar_year_range"]!=[2016,2022]
                or output["status"]!=model["status"]
                or output["n_successful_models"]!=96
                or output["n_infeasible_cutoff_target_mode_panels"]!=0
                or output["all_predeclared_cutoffs"]!=[2020,2021,2022]
                or output["source_model_seed_indices_as_frozen"]!=model["frozen_model_seeds"]
                or output["no_external_country_or_untouched_future_validation_claim"] is not True
                or output["purged_arm_zero_bird_ID_overlap"] is not True
            ):
                raise ValueError("original model chronology/source proof not supported")
            panels=output["per_seed_aggregate_only_model_panels"]
            if len(panels)!=96:
                raise ValueError("first source outcome R ranger models omitted")
            observed=Counter((q["cutoff"],q["target"],q["mode"])
                for q in panels if q["status"]=="SCORED")
            if observed!={key:8 for key in MEAN_EXPECT}:
                raise ValueError("not all 8 exact predeclared model seeds scored per cutoff/response/mode")
            for s in output["all_cutoff_response_model_summaries"]:
                key=(s["cutoff"],s["target"],s["mode"])
                if key not in MEAN_EXPECT or s["status"]!="SCORED":
                    raise ValueError("unexpected source arm or HOLD silently omitted")
                x=s["metric_summary"]
                metric_values=(x["test_accuracy"]["mean"],x["test_brier"]["mean"],
                     x["test_log_loss"]["mean"],
                     x["test_mean_log_score_gain_vs_train_prevalence"]["mean"],
                     x["test_auc"]["mean"],x["test_auc"]["min"],x["test_auc"]["max"],
                     x["test_positive_fraction"]["mean"],x["train_positive_fraction"]["mean"])
                if metric_values!=MEAN_EXPECT[key]:
                    raise ValueError("first original 8-seed mean scores changed")
    return {
        "status":"FIRST_RETROSPECTIVE_GLOBAL_FORWARD_BIRD_PURGE_SOURCE_VERIFIED",
        "original_run_id":44746545177,
        "original_artifact_id":14633317139,
        "source_models_scored":96,
        "primary_year_cutoff":2021,
        "primary_HR_purged_AUC":.933179,
        "primary_nest_purged_AUC":.881147,
        "source_2022_test_negative_per_outcome":4,
        "original_BOP":"empirical_state_prediction_mixed",
        "redkite_external":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--first-artifact-zip",type=Path)
    a=p.parse_args()
    r=json.loads(RECEIPT.read_text(encoding="utf-8"))
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    raw=a.first_artifact_zip.read_bytes() if a.first_artifact_zip else None
    print(json.dumps(verify_first(r,c,raw),sort_keys=True))

if __name__=="__main__":
    main()
