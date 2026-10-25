"""One pre-frozen SERIAL technical replay of exactly five prior original source HOLDs.

Purely technical follow-on. Uses the already-frozen *unchanged* original
shared-cell ecological rules and original checksum provenance, not a new
biological test or a selective replacement of the v0 original first results.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from scripts.movebank_native_ecology_20261019 import HERE
from scripts.global_solar_azimuth_multitaxon_shared_cells_v0 import (
    evaluate_source, source_preselection,
)

CONTRACT = HERE / "research/GLOBAL_SOLAR_AZIMUTH_SHARED_CELL_SOURCE_REPLAY_V1_CONTRACT.json"
PREVIOUS_FIRST = HERE / "research/GLOBAL_SOLAR_AZIMUTH_MULTI_SOURCE_SHARED_CELL_V0_FIRST_RESULT_20261025.json"


def fixed_serial_recovery_sources():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    previous = json.loads(PREVIOUS_FIRST.read_text(encoding="utf-8"))
    if contract["version"] != "solar-azimuth-shared-cell-technical-source-replay-v1":
        raise ValueError("Recovery protocol missing")
    if previous["first_workflow_run_id"] != 40165922718:
        raise ValueError("Original first-result receipt not preserved")
    fail = contract["fixed_failed_original_source_package_UUIDs"]
    prev_held = [x["package_uuid"] for x in previous["all_source_results"]
                 if x["source_status"] == "SOURCE_HOLD"]
    if len(fail) != 5 or len(set(fail)) != 5 or set(fail) != set(prev_held):
        raise ValueError("Recovery UUIDs differ from original source failure roster")
    candidates = source_preselection()
    candidate_by_id = {x["package_uuid"]: x for x in candidates}
    if len(candidate_by_id) != 10 or not set(fail) <= candidate_by_id.keys():
        raise ValueError("Unselected or missing original source")
    return [candidate_by_id[x] for x in fail]


def run_serial(out: Path):
    sources = fixed_serial_recovery_sources()
    results = []
    for row in sources:
        result = evaluate_source(row, out)  # frozen exact v0 algorithm, no modification
        result["technical_replay"] = "v1_single_serial_preselected_original_held_source"
        results.append(result)
        print("SOLAR_SHARED_CELL_SERIAL_RECOVERY_SOURCE " +
              json.dumps(result, sort_keys=True, ensure_ascii=False), flush=True)
    return {
        "version":"solar-azimuth-shared-cell-technical-source-replay-v1",
        "parent_first_workflow_run_id":40165922718,
        "preselected_held_source_archives":len(sources),
        "serial_original_source_MD5_verified":sum(
            x["source_status"] == "source_qualified_all_pairs_evaluated" for x in results),
        "still_SOURCE_HOLD":sum(x["source_status"] == "SOURCE_HOLD" for x in results),
        "supported_same_grid_month_clock_taxon_pairs":sum(
            p["status"] == "SUPPORTED_SOURCE_DESCRIPTIVE"
            for r in results for p in r["shared_taxon_pairs"]),
        "all_retried_source_results":results,
        "limitation":"Post-original-first technical replay. Failed original v0 source statuses are not rewritten. No new significance claims or causal solar directionality."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    report=run_serial(args.out)
    (args.out/"solar_azimuth_shared_cell_serial_recovery_v1.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SOLAR_SHARED_CELL_SERIAL_RECOVERY_SUMMARY "+
          json.dumps({k:v for k,v in report.items() if k!="all_retried_source_results"},
                     sort_keys=True), flush=True)


if __name__=="__main__":
    main()
