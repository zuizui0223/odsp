from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from odsp.untouched_external_refit_positive_contract import (
    run_untouched_external_refit_positive_contract,
    validate_untouched_external_refit_positive_contract,
)


def _rows(refit_count: int = 8, group_count: int = 2, blocks_per_group: int = 8):
    rows: list[dict[str, object]] = []
    for refit_index in range(refit_count):
        for group_index in range(group_count):
            for block_index in range(blocks_per_group):
                row_id = f"g{group_index}-b{block_index}"
                rows.append(
                    {
                        "row_id": row_id,
                        "refit_id": f"r{refit_index:02d}",
                        "group": f"g{group_index}",
                        "block": f"g{group_index}-b{block_index}",
                        "weight": 1.0,
                        "score_pooled": 0.0,
                        "score_coarse": 0.4,
                        "score_fine": 0.7,
                    }
                )
    return rows


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract(manifest_sha: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "endpoint_id": "external-test-v1",
        "data": {"path": "scores.csv", "format": "csv"},
        "columns": {
            "row_id": "row_id",
            "refit_id": "refit_id",
            "group": "group",
            "block": "block",
            "weight": "weight",
        },
        "score": {
            "kind": "log",
            "name": "log",
            "orientation": "higher_is_better",
            "common_scoring_rule": True,
            "common_reference_measure": True,
        },
        "external_validation": {
            "dataset_role": "untouched_external_validation",
            "freeze_manifest": {
                "path": "freeze.json",
                "sha256": manifest_sha,
                "frozen_at_utc": "2026-09-01T00:00:00Z",
            },
            "external_outcomes_first_accessed_at_utc": "2026-09-15T00:00:00Z",
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
        "levels": [
            {"name": "pooled", "information": [], "score_column": "score_pooled"},
            {"name": "coarse", "information": ["coarse"], "score_column": "score_coarse"},
            {"name": "fine", "information": ["coarse", "fine"], "score_column": "score_fine"},
        ],
        "certification": {
            "alternative": "greater",
            "familywise_lower_confidence_level": 0.95,
            "bootstrap_draws": 500,
            "seed": 20260916,
            "minimum_refits": 8,
            "minimum_blocks_per_group": 8,
            "gain_tolerance": 0.0,
            "reference_refit_id": "r00",
        },
    }


def _setup(tmp_path: Path, rows: list[dict[str, object]] | None = None):
    manifest = tmp_path / "freeze.json"
    manifest.write_text(
        json.dumps(
            {
                "manifest_type": "odsp-pre-external-outcome-freeze",
                "model_set": "frozen",
                "refit_ensemble": "r00-r07",
                "filtration": ["pooled", "coarse", "fine"],
                "alternative": "greater",
                "gain_tolerance": 0.0,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    data = tmp_path / "scores.csv"
    _write_csv(data, _rows() if rows is None else rows)
    contract = _contract(_sha256(manifest))
    contract_path = tmp_path / "endpoint.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    return manifest, data, contract, contract_path


def test_untouched_external_refit_contract_runs_full_consensus(tmp_path: Path):
    manifest, data, contract, contract_path = _setup(tmp_path)
    receipt = run_untouched_external_refit_positive_contract(contract_path)
    assert receipt["receipt_type"] == "odsp_untouched_external_refit_positive_validation_endpoint"
    assert receipt["freeze_manifest_sha256"] == _sha256(manifest)
    assert receipt["data_sha256"] == _sha256(data)
    assert receipt["refit_count"] == 8
    assert receipt["external_heldout_row_count"] == 16
    assert receipt["result"]["refit_consensus_certified_transfer_ceiling"] == "fine"
    assert receipt["boundaries"]["untouched_external_validation_contract_satisfied"] is True
    assert receipt["boundaries"]["historical_no_prior_outcome_access_independently_proven_by_odsp"] is False


def test_bad_freeze_manifest_hash_fails(tmp_path: Path):
    _, _, contract, contract_path = _setup(tmp_path)
    contract["external_validation"]["freeze_manifest"]["sha256"] = "0" * 64
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(ValueError, match="freeze manifest SHA256"):
        run_untouched_external_refit_positive_contract(contract_path)


def test_freeze_must_predate_first_external_outcome_access(tmp_path: Path):
    _, _, contract, _ = _setup(tmp_path)
    contract["external_validation"]["freeze_manifest"]["frozen_at_utc"] = "2026-09-16T00:00:00Z"
    with pytest.raises(ValueError, match="predate"):
        validate_untouched_external_refit_positive_contract(contract)


def test_any_external_outcome_development_use_fails_closed(tmp_path: Path):
    _, _, contract, _ = _setup(tmp_path)
    contract["external_validation"]["external_outcomes_used_for_any_development_decision"] = True
    with pytest.raises(ValueError, match="must be false"):
        validate_untouched_external_refit_positive_contract(contract)


def test_one_refit_fine_failure_stops_external_consensus_at_coarse(tmp_path: Path):
    rows = _rows()
    for row in rows:
        if row["refit_id"] == "r07":
            row["score_fine"] = 0.2
    _, _, _, contract_path = _setup(tmp_path, rows)
    receipt = run_untouched_external_refit_positive_contract(contract_path)
    assert receipt["result"]["reference_refit_certified_transfer_ceiling"] == "fine"
    assert receipt["result"]["refit_consensus_certified_transfer_ceiling"] == "coarse"
    assert receipt["result"]["reference_refit_can_override_consensus_failure"] is False


def test_missing_external_row_in_one_refit_fails_alignment(tmp_path: Path):
    rows = [
        row
        for row in _rows()
        if not (row["refit_id"] == "r07" and row["row_id"] == "g1-b7")
    ]
    _, _, _, contract_path = _setup(tmp_path, rows)
    with pytest.raises(ValueError, match="canonical external row set"):
        run_untouched_external_refit_positive_contract(contract_path)
