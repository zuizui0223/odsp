from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from odsp.cli import main
from odsp.untouched_external_refit_positive_contract_v2 import (
    run_untouched_external_refit_positive_contract_v2,
    verify_freeze_manifest_semantic_lock,
)


def _rows(refit_count: int = 8, group_count: int = 2, blocks_per_group: int = 8):
    rows: list[dict[str, object]] = []
    for refit_index in range(refit_count):
        for group_index in range(group_count):
            for block_index in range(blocks_per_group):
                rows.append(
                    {
                        "row_id": f"g{group_index}-b{block_index}",
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


def _roster_sha(rows: list[dict[str, object]]) -> str:
    row_ids = sorted({str(row["row_id"]) for row in rows})
    payload = "\n".join(row_ids) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _manifest(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "manifest_type": "odsp_pre_external_outcome_freeze_v1",
        "frozen_at_utc": "2026-09-01T00:00:00Z",
        "upstream_model_set_id": "models-v17",
        "external_dataset_id": "external-cohort-A",
        "external_row_ids_sha256": _roster_sha(rows),
        "refit_ids": [f"r{index:02d}" for index in range(8)],
        "reference_refit_id": "r00",
        "score": {
            "kind": "log",
            "name": "log",
            "orientation": "higher_is_better",
            "common_scoring_rule": True,
            "common_reference_measure": True,
        },
        "levels": [
            {"name": "pooled", "information": []},
            {"name": "coarse", "information": ["coarse"]},
            {"name": "fine", "information": ["coarse", "fine"]},
        ],
        "certification": {
            "alternative": "greater",
            "familywise_lower_confidence_level": 0.95,
            "bootstrap_draws": 500,
            "seed": 20260916,
            "minimum_refits": 8,
            "minimum_blocks_per_group": 8,
            "gain_tolerance": 0.0,
        },
    }


def _contract(manifest_sha: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "endpoint_id": "external-semantic-lock-test-v1",
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


def _setup(tmp_path: Path):
    rows = _rows()
    data = tmp_path / "scores.csv"
    _write_csv(data, rows)
    manifest_path = tmp_path / "freeze.json"
    manifest = _manifest(rows)
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    contract_path = tmp_path / "endpoint.json"
    contract = _contract(_sha256(manifest_path))
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    return rows, data, manifest, manifest_path, contract, contract_path


def _rewrite_manifest(manifest_path: Path, manifest: dict[str, object], contract_path: Path, contract: dict[str, object]):
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    contract["external_validation"]["freeze_manifest"]["sha256"] = _sha256(manifest_path)
    contract_path.write_text(json.dumps(contract), encoding="utf-8")


def test_semantic_lock_verifies_exact_runtime_analysis(tmp_path: Path):
    _, _, _, _, _, contract_path = _setup(tmp_path)
    lock = verify_freeze_manifest_semantic_lock(contract_path)
    assert lock["freeze_manifest_semantic_lock_verified"] is True
    assert lock["upstream_model_set_id"] == "models-v17"
    assert lock["external_dataset_id"] == "external-cohort-A"
    assert lock["refit_ids"] == [f"r{index:02d}" for index in range(8)]

    receipt = run_untouched_external_refit_positive_contract_v2(contract_path)
    assert receipt["receipt_type"] == "odsp_untouched_external_refit_positive_validation_endpoint_v2"
    assert receipt["boundaries"]["freeze_manifest_semantics_verified"] is True
    assert receipt["boundaries"]["external_row_roster_locked_before_outcome_access"] is True
    assert receipt["boundaries"]["runtime_analysis_matches_frozen_manifest"] is True
    assert receipt["boundaries"]["confirmatory_route_verified"] is True
    assert receipt["confirmatory_route"]["verified"] is True
    assert receipt["confirmatory_route"]["role"] == "primary_confirmatory"
    assert receipt["confirmatory_route"]["qualification_evidence"]
    assert receipt["result"]["refit_consensus_certified_transfer_ceiling"] == "fine"


def test_frozen_refit_ids_must_match_runtime_table(tmp_path: Path):
    _, _, manifest, manifest_path, contract, contract_path = _setup(tmp_path)
    manifest["refit_ids"] = [f"r{index:02d}" for index in range(7)] + ["r99"]
    _rewrite_manifest(manifest_path, manifest, contract_path, contract)
    with pytest.raises(ValueError, match="semantic mismatch for refit_ids"):
        verify_freeze_manifest_semantic_lock(contract_path)


def test_frozen_row_roster_must_match_external_rows(tmp_path: Path):
    _, _, manifest, manifest_path, contract, contract_path = _setup(tmp_path)
    manifest["external_row_ids_sha256"] = "0" * 64
    _rewrite_manifest(manifest_path, manifest, contract_path, contract)
    with pytest.raises(ValueError, match="external_row_ids_sha256"):
        verify_freeze_manifest_semantic_lock(contract_path)


def test_frozen_filtration_must_match_runtime_levels(tmp_path: Path):
    _, _, manifest, manifest_path, contract, contract_path = _setup(tmp_path)
    manifest["levels"][2]["information"] = ["coarse", "post_outcome_choice"]
    _rewrite_manifest(manifest_path, manifest, contract_path, contract)
    with pytest.raises(ValueError, match="semantic mismatch for levels"):
        verify_freeze_manifest_semantic_lock(contract_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("seed", 999),
        ("gain_tolerance", 0.05),
        ("bootstrap_draws", 1000),
        ("minimum_refits", 9),
    ],
)
def test_frozen_inferential_settings_must_match_runtime(
    tmp_path: Path, field: str, value: object
):
    _, _, manifest, manifest_path, contract, contract_path = _setup(tmp_path)
    manifest["certification"][field] = value
    _rewrite_manifest(manifest_path, manifest, contract_path, contract)
    with pytest.raises(ValueError, match="semantic mismatch for certification"):
        verify_freeze_manifest_semantic_lock(contract_path)


def test_manifest_internal_freeze_time_must_match_outer_contract(tmp_path: Path):
    _, _, manifest, manifest_path, contract, contract_path = _setup(tmp_path)
    manifest["frozen_at_utc"] = "2026-08-31T23:59:59Z"
    _rewrite_manifest(manifest_path, manifest, contract_path, contract)
    with pytest.raises(ValueError, match="semantic mismatch for frozen_at_utc"):
        verify_freeze_manifest_semantic_lock(contract_path)


def test_cli_uses_semantic_lock_not_legacy_hash_only_route(tmp_path: Path, capsys):
    _, _, manifest, manifest_path, contract, contract_path = _setup(tmp_path)
    manifest["certification"]["seed"] = 7
    _rewrite_manifest(manifest_path, manifest, contract_path, contract)
    code = main(["transfer-refits-external", "--contract", str(contract_path)])
    assert code == 2
    assert "semantic mismatch for certification" in capsys.readouterr().err


def test_external_v2_rejects_unqualified_three_contrast_family(tmp_path: Path):
    rows = _rows()
    for row in rows:
        row["score_middle"] = 0.55
    data = tmp_path / "scores.csv"
    _write_csv(data, rows)

    manifest = _manifest(rows)
    manifest["levels"] = [
        {"name": "pooled", "information": []},
        {"name": "coarse", "information": ["coarse"]},
        {"name": "middle", "information": ["coarse", "middle"]},
        {"name": "fine", "information": ["coarse", "middle", "fine"]},
    ]
    manifest_path = tmp_path / "freeze.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")

    contract = _contract(_sha256(manifest_path))
    contract["levels"] = [
        {"name": "pooled", "information": [], "score_column": "score_pooled"},
        {"name": "coarse", "information": ["coarse"], "score_column": "score_coarse"},
        {"name": "middle", "information": ["coarse", "middle"], "score_column": "score_middle"},
        {"name": "fine", "information": ["coarse", "middle", "fine"], "score_column": "score_fine"},
    ]
    contract_path = tmp_path / "endpoint.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    with pytest.raises(ValueError, match="qualified primary confirmatory route|unqualified"):
        run_untouched_external_refit_positive_contract_v2(contract_path)
