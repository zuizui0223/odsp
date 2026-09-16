from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from odsp.cli import main
from odsp.external_freeze_manifest import (
    create_external_freeze_manifest,
    validate_external_freeze_plan,
)
from odsp.untouched_external_refit_positive_contract_v2 import (
    verify_freeze_manifest_semantic_lock,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _roster(tmp_path: Path, *, extra_column: bool = False) -> Path:
    path = tmp_path / "roster.csv"
    fieldnames = ["row_id"] + (["outcome"] if extra_column else [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for group_index in range(2):
            for block_index in range(8):
                row = {"row_id": f"g{group_index}-b{block_index}"}
                if extra_column:
                    row["outcome"] = "sealed-value"
                writer.writerow(row)
    return path


def _plan() -> dict[str, object]:
    return {
        "schema_version": 1,
        "upstream_model_set_id": "models-v17",
        "external_dataset_id": "external-cohort-A",
        "roster": {"path": "roster.csv", "format": "csv", "row_id_column": "row_id"},
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


def _write_plan(tmp_path: Path, plan: dict[str, object] | None = None) -> Path:
    path = tmp_path / "freeze-plan.json"
    path.write_text(json.dumps(_plan() if plan is None else plan), encoding="utf-8")
    return path


def _write_scores(tmp_path: Path) -> Path:
    path = tmp_path / "scores.csv"
    fieldnames = [
        "row_id",
        "refit_id",
        "group",
        "block",
        "weight",
        "score_pooled",
        "score_coarse",
        "score_fine",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for refit_index in range(8):
            for group_index in range(2):
                for block_index in range(8):
                    writer.writerow(
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
    return path


def _external_contract(manifest: dict[str, object], manifest_path: Path) -> dict[str, object]:
    return {
        "schema_version": 1,
        "endpoint_id": "generated-freeze-roundtrip-v1",
        "data": {"path": "scores.csv", "format": "csv"},
        "columns": {
            "row_id": "row_id",
            "refit_id": "refit_id",
            "group": "group",
            "block": "block",
            "weight": "weight",
        },
        "score": manifest["score"],
        "external_validation": {
            "dataset_role": "untouched_external_validation",
            "freeze_manifest": {
                "path": manifest_path.name,
                "sha256": _sha256(manifest_path),
                "frozen_at_utc": manifest["frozen_at_utc"],
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
        "levels": [
            {
                "name": level["name"],
                "information": level["information"],
                "score_column": f"score_{level['name']}",
            }
            for level in manifest["levels"]
        ],
        "certification": {
            **manifest["certification"],
            "reference_refit_id": manifest["reference_refit_id"],
        },
    }


def test_generator_creates_non_backdatable_semantically_valid_manifest(tmp_path: Path):
    roster = _roster(tmp_path)
    plan_path = _write_plan(tmp_path)
    manifest_path = tmp_path / "freeze.json"
    receipt = create_external_freeze_manifest(plan_path, manifest_path)

    assert roster.is_file()
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["manifest_type"] == "odsp_pre_external_outcome_freeze_v1"
    assert manifest["frozen_at_utc"].endswith("Z")
    assert manifest["external_dataset_id"] == "external-cohort-A"
    assert manifest["refit_ids"] == [f"r{index:02d}" for index in range(8)]
    assert receipt["manifest_sha256"] == _sha256(manifest_path)
    assert receipt["external_row_count"] == 16
    assert receipt["boundaries"]["caller_supplied_freeze_timestamp_allowed"] is False
    assert receipt["boundaries"]["manifest_overwrite_allowed"] is False
    assert receipt["boundaries"]["trusted_timestamp_authority_used"] is False

    _write_scores(tmp_path)
    endpoint_path = tmp_path / "endpoint.json"
    endpoint_path.write_text(
        json.dumps(_external_contract(manifest, manifest_path)), encoding="utf-8"
    )
    lock = verify_freeze_manifest_semantic_lock(endpoint_path)
    assert lock["freeze_manifest_semantic_lock_verified"] is True
    assert lock["external_dataset_id"] == "external-cohort-A"


def test_freeze_plan_has_no_caller_timestamp_field():
    plan = _plan()
    plan["frozen_at_utc"] = "2000-01-01T00:00:00Z"
    with pytest.raises(ValueError, match="unknown fields"):
        validate_external_freeze_plan(plan)


def test_roster_with_outcome_or_other_columns_is_rejected(tmp_path: Path):
    _roster(tmp_path, extra_column=True)
    plan_path = _write_plan(tmp_path)
    with pytest.raises(ValueError, match="must contain only the row_id column"):
        create_external_freeze_manifest(plan_path, tmp_path / "freeze.json")


def test_duplicate_roster_row_ids_are_rejected(tmp_path: Path):
    path = tmp_path / "roster.csv"
    path.write_text("row_id\na\na\n", encoding="utf-8")
    plan_path = _write_plan(tmp_path)
    with pytest.raises(ValueError, match="must be unique"):
        create_external_freeze_manifest(plan_path, tmp_path / "freeze.json")


def test_existing_manifest_is_never_overwritten(tmp_path: Path):
    _roster(tmp_path)
    plan_path = _write_plan(tmp_path)
    manifest_path = tmp_path / "freeze.json"
    manifest_path.write_text("existing\n", encoding="utf-8")
    before = manifest_path.read_bytes()
    with pytest.raises(FileExistsError, match="will not be overwritten"):
        create_external_freeze_manifest(plan_path, manifest_path)
    assert manifest_path.read_bytes() == before


def test_refit_plan_must_satisfy_minimum_refit_count():
    plan = _plan()
    plan["refit_ids"] = ["r00", "r01"]
    plan["reference_refit_id"] = "r00"
    with pytest.raises(ValueError, match="do not satisfy"):
        validate_external_freeze_plan(plan)


def test_cli_generates_manifest_and_receipt(tmp_path: Path, capsys):
    _roster(tmp_path)
    plan_path = _write_plan(tmp_path)
    manifest_path = tmp_path / "freeze.json"
    code = main(
        [
            "freeze-refits-external",
            "--plan",
            str(plan_path),
            "--manifest-out",
            str(manifest_path),
        ]
    )
    assert code == 0
    assert manifest_path.is_file()
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["receipt_type"] == "odsp_pre_external_outcome_freeze_receipt_v1"
    assert receipt["manifest_sha256"] == _sha256(manifest_path)
