#!/usr/bin/env python3
"""Publication-aggregate red-kite prevalence audit; reads no biological CSV."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/BOP_RED_KITE_PUBLISHED_BASELINE_AUDIT_V1.json"

def calculate(contract: dict) -> dict:
    if (contract.get("audit_id") != "bop-red-kite-published-aggregate-baseline-v1"
            or contract.get("status") != "POSTPUBLICATION_DESCRIPTIVE_ARITHMETIC_ONLY"):
        raise ValueError("unrecognized publication-only audit or status")
    src = contract["source"]
    if src["paper_doi"] != "10.1111/jav.03246" or src["zenodo_doi"] != "10.5281/zenodo.13736049":
        raise ValueError("source identity drift")
    n = contract["reported_german"]
    acc = contract["published_accuracy_pct"]
    expected_counts = {
        "eligible_individual_seasons":99, "eligible_birds":63, "distinct_populations":2,
        "home_range_yes_seasons":98, "nest_attempt_yes_seasons":89,
        "nest_success_yes_among_attempts":55,
    }
    if n != expected_counts or acc != {"home_range":96.0,"nest_attempt":84.8,"nest_success":84.7}:
        raise ValueError("published counts/accuracies changed; new audit required")
    if not (0 <= n["nest_success_yes_among_attempts"] <= n["nest_attempt_yes_seasons"]
            <= n["home_range_yes_seasons"] <= n["eligible_individual_seasons"]):
        raise ValueError("impossible nested reproductive counts")
    limits = contract["interpretation"]
    if (limits["original_bop_legacy_terminal"] != "empirical_state_prediction_mixed"
            or limits["red_kite_schema_terminal"] != "HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
            or limits["new_data_access"] != "NONE"):
        raise ValueError("historical empirical boundaries or source access reclassified")
    contexts = {
        "home_range": (n["home_range_yes_seasons"],n["eligible_individual_seasons"]),
        "nest_attempt": (n["nest_attempt_yes_seasons"],n["eligible_individual_seasons"]),
        "nest_success": (n["nest_success_yes_among_attempts"],n["nest_attempt_yes_seasons"]),
    }
    rows = []
    for state,(yes,total) in contexts.items():
        retrospective = 100*max(yes,total-yes)/total
        rows.append({
            "state":state, "published_positives":yes, "published_context_seasons":total,
            "published_model_accuracy_pct":acc[state],
            "posthoc_majority_class_accuracy_pct":round(retrospective,5),
            "illustrative_accuracy_gap_percentage_points":round(acc[state]-retrospective,5),
            "valid_independent_prediction_comparison":False,
            "requires_same_score_roster_and_train_only_reference":True,
            "success_denominator_not_reconciled":state=="nest_success",
        })
    return {
        "status":"PUBLISHED_AGGREGATE_DIAGNOSTIC_ONLY",
        "source":src["paper_doi"],
        "biological_individuals_published":n["eligible_birds"],
        "individual_seasons_published":n["eligible_individual_seasons"],
        "replication_units_verified_from_source":False,
        "new_prediction_evaluated":False,
        "rank_lower_bound_calibrated":False,
        "original_bop_terminal":"empirical_state_prediction_mixed",
        "red_kite_biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "benchmarks":rows,
    }

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=calculate(json.loads(SOURCE.read_text(encoding="utf-8")))
    if a.out.resolve()==SOURCE.resolve():
        raise ValueError("cannot overwrite published input")
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"new_prediction_evaluated":False,
                      "benchmarks":result["benchmarks"]},sort_keys=True))

if __name__=="__main__":
    main()
