#!/usr/bin/env python3
"""Original NIE EcoBank Version 1.1 ZIP four-species event feasibility.

NO internet access is assumed or hidden. Requires a verified ORIGINAL
archive ZIP obtained independently from
https://doi.org/10.22756/ETC.20260000001022, plus a documented SHA256
from the trusted release host. Source ZIP names alone are not trust.

Default without an archive is a valid source-HOLD result.
Even with source ZIP: only 4-taxon timestamp feasibility, NEVER
hourly camera exposure or biological effect-size estimates.
"""
import argparse
import json
from pathlib import Path

from odsp.uljin_original_source_zip_feasibility_v0 import (
    read_original_source_feasibility
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_ORIGINAL_V1P1_SOURCE_FEASIBILITY_V0_CONTRACT.json"
BIOLOGY=ROOT/"ULJIN_FOUR_UNGULATE_TEMPORAL_REFUGE_ECOLOGY_V0_CONTRACT.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--original-v1p1-zip",type=Path)
    p.add_argument("--independently-attested-original-v1p1",action="store_true")
    p.add_argument("--original-release-sha256",
                   help="SHA256 independently documented for original Version 1.1 ZIP")
    args=p.parse_args()
    out=read_original_source_feasibility(
        json.loads(PLAN.read_text()),
        json.loads(BIOLOGY.read_text()),
        json.loads(CAL.read_text()),
        args.original_v1p1_zip,
        externally_verified_original_v1p1=(
            args.independently_attested_original_v1p1),
        externally_verified_archive_sha256=args.original_release_sha256)
    print(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
