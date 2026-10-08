#!/usr/bin/env python3
"""First frozen exact 2×2×6 ecological estimand witness, source-free."""
import hashlib
import json
from pathlib import Path

from odsp.uljin_threeway_margin_identifiability_v0 import (
    construct_marginal_identifiability_witness,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_THREEWAY_MARGIN_IDENTIFIABILITY_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_THREEWAY_MARGIN_IDENTIFIABILITY_V0_FIRST_RECEIPT.json"


def main()->int:
    frozen=CONTRACT.read_bytes()
    result=construct_marginal_identifiability_witness(json.loads(frozen))
    if (result["two_way_margin_operator_nullity"]!=5
        or result["independent_poisson_coarse_branch_phase_KL"]!=0
        or result["independent_poisson_full_threeway_KL_A_vs_B"]<=0):
        raise ValueError("exact identifiability counterexample gate failed")
    result["frozen_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "all_three_two_way_margins_identical":
            result["all_three_two_way_count_margins_exactly_equal"],
        "coarse_branch_phase_poisson_KL":
            result["independent_poisson_coarse_branch_phase_KL"],
        "full_site_resolved_poisson_KL_A_vs_B":
            result["independent_poisson_full_threeway_KL_A_vs_B"],
        "nullity":result["two_way_margin_operator_nullity"],
        "overlapping_margins_joint_law_equal":
            result["joint_distribution_of_all_overlapping_two_way_margins_equal"],
        "original_source_rows_accessed":False,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
