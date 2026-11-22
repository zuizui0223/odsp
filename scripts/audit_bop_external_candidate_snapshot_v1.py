#!/usr/bin/env python3
"""Reproduce seven public metadata screen decisions, without source downloads.

Reads only the committed post-exploration candidate synopsis. Does not open
provider GPS, crosswalks, outcome labels, or individual identity records.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

from odsp.external_source_candidate_gate import (
    freeze_candidate_source,
    screen_candidate_source,
)

REPOSITORY = Path(__file__).resolve().parents[1]
SOURCE = REPOSITORY / "research/BOP_EXTERNAL_SOURCE_CANDIDATE_METADATA_V1.json"


def audit_snapshot() -> dict[str, object]:
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    if set(raw) != {
        "schema_version", "evidence_role", "snapshot_date",
        "calibrated_goal", "label_or_gps_data_opened", "candidates",
    } or raw["schema_version"] != 1 or raw["label_or_gps_data_opened"] is not False:
        raise ValueError("candidate source registry lacks its frozen safe schema")
    results = []
    candidates = raw["candidates"]
    if not isinstance(candidates, list) or len(candidates) != 7:
        raise ValueError("unexpected fixed candidate universe")
    for entry in candidates:
        if set(entry) != {
            "target_stratum", "candidate", "publisher_note",
            "expected_reduced_content", "expected_historic_rank",
        }:
            raise ValueError("candidate registry has a forbidden extra field")
        source = freeze_candidate_source(entry["candidate"])
        outputs = []
        for route, aim, declared in (
            ("new_reduced_common_input", "positive_population_content", "expected_reduced_content"),
            ("historic_rf_direct", "new_animal_rank", "expected_historic_rank"),
        ):
            result = screen_candidate_source(
                source,
                route=route,
                aim=aim,
                target_stratum=entry["target_stratum"],
            )
            if result.status != entry[declared]:
                raise ValueError("candidate metadata classification departed from pinned receipt")
            if result.status == "ELIGIBLE_FOR_SOURCE_ONLY_PREFLIGHT":
                raise ValueError("screen unexpectedly promoted a known candidate")
            outputs.append(result.as_public_dict())
        results.append({
            "candidate_id": source.candidate_id,
            "publisher_metadata_source_sha256": source.sha256,
            "screens": outputs,
        })
    return {
        "schema_version": 1,
        "stage": "publisher_metadata_screen_after_exploratory_discovery",
        "source_registry_path": str(SOURCE.relative_to(REPOSITORY)),
        "no_tracking_or_outcome_files_opened": True,
        "real_cross_source_biological_data_admitted": False,
        "candidate_count": len(results),
        "screen_count": 2 * len(results),
        "results": results,
        "historic_bop_terminal": "empirical_state_prediction_mixed",
        "dryad_rf_terminal": "NOT_ADMITTED",
        "cross_source_identity_proven": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(audit_snapshot(), indent=2, sort_keys=True, ensure_ascii=False))
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"metadata audit refused: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
