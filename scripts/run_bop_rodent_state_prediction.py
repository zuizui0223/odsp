#!/usr/bin/env python3
"""Execute the frozen BOP_RODENT v3 multi-species state-prediction endpoint."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request

import numpy as np

from odsp.bop_rodent_prediction import (
    STATE_LABELS,
    admitted_species,
    build_admissions,
    deterministic_folds,
    execute_five_fold_prediction,
    parse_admissible_bop_row,
    terminal_decision,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "BOP_RODENT_STATE_PREDICTION_CONTRACT.json"
ZENODO_BASE = "https://zenodo.org/records/10055071/files"


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "odsp-state-prediction/0.10"})
    with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as out:
        for block in iter(lambda: response.read(1024 * 1024), b""):
            out.write(block)


def _state_counts(events):
    result = {state: 0 for state in STATE_LABELS}
    for event in events:
        result[event.altitude_state] += 1
    return result


def execute(output: Path) -> dict[str, object]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract["outcome_access_before_freeze"] is not False:
        raise ValueError("contract is not prospectively frozen")

    required = set(contract["source"]["required_columns"])
    source_receipts: list[dict[str, object]] = []
    failures: dict[str, int] = {}
    raw_rows = 0
    admissible_rows = 0
    # Stream directly into the frozen hourly-thinned representation so the
    # endpoint never requires the complete multi-year decompressed table in RAM.
    chosen = {}

    with tempfile.TemporaryDirectory(prefix="bop-rodent-") as tmp:
        data_dir = Path(tmp)
        for spec in contract["source"]["gps_files"]:
            name = str(spec["name"])
            expected_md5 = str(spec["md5"])
            path = data_dir / name
            _download(f"{ZENODO_BASE}/{name}", path)
            observed_md5 = _md5(path)
            if observed_md5 != expected_md5:
                raise ValueError(f"MD5 mismatch for {name}: {observed_md5} != {expected_md5}")
            file_rows = 0
            file_admissible = 0
            with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                columns = set(reader.fieldnames or ())
                missing = sorted(required - columns)
                if missing:
                    raise ValueError(f"{name} is missing required columns: {missing}")
                for row in reader:
                    raw_rows += 1
                    file_rows += 1
                    event, reason = parse_admissible_bop_row(row, source_file=name)
                    if event is None:
                        key = reason or "unknown_filter_failure"
                        failures[key] = failures.get(key, 0) + 1
                        continue
                    admissible_rows += 1
                    file_admissible += 1
                    hour_bin = int(event.timestamp_utc.timestamp() // 3600)
                    key = (event.individual_id, hour_bin)
                    previous = chosen.get(key)
                    if previous is None or event.timestamp_utc < previous.timestamp_utc:
                        chosen[key] = event
            source_receipts.append(
                {
                    "name": name,
                    "expected_md5": expected_md5,
                    "observed_md5": observed_md5,
                    "compressed_bytes": path.stat().st_size,
                    "raw_rows": file_rows,
                    "admissible_rows_before_thinning": file_admissible,
                }
            )

    thinned = tuple(sorted(chosen.values(), key=lambda e: (e.individual_id, e.timestamp_utc)))
    cfg = contract["independence_and_admission"]
    admissions = build_admissions(
        thinned,
        min_events=int(cfg["individual_minimum_hourly_thinned_events"]),
        min_states=int(cfg["minimum_supported_altitude_states_per_individual"]),
        min_state_events=int(cfg["minimum_events_in_each_supported_state"]),
        min_individuals_per_species=int(cfg["minimum_eligible_individuals_per_admitted_species"]),
    )
    species_labels = admitted_species(admissions)
    eligible_ids = {item.individual_id for item in admissions if item.final_eligible}
    final_events = tuple(event for event in thinned if event.individual_id in eligible_ids)

    can_open = (
        len(species_labels) >= int(cfg["minimum_admitted_species"])
        and len(eligible_ids) >= int(cfg["minimum_total_eligible_individuals"])
    )
    heldout_results = ()
    if can_open:
        heldout_results = execute_five_fold_prediction(
            final_events,
            admissions,
            random_state=int(contract["models"]["primary"]["random_state"]),
        )
    decision = terminal_decision(
        admissions,
        heldout_results,
        minimum_species=int(cfg["minimum_admitted_species"]),
        minimum_individuals=int(cfg["minimum_total_eligible_individuals"]),
    )

    by_species = {}
    for species in sorted({item.species for item in admissions}):
        items = [item for item in admissions if item.species == species]
        by_species[species] = {
            "individual_count": len(items),
            "individually_eligible_count": sum(item.individually_eligible for item in items),
            "final_eligible_count": sum(item.final_eligible for item in items),
            "hourly_thinned_event_count": sum(item.thinned_event_count for item in items),
            "state_counts": {
                state: int(sum(item.state_counts[state] for item in items)) for state in STATE_LABELS
            },
        }

    feature_importance = None
    importance_rows = [
        item.primary_feature_importance
        for item in heldout_results
        if item.primary_feature_importance is not None
    ]
    if importance_rows:
        names = tuple(importance_rows[0])
        feature_importance = {
            name: float(np.mean([row[name] for row in importance_rows])) for name in names
        }

    result = {
        "schema_version": 1,
        "endpoint": "bop_rodent_state_prediction_v1",
        "contract_id": contract["contract_id"],
        "source": {
            "archive_doi": contract["source"]["archive_doi"],
            "archive_version": contract["source"]["archive_version"],
            "movebank_study_id": contract["source"]["movebank_study_id"],
            "files": source_receipts,
        },
        "data_flow": {
            "raw_row_count": raw_rows,
            "admissible_before_thinning": admissible_rows,
            "hourly_thinned_event_count": len(thinned),
            "eligible_event_count": len(final_events),
            "filter_failures": dict(sorted(failures.items())),
            "all_thinned_state_counts": _state_counts(thinned),
            "individual_count_before_admission": len(admissions),
            "eligible_individual_count": len(eligible_ids),
            "admitted_species": list(species_labels),
            "admitted_species_count": len(species_labels),
        },
        "species_summary": by_species,
        "admissions": [item.as_dict() for item in admissions],
        "fold_assignment": deterministic_folds(admissions),
        "heldout_results": [item.as_dict() for item in heldout_results],
        "primary_mean_feature_importance_descriptive": feature_importance,
        "decision": decision,
        "claim_ceiling": contract["claim_ceiling"],
        "closed_endpoints_untouched": contract["closed_endpoints_untouched"],
        "retuning_performed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/BOP_RODENT_STATE_PREDICTION_RESULT.json"),
    )
    args = parser.parse_args()
    result = execute(args.output)
    print(json.dumps({
        "terminal_category": result["decision"]["terminal_category"],
        "admitted_species_count": result["decision"]["admitted_species_count"],
        "eligible_individual_count": result["decision"]["eligible_individual_count"],
        "hourly_thinned_event_count": result["data_flow"]["hourly_thinned_event_count"],
        "output": str(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
