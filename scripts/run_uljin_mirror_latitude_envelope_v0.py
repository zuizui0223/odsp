#!/usr/bin/env python3
"""No animal source: replay original 41 dates across a public latitude envelope."""
import hashlib
import json
from pathlib import Path

from odsp.uljin_mirror_latitude_envelope_v0 import original_pairs_latitude_sensitivity

ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
PLAN=ROOT/"ULJIN_MIRROR_LATITUDE_ENVELOPE_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_MIRROR_LATITUDE_ENVELOPE_FIRST_RECEIPT.json"


def main():
    frozen=PLAN.read_bytes()
    result=original_pairs_latitude_sensitivity(
        json.loads(MAIN.read_text()), json.loads(frozen)
    )
    result["plan_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "pairs":result["original_pair_count_retained_without_rematching"],
        "latitude_envelope":result["public_latitude_envelope"],
        "source_camera_or_wildlife_rows_opened":False,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
