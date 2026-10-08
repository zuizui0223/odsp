#!/usr/bin/env python3
"""First source-free known-truth conditional branch-shape synthetic panel.

A strict zero-preserving conditional Poisson model, trained on invented
stations, is scored on disjoint invented stations in two KNOWN worlds.
Even if the model works this does NOT establish seasonal ecological
memory, independent operation logs or any Uljin source event analysis.
"""
import hashlib
import json
from pathlib import Path

from odsp.uljin_conditional_branch_shape_v0 import (
    MirrorCountCell,expected_falling_probability,score_heldout_station_frame
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_CONDITIONAL_BINOMIAL_ZERO_PRESERVING_V0_CONTRACT.json"
OUTPUT=ROOT/"ULJIN_CONDITIONAL_BINOMIAL_SYNTHETIC_V0_FIRST_RECEIPT.json"


def world(betas):
    training=[]; heldout=[]
    for i in range(26):
        region="UJ1" if i%2==0 else "UJ2"
        station=f"{region}-invented-{i:03d}"
        rows=training if i<16 else heldout
        for pair in range(5):
            for bin_no in range(6):
                a,b=(4.,2.) if (pair+bin_no)%2==0 else (3.,4.)
                n=100
                p=expected_falling_probability(a,b,betas[bin_no])
                f=round(n*p)
                rows.append(MirrorCountCell(
                    station,region,"invented ungulate",f"synthetic-{pair}",
                    bin_no,n-f,f,a,b
                ))
    return score_heldout_station_frame(training,heldout)


def main():
    raw=CONTRACT.read_bytes()
    contract=json.loads(raw)
    if (
        contract["method_id"]!="uljin_mirror_exposure_offset_conditional_binomial_v0"
        or contract["status"]!="FROZEN_SYNTHETIC_METHOD_ONLY_BEFORE_ANY_ECOBANK_EVENT_SOURCE_ACCESS"
        or contract["comparators"]["penalty_lambda"]!=2.
        or contract["comparators"]["intercept_ridge"]!=1e-6
    ):
        raise ValueError("original before-synthetic frozen design changed")
    no_shape=world([.25]*6)
    shape=world([-1.3,-.9,-.4,.4,.9,1.3])
    if not (
        abs(no_shape["test_site_equal_mean_conditional_gain"])<.0005
        and shape["test_site_equal_mean_conditional_gain"]>.15
        and no_shape["test_physical_sites"]==10
        and shape["test_physical_sites"]==10
    ):
        raise ValueError("frozen known-truth synthetic gates failed")
    output={
        "schema_version":1,
        "status":"FIRST_TWO_SYNTHETIC_WORLDS_PASS",
        "frozen_plan_sha256":hashlib.sha256(raw).hexdigest(),
        "world_no_shape":no_shape,
        "world_branch_by_clock_bin_shape":shape,
        "original_Uljin_EcoBank_record_accessed":False,
        "camera_operation_lineage_or_spatial_iid_verified":False,
        "real_seasonal_photoperiod_hysteresis_identified":False,
        "first_source_free_hypothesis_causally_identified":False,
        "original_ODSP_qualified_inference_reclassified":False,
    }
    OUTPUT.write_text(json.dumps(output,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "status":output["status"],
        "no_shape_gain":no_shape["test_site_equal_mean_conditional_gain"],
        "shape_gain":shape["test_site_equal_mean_conditional_gain"],
        "real_animal_data_accessed":False,
        "receipt":OUTPUT.name
    },sort_keys=True))
if __name__=="__main__":
    main()
