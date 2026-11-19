#!/usr/bin/env python3
"""Verify first original Swiss 2024 STRICT PRIOR-YEAR ranger result offline.

Never downloads source RDS or opens labels, individual keys or predictions.
Pins first successful source ZIP SHA256 + all three member SHA256s and
recomputes the 16-seed paired model deltas from committed aggregates.
"""
from __future__ import annotations
import argparse
from io import BytesIO
import hashlib
import json
from pathlib import Path
import statistics
import zipfile

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_SWISS_RANGER_FOCAL_PRIOR_YEAR_V1_CONTRACT.json"
RECEIPT=ROOT/"BOP_SWISS_RANGER_FOCAL_PRIOR_YEAR_V1_FIRST_RECEIPT.json"
SOURCE_BLOB="fab942c0df8d6f77dc1db2bd2e2717681b9a3632"
FIRST_ZIP_SHA="23f6128024bc6476c56a90d2acef2a08f49e48de321257449197c3d2b703dbb6"
FIRST_MODEL_SHA="e73d5613b46d246cfbadd7a73dcb931052f9d908480f67bfde91ec51fc017812"
SEEDS=list(range(20261201,20261217))
MEANS={
  ("HR","disjoint_other_birds"):(.9425,.99119,.176148,.049911,.517839),
  ("HR","same_bird_other_year_exposure"):(.9425,.987786,.181905,.049604,.511061),
  ("nest","disjoint_other_birds"):(.9025,.982432,.170291,.056638,.496797),
  ("nest","same_bird_other_year_exposure"):(.90375,.981986,.170662,.056964,.489112)
}
PAIRED={
  "HR":(0,.005757,-.000307,-.006778,12),
  "nest":(.00125,.000371,.000326,-.007685,9)
}

