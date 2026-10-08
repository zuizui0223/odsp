#!/usr/bin/env python3
"""First source-row-free published species-count sparsity scenario."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from odsp.uljin_published_taxon_rate_sparsity_v1 import (
    published_taxon_rate_sparsity_scenario,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_PUBLISHED_SPECIES_SPARSE_MATCH_SENSITIVITY_V1_CONTRACT.json"
OUT=ROOT/"ULJIN_PUBLISHED_SPECIES_SPARSE_MATCH_V1_FIRST_RECEIPT.json"


def main():
    raw=PLAN.read_bytes()
    answer=published_taxon_rate_sparsity_scenario(json.loads(raw))
    answer["frozen_design_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.write_text(
        json.dumps(answer,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status":answer["status"],
        "matched_pairs_hypothetical_total":
            answer["sum_hypothetical_matched_station_species_date_pairs"],
        "individual_taxa_expected_pairs":{
            x["taxon"]:x["expected_station_taxon_date_pairs_with_both_dates_detected"]
            for x in answer["published_species_scenarios"]
        },
        "real_camera_or_animal_records_opened":False,
        "receipt":OUT.name,
    },ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
