#!/usr/bin/env python3
"""Execute the frozen MH_ANTWERPEN state-resolved prediction endpoint.

The design is read from ``MH_ANTWERPEN_STATE_PREDICTION_CONTRACT.json``.  The
script downloads only the prospectively named public GPS files, verifies every
MD5, parses admissible events, applies the frozen 10-minute thinning and
individual admission rules, then runs leave-one-individual-out primary RF and
logit sensitivity scoring.  No threshold or model selection occurs here.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request

from odsp.mh_antwerpen_prediction import (
    STATE_LABELS,
    endpoint_decision,
    individual_admission,
    parse_admissible_row,
    run_leave_one_individual_out,
    thin_10min_earliest,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "MH_ANTWERPEN_STATE_PREDICTION_CONTRACT.json"
ZENODO_BASE = "https://zenodo.org/records/10054153/files"


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "odsp-state-prediction/0.10"})
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as out:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            out.write(block)


def _required_columns(contract: dict[str, object]) -> set[str]:
    return set(contract["source"]["required_columns"])


def execute(output: Path) -> dict[str, object]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract["outcome_access_before_freeze"] is not False:
        raise ValueError("contract is not prospectively frozen")

    parse_failures: dict[str, int] = {}
    source_receipts: list[dict[str, object]] = []
    all_events = []
    raw_row_count = 0
    required = _required_columns(contract)

    with tempfile.TemporaryDirectory(prefix="mh-antwerpen-") as tmp:
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
            file_admitted = 0
            with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                columns = set(reader.fieldnames or ())
                missing = sorted(required - columns)
                if missing:
                    raise ValueError(f"{name} is missing required columns: {missing}")
                for row in reader:
                    raw_row_count += 1
                    file_rows += 1
                    event, reason = parse_admissible_row(row, source_file=name)
                    if event is None:
                        key = reason or "unknown_parse_failure"
                        parse_failures[key] = parse_failures.get(key, 0) + 1
                        continue
                    all_events.append(event)
                    file_admitted += 1
            source_receipts.append(
                {
                    "name": name,
                    "expected_md5": expected_md5,
                    "observed_md5": observed_md5,
                    "compressed_bytes": path.stat().st_size,
                    "raw_rows": file_rows,
                    "admissible_rows_before_thinning": file_admitted,
                }
            )

    thinned = thin_10min_earliest(all_events)
    admission_cfg = contract["independence_and_admission"]
    admissions = individual_admission(
        thinned,
        min_events=int(admission_cfg["minimum_thinned_events_per_individual"]),
        min_states=int(admission_cfg["minimum_supported_states_per_individual"]),
        min_events_per_supported_state=int(admission_cfg["minimum_events_in_each_supported_state"]),
    )
    eligible = [item.individual_id for item in admissions if item.eligible]

    folds = []
    if len(eligible) >= int(admission_cfg["minimum_eligible_individuals"]):
        folds = list(
            run_leave_one_individual_out(
                thinned,
                eligible,
                random_state=int(contract["models"]["primary"]["random_state"]),
            )
        )

    decision = endpoint_decision(
        admissions,
        folds,
        minimum_eligible_individuals=int(admission_cfg["minimum_eligible_individuals"]),
    )

    state_counts_all = {state: 0 for state in STATE_LABELS}
    for event in thinned:
        state_counts_all[event.altitude_state] += 1

    primary_feature_importance = None
    scored_importances = [
        fold.primary_feature_importance
        for fold in folds
        if fold.primary_feature_importance is not None
    ]
    if scored_importances:
        names = tuple(scored_importances[0])
        primary_feature_importance = {
            name: sum(float(item[name]) for item in scored_importances) / len(scored_importances)
            for name in names
        }

    result = {
        "schema_version": 1,
        "endpoint": "mh_antwerpen_state_prediction_v1",
        "contract_id": contract["contract_id"],
        "source": {
            "archive_doi": contract["source"]["archive_doi"],
            "movebank_study_id": contract["source"]["movebank_study_id"],
            "files": source_receipts,
        },
        "data_flow": {
            "raw_row_count": raw_row_count,
            "admissible_before_thinning": len(all_events),
            "thinned_event_count": len(thinned),
            "parse_or_filter_failures": dict(sorted(parse_failures.items())),
            "thinned_state_counts": state_counts_all,
            "individual_count_before_admission": len(admissions),
            "eligible_individual_count": len(eligible),
        },
        "admissions": [item.as_dict() for item in admissions],
        "folds": [fold.as_dict() for fold in folds],
        "primary_mean_feature_importance_descriptive": primary_feature_importance,
        "decision": decision,
        "claim_ceiling": contract["claim_ceiling"],
        "closed_endpoints_untouched": contract["frozen_endpoints_untouched"],
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
        default=Path("artifacts/MH_ANTWERPEN_STATE_PREDICTION_RESULT.json"),
    )
    args = parser.parse_args()
    result = execute(args.output)
    print(
        json.dumps(
            {
                "terminal_category": result["decision"]["terminal_category"],
                "eligible_individual_count": result["decision"]["eligible_individual_count"],
                "thinned_event_count": result["data_flow"]["thinned_event_count"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
