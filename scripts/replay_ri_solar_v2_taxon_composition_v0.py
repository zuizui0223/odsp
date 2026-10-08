#!/usr/bin/env python3
"""Reproduce the frozen first RI v2 taxonomic descriptive check only."""
from pathlib import Path
import json
from odsp.ri_solar_v2_taxon_composition_v0 import run_from_files

ROOT=Path(__file__).resolve().parents[1]
original=ROOT/".analysis_input"/"RI_SOLAR_CLOCK_YEARSEASON_V2_FIRST_RESULT.json"
plan=ROOT/"RI_SOLAR_V2_POSTOUTCOME_TAXON_COMPOSITION_CONTRACT.json"
out=ROOT/"RI_SOLAR_V2_TAXON_COMPOSITION_FIRST_RECEIPT.json"

def main():
    d=run_from_files(original,plan,out)
    x=d["provisional_taxon_equal_weight"]
    summary={
        "status":d["taxon_screen"]["status"],
        "original_winter":d["original_all_site_weighted_gains"]["winter"],
        "original_summer":d["original_all_site_weighted_gains"]["summer"],
        "provisional_taxa":d["taxon_screen"]["provisional_site_event_pass_count"],
        "provisional_winter":x["winter_mean"],
        "provisional_summer":x["summer_mean"],
        "winter_positive_summer_negative":x["winter_positive_summer_negative_count"],
        "winter_negative_summer_positive":x["winter_negative_summer_positive_count"],
        "all_original_claims_unchanged":d["original_ecological_v0_v1_v2_inference_reclassified"] is False,
        "receipt":out.name,
    }
    print(json.dumps(summary,sort_keys=True,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
