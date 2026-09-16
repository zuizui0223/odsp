from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from odsp.external_paired_freeze_manifest import create_paired_external_freeze_manifest
from odsp.untouched_external_refit_positive_contract_v2 import (
    run_untouched_external_refit_positive_contract_v2,
)
from odsp.untouched_external_refit_shared_block_positive_contract_v3 import (
    run_untouched_external_refit_shared_block_positive_contract_v3,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _row_ids(group_count: int = 3, block_count: int = 8) -> list[str]:
    return [
        f"g{group_index}-b{block_index}"
        for group_index in range(group_count)
        for block_index in range(block_count)
    ]


def _long_rows(
    *,
    refit_ids: tuple[str, ...] = ("r00", "r01", "r02"),
    group_count: int = 3,
    block_count: int = 8,
    failed_fine_refit: str | None = None,
    support_mismatch: bool = False,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for refit_id in refit_ids:
        for group_index in range(group_count):
            for block_index in range(block_count):
                shared_block = f"b{block_index}"
                if support_mismatch and group_index == group_count - 1 and block_index == block_count - 1:
                    shared_block = "b-mismatch"
                coarse = 0.4
                fine = 0.7 if refit_id != failed_fine_refit else 0.2
                rows.append(
                    {
                        "row_id": f"g{group_index}-b{block_index}",
                        "refit_id": refit_id,
                        "group": f"g{group_index}",
                        "block": shared_block,
                        "weight": 1.0,
                        "score_pooled": 0.0,
                        "score_coarse": coarse,
                        "score_fine": fine,
                    }
                )
    return rows


def _freeze_plan() -> dict[str, object]:
    return {
        "schema_version": 1,
        "upstream_model_set_id": "paired-model-set-v1",
        "external_dataset_id": "paired-external-v1",
        "roster": {"path": "roster.csv", "format": "csv", "row_id_column": "row_id"},
        "refit_ids": ["r00", "r01", "r02"],
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
            "minimum_refits": 2,
            "minimum_blocks_per_group": 8,
            "gain_tolerance": 0.0,
        },
    }


def _external_contract(manifest: Path) -> dict[str, object]:
    frozen = json.loads(manifest.read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "endpoint_id": "paired-external-test-v3",
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
                "path": "freeze-paired.json",
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
            "minimum_refits": 2,
            "minimum_blocks_per_group": 8,
            "gain_tolerance": 0.0,
            "reference_refit_id": "r00",
        },
    }


def _setup(
    tmp_path: Path,
    *,
    failed_fine_refit: str | None = None,
    support_mismatch: bool = False,
):
    roster = tmp_path / "roster.csv"
    _write_csv(roster, [{"row_id": row_id} for row_id in _row_ids()])
    plan = tmp_path / "freeze-plan.json"
    plan.write_text(json.dumps(_freeze_plan()), encoding="utf-8")
    manifest = tmp_path / "freeze-paired.json"
    create_paired_external_freeze_manifest(plan, manifest)
    scores = tmp_path / "scores.csv"
    _write_csv(
        scores,
        _long_rows(
            failed_fine_refit=failed_fine_refit,
            support_mismatch=support_mismatch,
        ),
    )
    contract = tmp_path / "endpoint.json"
    contract.write_text(json.dumps(_external_contract(manifest)), encoding="utf-8")
    return manifest, scores, contract


def test_paired_external_v3_reaches_full_all_refit_ceiling(tmp_path: Path):
    manifest, _, contract = _setup(tmp_path)
    receipt = run_untouched_external_refit_shared_block_positive_contract_v3(contract)
    assert receipt["receipt_type"] == (
        "odsp_untouched_external_refit_shared_block_positive_validation_endpoint_v3"
    )
    assert receipt["freeze_manifest_sha256"] == _sha256(manifest)
    assert receipt["result"]["design"] == "shared_blocks"
    assert receipt["result"]["all_refit_certified_transfer_ceiling"] == "fine"
    assert receipt["scientific_roles"]["validation_design"] == "paired_shared_blocks"
    assert receipt["boundaries"]["validation_group_independence_assumed"] is False
    assert receipt["boundaries"]["exact_positive_mass_shared_block_support_required"] is True


def test_one_failed_refit_stops_paired_external_ceiling(tmp_path: Path):
    _, _, contract = _setup(tmp_path, failed_fine_refit="r02")
    receipt = run_untouched_external_refit_shared_block_positive_contract_v3(contract)
    assert receipt["result"]["all_refit_certified_transfer_ceiling"] == "coarse"
    assert receipt["result"]["step_robustness"][1]["category"] == "not_robust_across_refits"
    assert receipt["result"]["reference_refit_can_override_failure"] is False


def test_shared_block_support_mismatch_hard_stops_external_endpoint(tmp_path: Path):
    _, _, contract = _setup(tmp_path, support_mismatch=True)
    with pytest.raises(ValueError, match="identical positive-mass block support"):
        run_untouched_external_refit_shared_block_positive_contract_v3(contract)


def test_paired_freeze_manifest_cannot_be_used_by_independent_external_v2(tmp_path: Path):
    _, _, contract = _setup(tmp_path)
    with pytest.raises(ValueError, match="schema_version must be 1"):
        run_untouched_external_refit_positive_contract_v2(contract)


def test_validation_design_semantic_tamper_fails_even_with_updated_hash(tmp_path: Path):
    manifest, _, contract = _setup(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["validation_design"]["kind"] = "independent_groups"
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    endpoint = json.loads(contract.read_text(encoding="utf-8"))
    endpoint["external_validation"]["freeze_manifest"]["sha256"] = _sha256(manifest)
    contract.write_text(json.dumps(endpoint), encoding="utf-8")
    with pytest.raises(ValueError, match="validation_design"):
        run_untouched_external_refit_shared_block_positive_contract_v3(contract)


def test_paired_freeze_generator_rejects_outcome_columns(tmp_path: Path):
    roster = tmp_path / "roster.csv"
    _write_csv(roster, [{"row_id": "r1", "outcome": 1}])
    plan_payload = _freeze_plan()
    plan_payload["roster"]["path"] = "roster.csv"
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(plan_payload), encoding="utf-8")
    with pytest.raises(ValueError, match="only the row_id column"):
        create_paired_external_freeze_manifest(plan, tmp_path / "freeze.json")
