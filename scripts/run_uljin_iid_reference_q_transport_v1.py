#!/usr/bin/env python3
"""First pre-frozen IID reference q transport versus target q standardization."""
import hashlib
import json
from pathlib import Path
from odsp.uljin_iid_reference_q_transport_v1 import (
    iid_reference_transport_full_panel,
)
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_IID_REFERENCE_Q_TRANSPORT_V1_CONTRACT.json"
OLD=ROOT/"ULJIN_Q_TRANSPORT_DISTANCE_MIX_V0_FIRST_RESULT_LEDGER.json"
OUT=ROOT/"ULJIN_IID_REFERENCE_Q_TRANSPORT_V1_FIRST_RECEIPT.json"


def main()->int:
    frozen=PLAN.read_bytes()
    out=iid_reference_transport_full_panel(
        json.loads(frozen),json.loads(OLD.read_bytes()))
    if (out["total_worlds"]!=2400 or
        not out["parent_all_first_frozen_source_free_outcomes_replayed"]):
        raise ValueError("first 2400-world source-transport replay incomplete")
    out["pre_first_outcome_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":out["status"],
        "parent_all_previous_original_results_replayed":True,
        "cases":[{
            "world":row["world"],"n_per_original_q_stratum_cell":
                row["n_reference_per_distance_q_cell_from_parent"],
            "iid_valid_reference_positive_fraction":
                row["proper_iid_source_reference_certification_fraction"],
            "target_distance_standardized_positive_fraction":
                row["target_distance_standardized_certification_fraction"],
            "iid_reference_four_q_coverage":
                row["iid_source_reference_four_q_simultaneous_coverage"]
        } for row in out["case_results"]],
        "real_reference_or_animal_data_opened":False,
    },sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
