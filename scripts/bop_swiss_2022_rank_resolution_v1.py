#!/usr/bin/env python3
"""Source-free exact finite-rank reference for Swiss 2022 28/4 class imbalance.

The original 96-model source result in merged #298 remains unchanged. This
computes a CONDITIONAL tie-free random-rank combinatorial reference, NOT
a p-value for the 8-seed mean AUC (same 32 test rows reused each seed).
Also compares recorded accuracy with an explicitly oracle/test-prevalence
majority-class benchmark (NOT deployable training-only baseline).
No original RDS, outcomes, source IDs, or model probabilities are accessed.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_SWISS_2022_RANK_RESOLUTION_V1_CONTRACT.json"
PRIOR=ROOT/"BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_FIRST_RECEIPT.json"

def git_blob_sha1(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def frozen()->tuple[dict,dict]:
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    r=json.loads(PRIOR.read_text(encoding="utf-8"))
    s=c["source"]; n=c["rank_reference"]; d=c["predeclared_screens"]; limits=c["scientific_limits"]
    if (
        c["contract_id"]!="bop-swiss-2022-auc-small-negative-exact-rank-reference-v1"
        or c["freeze_date"]!="2026-11-20"
        or r["receipt_id"]!="bop-swiss-temporal-bird-purge-original-first-v1"
        or git_blob_sha1(PRIOR.read_bytes())!=s["original_source_receipt_expected_git_blob_SHA1"]
        or r["first_actions"]["run_id"]!=s["original_first_run"]
        or r["first_actions"]["artifact_id"]!=s["original_first_artifact_id"]
        or s["original_GitHub_source_prepared_RDS_recontact_forbidden"] is not True
        or s["no_HR_nest_labels_or_individual_predictions_reopen"] is not True
        or (s["checked_2022_cutoff_purged_test_n"],s["checked_2022_cutoff_test_distinct_bird_ID_strings"],
            s["checked_2022_both_outcomes_positives"],s["checked_2022_both_outcomes_negatives"])!=(32,32,28,4)
        or (n["n_combinations"],n["pair_count"],n["AUC_U_denominator"])!=(35960,112,112)
        or n["choose_4_negative_score_rank_positions_from_32_without_replacement"] is not True
        or n["rank_comparisons_share_same_four_negatives_not_independent_pairs"] is not True
        or n["this_is_not_an_exact_p_value_for_8_seed_average_or_actual_tied_RF_scores"] is not True
        or n["no_significance_or_regime_shift_claim"] is not True
        or d["all_fixed_cutoffs"]!=[2020,2021,2022]
        or d["all_2022_modes_targets"]!=[["HR","full_forward"],["HR","bird_purged_forward"],
                                       ["nest","full_forward"],["nest","bird_purged_forward"]]
        or d["diagnostic_majority_baseline_uses_test_labels_not_deployable_estimator"] is not True
        or limits["original_BOP_terminal"]!="empirical_state_prediction_mixed"
        or limits["external_redkite_terminal"]!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or limits["original_Dryad"]!="NOT_ADMITTED"
    ):
        raise ValueError("historical source or frozen finite-rank sensitivity protocol drifted")
    prior=r["first_models"]
    if (
        prior["original_models_scored"]!=96 or prior["held_panels"]!=0
        or prior["primary_cutoff"]!=2021
        or (prior["source_2022_test_HR_positives"],prior["source_2022_test_HR_negatives"],
            prior["source_2022_test_nest_positives"],prior["source_2022_test_nest_negatives"])!=(28,4,28,4)
        or len(prior["all_twelve_cell_means"])!=12
        or r["scientific_ceiling"]["small_2022_sample_with_only_4_negatives_no_mechanism_established"] is not True
        or r["scientific_ceiling"]["source_HR_nest_outcomes_previously_accessed_not_untouched_validation"] is not True
    ):
        raise ValueError("2022 source test identities/support/score interpretations not preserved")
    return c,r

def random_rank_distribution(n_positive:int,n_negative:int)->Counter[int]:
    """All equally likely placements of negative labels among distinct scores.

    U = number of positive-score > negative-score comparisons.
    No per-row prediction scores or labels are used.
    """
    n=n_positive+n_negative
    if n_positive<=0 or n_negative<=0 or n>100:
        raise ValueError("invalid exact rank-reference panel")
    freq=Counter()
    for negative_rank_positions in itertools.combinations(range(n),n_negative):
        U=n_negative*(n-1)-sum(negative_rank_positions)-n_negative*(n_negative-1)//2
        if U<0 or U>n_positive*n_negative:
            raise ValueError("exact rank-pair count outside support")
        freq[U]+=1
    if sum(freq.values())!=math.comb(n,n_negative):
        raise ValueError("exact without-replacement permutation count changed")
    return freq

def rank_quantile(freq:Counter[int],q:float)->float:
    if not 0<q<1:
        raise ValueError("unsupported exact rank quantile")
    total=sum(freq.values())
    accum=0
    for u,num in sorted(freq.items()):
        accum+=num
        if accum/total>=q:
            return u/max(freq)
    raise ValueError("exact rank distribution has no tail")

def lower_reference(freq:Counter[int],threshold:float)->float:
    n=sum(freq.values())
    denominator=max(freq)
    if not 0<=threshold<=1:
        raise ValueError("AUC outside ranking domain")
    return sum(v for u,v in freq.items() if u/denominator<=threshold)/n

def run()->dict:
    c,r=frozen()
    p=r["first_models"]
    d=random_rank_distribution(28,4)
    n_total=sum(d.values())
    if n_total!=35960 or min(d)!=0 or max(d)!=112:
        raise ValueError("finite rank source n28/4 reference invalid")
    scores={}
    baseline=[]
    for row in p["all_twelve_cell_means"]:
        (cutoff,target,mode,accuracy,brier,logloss,gain,auc,
         auc_min,auc_max,test_prevalence,train_prevalence)=row
        if (cutoff,target,mode) in scores:
            raise ValueError("duplicate frozen model cell")
        if cutoff not in (2020,2021,2022) or target not in ("HR","nest") or mode not in ("full_forward","bird_purged_forward"):
            raise ValueError("original model panel not a predeclared fixed cutoff/target/mode")
        score=(cutoff,target,mode)
        scores[score]=row
        oracle_majority=max(test_prevalence,1-test_prevalence)
        baseline.append({
            "cutoff":cutoff,"target":target,"mode":mode,
            "original_test_prevalence":test_prevalence,
            "source_test_majority_class_accuracy_DIAGNOSTIC_ONLY":round(oracle_majority,6),
            "fixed_R_RF_accuracy_mean":accuracy,
            "fixed_R_RF_accuracy_minus_oracle_majority_benchmark":round(accuracy-oracle_majority,6),
            "training_prevalence_reference_log_gain_ORIGINAL":gain,
            "reference_uses_test_label_prevalence_not_prospective_estimator":True,
        })
    expected={(year,target,mode) for year in (2020,2021,2022)
              for target in ("HR","nest") for mode in ("full_forward","bird_purged_forward")}
    if set(scores)!=expected:
        raise ValueError("original frozen full twelve cutoff/target/mode panel incomplete")
    cases=[]
    for target,mode in c["predeclared_screens"]["all_2022_modes_targets"]:
        row=scores[(2022,target,mode)]
        auc_mean=row[7]
        cases.append({
            "cutoff":2022,"target":target,"mode":mode,
            "original_eight_forest_seeds_on_same_test_set":8,
            "original_2022_mean_AUC":auc_mean,
            "original_eight_seed_AUC_range":[row[8],row[9]],
            "tie_free_rank_combinations":n_total,
            "random_rank_lower_tail_at_observed_mean_AUC_REFERENCE_NOT_P_VALUE":round(lower_reference(d,auc_mean),9),
            "below_half_mean_AUC":auc_mean<.5,
            "no_inference_from_seed_repetition":True,
        })
    return {
        "schema_version":1,
        "status":"SWISS_2022_FOUR_NEGATIVES_SOURCE_FREE_RANK_REFERENCE_ONLY",
        "contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "original_source_first_run":r["first_actions"]["run_id"],
        "original_source_first_artifact_id":r["first_actions"]["artifact_id"],
        "original_model_results_unchanged":True,
        "test_2022_positive_rows":28,"test_2022_negative_rows":4,
        "number_of_positive_negative_rank_pairs_per_single_forest":112,
        "one_negative_moved_past_all_28_positives_can_change_AUC_by":.25,
        "exact_tie_free_random_rank_label_placements":n_total,
        "random_rank_auc_stddev":round(math.sqrt((32+1)/(12*28*4)),9),
        "random_rank_central_90_reference":[round(rank_quantile(d,.05),9),round(rank_quantile(d,.95),9)],
        "random_rank_central_95_reference":[round(rank_quantile(d,.025),9),round(rank_quantile(d,.975),9)],
        "four_original_2022_mean_AUC_random_rank_lower_reference":cases,
        "all_twelve_model_accuracies_vs_test_majority_oracle_DIAGNOSTIC_ONLY":baseline,
        "original_2022_seed_average_not_one_realized_ranking_and_may_have_score_ties":True,
        "posthoc_exploratory_reference_not_confirmatory_significance_test":True,
        "fixed_seeds_share_same_32_test_year_rows_not_eight_independent_trials":True,
        "no_new_source_or_outcome_or_probability_access":True,
        "no_actual_2022_causal_regime_shift_inferred":True,
        "historical_BOP_terminal":"empirical_state_prediction_mixed",
        "redkite_external_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "original_Dryad":"NOT_ADMITTED",
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.resolve() in (CONTRACT.resolve(),PRIOR.resolve()):
        raise ValueError("cannot overwrite immutable contract or original source")
    result=run()
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "exact_reference_label_placements":result["exact_tie_free_random_rank_label_placements"],
        "original_2022_four_cells":[
            {k:v for k,v in x.items() if k in ("target","mode","original_2022_mean_AUC",
                "random_rank_lower_tail_at_observed_mean_AUC_REFERENCE_NOT_P_VALUE")}
            for x in result["four_original_2022_mean_AUC_random_rank_lower_reference"]],
        "source_recontacted":False
    },sort_keys=True))

if __name__=="__main__":
    main()
