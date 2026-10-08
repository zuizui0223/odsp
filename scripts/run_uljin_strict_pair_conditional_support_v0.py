#!/usr/bin/env python3
"""Frozen idealized analytical feasibility receipt; no actual source reads."""
import hashlib
import json
from pathlib import Path
from odsp.uljin_strict_pair_conditional_support_v0 import (
    run_strict_pair_support_screen,
)
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_STRICT_PAIR_CONDITIONAL_SUPPORT_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_STRICT_PAIR_CONDITIONAL_SUPPORT_V0_FIRST_RECEIPT.json"


def main()->int:
    frozen=PLAN.read_bytes()
    result=run_strict_pair_support_screen(json.loads(frozen))
    result["frozen_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "hypothetical_all_year_fraction_one": [{
            "taxon":row["taxon"],
            "expected_both_branch_site_pair_groups":
                row["expected_both_branch_site_pair_groups"],
        } for row in result["cases"]
          if row["assumed_fraction_of_events_retained"]==1.],
        "does_not_bound_pooled_conditional_poisson_power":True,
        "raw_data_opened":False,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
