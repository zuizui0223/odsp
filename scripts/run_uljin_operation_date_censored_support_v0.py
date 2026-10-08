#!/usr/bin/env python3
"""Only synthetic date-censored uptime examples; NO EcoBank ZIP/CSV access."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from odsp.uljin_operation_date_censored_support_v0 import (
    classify_date_censored_mirror_support,
)

ROOT=Path(__file__).resolve().parents[1]
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
PLAN=ROOT/"ULJIN_OPERATION_DATE_CENSORED_SUPPORT_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_OPERATION_DATE_CENSORED_SUPPORT_V0_FIRST_RECEIPT.json"


def dep(start="2022-04-01",end="2022-10-01"):
    return {"Station":"UJ1_SYNTHETIC","DeploymentStartDate":start,
            "DeploymentEndDate":end}
def off(start,end):
    return {"Station":"UJ1_SYNTHETIC","DowntimeStartDate":start,
            "DowntimeEndDate":end}

def main()->int:
    frozen=PLAN.read_bytes()
    cal=json.loads(CAL.read_bytes())
    plan=json.loads(frozen)
    examples={
        "full_interior_days":([dep()],[]),
        "boundary_start_date":([dep(start="2022-05-01")],[]),
        "one_date_unknown_hour_outage":([dep()],[off("2022-05-01","2022-05-01")]),
        "guaranteed_full_date_outage":([dep()],[off("2022-04-30","2022-05-02")]),
        "single_date_only_deployment":([dep(start="2022-05-01",end="2022-05-01")],[]),
    }
    results={}
    for label,(deploy,outages) in examples.items():
        result=classify_date_censored_mirror_support(
            cal,plan,deploy,outages,synthetic_complete_downtime_roster=True)
        results[label]=result["region_only_counts"]["UJ1"]
    unknown=classify_date_censored_mirror_support(
        cal,plan,[dep()],[],synthetic_complete_downtime_roster=False)
    if (unknown["status"]!="HOLD_DOWNTIME_COMPLETENESS_UNKNOWN"
        or results["full_interior_days"]["guaranteed_eligible_pairs"]!=41
        or results["boundary_start_date"]["ambiguous_pairs"]!=1
        or results["one_date_unknown_hour_outage"]["ambiguous_pairs"]!=1
        or results["guaranteed_full_date_outage"]["definitely_ineligible_pairs"]!=1
        or results["guaranteed_full_date_outage"]["ambiguous_pairs"]!=1
        or results["guaranteed_full_date_outage"]["guaranteed_eligible_pairs"]!=39
        or results["single_date_only_deployment"]["guaranteed_eligible_pairs"]!=0):
        raise ValueError("frozen synthetic dated-censored truth world failed")
    output={
       "schema_version":1,
       "method":"uljin_operation_date_censored_pair_support_v0",
       "status":"PASS_SOURCE_FREE_DATE_CENSORED_SYNTHETIC_SUPPORT_ONLY",
       "source_free_contract_sha256":hashlib.sha256(frozen).hexdigest(),
       "original_41_date_pairs_unchanged":True,
       "synthetic_cases":results,
       "unknown_downtime_completeness_status":unknown["status"],
       "no_animal_or_original_camera_source_records_read":True,
       "archive_authenticated":False,
       "independent_hardware_operation_lineage_verified":False,
       "real_Uljin_eligibility_computed":False,
       "historical_ODSP_routes_modified":False
    }
    OUT.write_text(json.dumps(output,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
       "status":output["status"],
       "cases":{k:{
           "eligible":v["guaranteed_eligible_pairs"],
           "ineligible":v["definitely_ineligible_pairs"],
           "unknown":v["ambiguous_pairs"]
       } for k,v in results.items()},
       "real_source_or_wildlife_rows_opened":False
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