def _blob_sha1(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def verify_first(receipt:dict,contract:dict,*,raw_zip:bytes|None=None)->dict:
    freeze=receipt["frozen_before_reread"]
    actions=receipt["first_actions"]
    chronology=receipt["chronology_gate"]
    model=receipt["model"]
    limits=receipt["claim_ceiling"]
    csource=contract["origin"]
    design=contract["sample_design"]
    if (
        receipt.get("receipt_id")!="bop-swiss-focal-prior-year-ranger-first-v1"
        or contract.get("contract_id")!="bop-swiss-ranger-focal-prior-year-later-test-v1"
        or freeze.get("contract_commit")!="4b3d8d486207f6488701bdc71f662f089b3f0b8f"
        or freeze.get("freeze_date")!="2026-11-19"
        or _blob_sha1(CONTRACT.read_bytes())!="e5248bcbbe6ae28c22e586be8fce4ff9ff17fd5e"
        or freeze.get("source_git_blob_sha1")!=SOURCE_BLOB
        or csource.get("source_RDS_git_blob_sha1")!=SOURCE_BLOB
        or freeze.get("source_size_bytes")!=53709803
        or freeze.get("prior_label_access_precedes_this_study") is not True
        or actions.get("run_id")!=44516904222
        or actions.get("source_job_id")!=135539346693
        or actions.get("source_head_sha")!="b8e9fcf5c3b524b1d811fbae29d0f90f3bd57d22"
        or actions.get("source_job_conclusion")!="success"
        or actions.get("python_safety_matrix")!=["3.10","3.12","3.13"]
        or actions.get("R_source_free_synthetic_success") is not True
        or actions.get("artifact_id")!=14527975243
        or actions.get("artifact_name")!="bop-swiss-focal-prior-year-first"
        or actions.get("original_artifact_ZIP_bytes")!=6126
        or actions.get("original_artifact_ZIP_sha256")!=FIRST_ZIP_SHA
    ):
        raise ValueError("first original source and pre-reread contract provenance drifted")
    expected_members={
        "bop-swiss-focal-prior-original-schema-first.json":(572,"f6d267261433655512cb131b7d935f78a51c4d0d1e29fa9d74b606bf67b310fc"),
        "bop-swiss-focal-prior-chronology-schema-first.json":(534,"ab71147ff04fc08ad1fa450743e87d65bf9b326488f9f5fe499a08b135913c35"),
        "bop-swiss-focal-prior-model-first.json":(57460,FIRST_MODEL_SHA)
    }
    actual_members={x.get("path"):(x.get("bytes"),x.get("sha256")) for x in actions.get("members",[])}
    if actual_members!=expected_members or len(actions.get("members",[]))!=3:
        raise ValueError("original source schema/model artifact member SHA or length changed")
    if (
        chronology.get("status")!="FOCAL_CHRONOLOGY_SCHEMA_51_TWO_SEASON_BIRDS_PASS"
        or chronology.get("source_year_range")!=[2016,2022]
        or chronology.get("n_year_id_strings")!=697
        or chronology.get("n_bird_id_strings")!=258
        or chronology.get("n_two_season_ids_with_distinct_years")!=51
        or chronology.get("outcome_values_inspected_before_gate") is not False
    ):
        raise ValueError("chronological source gate or response-access boundary changed")
    if (
        model.get("status")!="PAIRED_CHRONOLOGICAL_PRIOR_YEAR_RANGER_SOURCE_REFIT"
        or model.get("R_version")!="R version 4.4.3 (2025-02-28)"
        or model.get("ranger_version")!="0.18.0"
        or model.get("original_family_fixed_n_trees")!=500
        or model.get("mtry")!=5 or model.get("min_node_size")!=10
        or model.get("original_tuned_2024_ranger_not_reproduced") is not True
        or model.get("predeclared_seeds")!=SEEDS or design.get("seeds")!=SEEDS
        or model.get("outcomes")!=["HR","nest"]
        or model.get("n_models")!=64 or model.get("n_pairs")!=32
        or model.get("test_seasons_each_mode")!=50
        or model.get("train_seasons_each_mode")!=488
        or model.get("common_training_seasons")!=438
        or model.get("group_safe_bird_overlap")!=0
        or model.get("prior_focal_bird_exposed_overlap")!=50
        or model.get("test_rows_identical_within_seed") is not True
        or model.get("all_focal_exposed_train_years_strictly_earlier_than_test_years") is not True
        or model.get("only_focal_bird_chronology_not_entire_training_years") is not True
    ):
        raise ValueError("focal chronology source or model protocol changed")
    metrics=model.get("mean_metrics_by_target_and_mode")
    if len(metrics)!=4:
        raise ValueError("all four source model cells must be reported")
    seen=set()
    for x in metrics:
        key=(x.get("target"),x.get("mode"))
        values=(x.get("accuracy"),x.get("auc"),x.get("log_loss"),x.get("brier"),x.get("gain"))
        if key not in MEANS or key in seen or values!=MEANS[key]:
            raise ValueError("first actual source ranger mean scores changed")
        seen.add(key)
    if seen!=set(MEANS):
        raise ValueError("first source target/mode matrix incomplete")
    if model.get("paired_seed_delta_fields")!=["seed","test_log_loss","brier","accuracy","gain"]:
        raise ValueError("first source paired outcomes reordered")
    pairmap=model.get("paired_seed_deltas")
    if set(pairmap)!={"HR","nest"} or len(model.get("paired_effects_exposed_minus_safe",[]))!=2:
        raise ValueError("first source 32 paired comparisons not present")
    for target in ("HR","nest"):
        rows=pairmap[target]
        if len(rows)!=16 or any(len(x)!=5 for x in rows) or [x[0] for x in rows]!=SEEDS:
            raise ValueError("missing/duplicated/retuned original paired split seed")
        expected=PAIRED[target]
        result=(
          round(statistics.mean(x[3] for x in rows),6),
          round(statistics.mean(x[1] for x in rows),6),
          round(statistics.mean(x[2] for x in rows),6),
          round(statistics.mean(x[4] for x in rows),6),
          sum(x[1]>0 for x in rows)
        )
        if result!=expected:
            raise ValueError("first per-seed paired differences no longer reproduce original sign/mean")
        stored=next((x for x in model["paired_effects_exposed_minus_safe"] if x.get("target")==target),None)
        if stored is None or (
            stored["accuracy"],stored["log_loss"],stored["brier"],stored["gain"],
            stored["log_loss_worse_for_exposure_in_16_seeds"]
        )!=result:
            raise ValueError("paired target summary and actual original source seed deltas disagree")
        for keyname,attr in (("accuracy",0),("log_loss",2),("brier",3),("gain",4)):
            safe=MEANS[(target,"disjoint_other_birds")][attr]
            exposed=MEANS[(target,"same_bird_other_year_exposure")][attr]
            if round(exposed-safe,6)!=stored[keyname]:
                raise ValueError("original reported paired mean is inconsistent with first model cell means")
    if (
        limits.get("source_rds_and_outcome_columns_already_inspected_in_previous_PRS") is not True
        or limits.get("no_untouched_external_validation") is not True
        or limits.get("only_focal_test_bird_prior_year_chronology_not_global_forward_holdout") is not True
        or limits.get("per_bird_ID_not_canonical_cross_study_identity") is not True
        or limits.get("training_50_row_replacement_changes_label_and_feature_distribution") is not True
        or limits.get("no_pure_causal_identity_conclusion") is not True
        or limits.get("no_16_independent_ecological_studies_or_significance_test") is not True
        or limits.get("not_original_tuned_ranger_reproduction") is not True
        or limits.get("success_response_not_opened") is not True
        or limits.get("individual_IDs_and_per_row_predictions_not_exported") is not True
        or limits.get("original_BOP")!="empirical_state_prediction_mixed"
        or limits.get("redkite_new_group")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or limits.get("dryad")!="NOT_ADMITTED"
    ):
        raise ValueError("historical BOP, external red-kite or prior-year inference limits overclaimed")
    if raw_zip is not None:
        if len(raw_zip)!=6126 or hashlib.sha256(raw_zip).hexdigest()!=FIRST_ZIP_SHA:
            raise ValueError("input is not the original first successful Actions source artifact ZIP")
        with zipfile.ZipFile(BytesIO(raw_zip)) as z:
            if set(z.namelist())!=set(expected_members):
                raise ValueError("non-aggregate/source event file found in original artifact")
            parsed={}
            for name,(expected_bytes,expected_sha) in expected_members.items():
                content=z.read(name)
                if len(content)!=expected_bytes or hashlib.sha256(content).hexdigest()!=expected_sha:
                    raise ValueError("first artifact member source proof does not match hash")
                parsed[name]=json.loads(content)
            source=parsed["bop-swiss-focal-prior-chronology-schema-first.json"]
            if (
                source["status"]!=chronology["status"]
                or source["two_season_birds_with_strict_temporal_order"]!=51
                or source["verified_source_year_range"]!=chronology["source_year_range"]
                or source["outcome_values_inspected"] is not False
            ):
                raise ValueError("original outcome-blind chronology gate disagrees with receipt")
            full=parsed["bop-swiss-focal-prior-model-first.json"]
            if (
                full["status"]!=model["status"] or len(full["aggregate_score_panels"])!=64
                or len(full["aggregate_pairwise_differences"])!=32
                or full["precommitted_seeds"]!=SEEDS
                or full["focal_test_bird_prior_year_verified_in_training"] is not True
                or full["no_global_forward_validation_claim"] is not True
                or full["original_BOP_terminal"]!="empirical_state_prediction_mixed"
            ):
                raise ValueError("original source model row count/chronology/science boundary mismatch")
            for summary in metrics:
                matched=next((x for x in full["source_summary_by_target_and_mode"]
                   if x["target"]==summary["target"] and x["mode"]==summary["mode"]),None)
                if not matched:
                    raise ValueError("original model summary not in source")
                for key,sourcekey in (
                    ("accuracy","test_accuracy"),("auc","test_auc"),
                    ("log_loss","test_log_loss"),("brier","test_brier"),
                    ("gain","test_mean_log_score_gain_vs_train_prevalence")
                ):
                    if matched["all_metrics"][sourcekey]["mean"]!=summary[key]:
                        raise ValueError("original ZIP model mean scores disagree")
            for t in ("HR","nest"):
                q=next(x for x in full["paired_difference_summary_by_target"] if x["target"]==t)
                expected=next(x for x in model["paired_effects_exposed_minus_safe"] if x["target"]==t)
                for key,prefix in (("accuracy","accuracy"),
                    ("log_loss","test_log_loss"),("brier","brier"),("gain","log_score_gain")):
                    if q["paired_descriptive_differences"]["exposed_minus_disjoint_"+prefix]["mean"]!=expected[key]:
                        raise ValueError("original first ZIP paired expectation differs")
    return {
        "status":"FROZEN_FIRST_FOCAL_PRIOR_YEAR_RANGER_SOURCE_AND_PAIRS_VERIFIED",
        "original_first_run":44516904222,
        "test_50_birds_later_year_fixed":True,
        "prior_exposure_older_for_all_50_test_birds":True,
        "n_original_models":64,"n_paired_comparisons":32,
        "HR_exposed_minus_safe_log_loss":.005757,
        "nest_exposed_minus_safe_log_loss":.000371,
        "no_external_independent_generalization_certificate":True,
        "original_BOP":"empirical_state_prediction_mixed",
        "redkite_new_group":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-first-artifact-zip",type=Path)
    a=p.parse_args()
    raw=a.original_first_artifact_zip.read_bytes() if a.original_first_artifact_zip else None
    result=verify_first(
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        json.loads(CONTRACT.read_text(encoding="utf-8")),
        raw_zip=raw)
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
