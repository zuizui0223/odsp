#!/usr/bin/env python3
"""First frozen 48x800 independent q/w reference variance budget decomposition."""
from pathlib import Path
import hashlib
import json
from odsp.uljin_q_w_variance_budget_v0 import run_full_decomposition

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_Q_W_VARIANCE_BUDGET_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_Q_W_EQUAL_BUDGET_V0_FIRST_RESULT_LEDGER.json"
OUT=ROOT/"ULJIN_Q_W_VARIANCE_BUDGET_V0_FIRST_RECEIPT.json"


def main()->int:
    frozen=PLAN.read_bytes()
    output=run_full_decomposition(json.loads(frozen),
                                  json.loads(PARENT.read_bytes()))
    if (output["number_of_scenarios"]!=48 or
        output["total_independent_worlds"]!=38400):
        raise ValueError("the 48×800 independent q/w variance world freeze failed")
    output["pre_outcome_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(output,sort_keys=True,indent=2,allow_nan=False)+"\n")
    summary=[]
    for name,opt in output["continuous_local_variance_optimum_by_truth"].items():
        rows=[r for r in output["all_original_equal_budget_scenarios"]
              if r["truth"]==name and r["budget"]==12000]
        summary.append({
            "world":name,
            "continuous_nq_over_nw":opt["continuous_optimal_nq_over_nw"],
            "reference_budget_fraction_to_q":
                opt["fraction_total_reference_opportunities_to_q"],
            "original_three_strategies_at_budget_12000":[{
                "strategy":r["strategy"],
                "first_order_q_variance_share":r["first_order_fraction_variance_due_to_q"],
                "first_order_total_log_detector_OR_variance":
                    r["first_order_total_log_detector_OR_variance"],
                "empirical_sample_variance":r["sample_variance_full_or_null"],
                "empirical_relative_error":
                    r["empirical_over_first_order_relative_error_or_null"]
            } for r in rows],
        })
    print(json.dumps({
        "status":output["status"],
        "all_scenarios":output["number_of_scenarios"],
        "calibration_draws":output["total_independent_worlds"],
        "optima_and_one_budget_comparisons":summary,
        "no_true_ecological_event_records_read":True,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
