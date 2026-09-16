from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import pytest

from odsp.external_paired_lattice_freeze_manifest import create_paired_external_lattice_freeze_manifest
from odsp.untouched_external_refit_shared_block_positive_lattice_contract_v4 import (
    run_untouched_external_paired_all_refit_lattice_contract_v4,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _subsets():
    for size in range(3):
        yield from itertools.combinations(("A", "B"), size)


def _column(subset: tuple[str, ...]) -> str:
    return "score_base" if not subset else "score_" + "_".join(x.lower() for x in subset)


def _freeze_plan() -> dict[str, object]:
    return {
        "schema_version": 1,
        "upstream_model_set_id": "pairing-lock-models-v1",
        "external_dataset_id": "pairing-lock-external-v1",
        "roster": {
            "path": "roster.csv",
            "format": "csv",
            "row_id_column": "row_id",
            "group_column": "group",
            "block_column": "block",
            "weight_column": "weight",
        },
        "refit_ids": ["r00", "r01"],
        "score": {
            "kind": "log",
            "name": "log",
            "orientation": "higher_is_better",
            "common_scoring_rule": True,
            "common_reference_measure": True,
        },
        "base_information": ["baseline"],
        "information_blocks": [
            {"name": "A", "variables": ["a"]},
            {"name": "B", "variables": ["b"]},
        ],
        "nodes": [
            {"blocks": list(subset), "score_column": _column(subset)}
            for subset in _subsets()
        ],
        "certification": {
            "alternative": "greater",
            "familywise_lower_confidence_level": 0.95,
            "bootstrap_draws": 500,
            "seed": 20260916,
            "minimum_refits": 2,
            "minimum_shared_blocks": 4,
            "gain_tolerance": 0.0,
        },
    }


def _pairing_roster() -> list[dict[str, object]]:
    return [
        {
            "row_id": f"{group}-b{block_i}",
            "group": group,
            "block": f"b{block_i}",
            "weight": 1.0,
        }
        for group in ("g0", "g1")
        for block_i in range(4)
    ]


def _score_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for refit in ("r00", "r01"):
        for group in ("g0", "g1"):
            for block_i in range(4):
                row: dict[str, object] = {
                    "row_id": f"{group}-b{block_i}",
                    "refit_id": refit,
                    "group": group,
                    "block": f"b{block_i}",
                    "weight": 1.0,
                }
                for subset in _subsets():
                    row[_column(subset)] = 0.3 * len(subset)
                rows.append(row)
    return rows


def _contract(manifest: Path) -> dict[str, object]:
    plan = _freeze_plan()
    frozen = json.loads(manifest.read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "endpoint_id": "pairing-freeze-regression-v4",
        "upstream_model_set_id": plan["upstream_model_set_id"],
        "external_dataset_id": plan["external_dataset_id"],
        "data": {"path": "scores.csv", "format": "csv"},
        "columns": {
            "row_id": "row_id",
            "refit_id": "refit_id",
            "group": "group",
            "block": "block",
            "weight": "weight",
        },
        "score": plan["score"],
        "external_validation": {
            "dataset_role": "untouched_external_validation",
            "freeze_manifest": {
                "path": "freeze.json",
                "sha256": _sha256(manifest),
                "frozen_at_utc": frozen["frozen_at_utc"],
            },
            "external_outcomes_first_accessed_at_utc": "2099-01-01T00:00:00Z",
            "development_data_disjoint": True,
            "external_rows_used_for_upstream_fit": False,
            "external_rows_used_for_refit_generation": False,
            "external_rows_used_for_model_selection": False,
            "external_rows_used_for_filtration_selection": False,
            "external_outcomes_used_for_threshold_selection": False,
            "external_outcomes_used_for_score_rule_selection": False,
            "external_outcomes_used_for_any_development_decision": False,
            "models_frozen_before_external_outcome_access": True,
            "refit_ensemble_frozen_before_external_outcome_access": True,
            "filtration_frozen_before_external_outcome_access": True,
            "score_rule_frozen_before_external_outcome_access": True,
            "gain_tolerance_frozen_before_external_outcome_access": True,
            "alternative_frozen_before_external_outcome_access": True,
        },
        "base_information": plan["base_information"],
        "information_blocks": plan["information_blocks"],
        "nodes": plan["nodes"],
        "certification": plan["certification"],
    }


def test_row_pairing_metadata_cannot_change_after_preoutcome_freeze(tmp_path: Path):
    roster = tmp_path / "roster.csv"
    _write_csv(roster, _pairing_roster())

    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(_freeze_plan()), encoding="utf-8")
    manifest = tmp_path / "freeze.json"
    create_paired_external_lattice_freeze_manifest(plan, manifest)

    rows = _score_rows()
    # Reassign two rows between validation groups after the freeze while preserving
    # the exact row IDs and each group's positive-mass shared-block support.
    for row in rows:
        if row["row_id"] == "g0-b0":
            row["group"] = "g1"
        elif row["row_id"] == "g1-b0":
            row["group"] = "g0"
    _write_csv(tmp_path / "scores.csv", rows)

    endpoint = tmp_path / "endpoint.json"
    endpoint.write_text(json.dumps(_contract(manifest)), encoding="utf-8")

    with pytest.raises(ValueError, match="pairing|paired row metadata|semantic mismatch"):
        run_untouched_external_paired_all_refit_lattice_contract_v4(endpoint)
