from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import pytest

from odsp.external_paired_lattice_freeze_manifest import (
    create_paired_external_lattice_freeze_manifest,
)
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


def _row_ids(group_count: int = 3, block_count: int = 8) -> list[str]:
    return [
        f"g{group_index}-b{block_index}"
        for group_index in range(group_count)
        for block_index in range(block_count)
    ]


def _blocks(names: tuple[str, ...]) -> list[dict[str, object]]:
    return [{"name": name, "variables": [name.lower()]} for name in names]


def _subsets(names: tuple[str, ...]):
    for size in range(len(names) + 1):
        yield from itertools.combinations(names, size)


def _nodes(names: tuple[str, ...]) -> list[dict[str, object]]:
    rows = []
    for subset in _subsets(names):
        suffix = "base" if not subset else "_".join(value.lower() for value in subset)
        rows.append({"blocks": list(subset), "score_column": f"score_{suffix}"})
    return rows


def _score_contract() -> dict[str, object]:
    return {
        "kind": "log",
        "name": "log",
        "orientation": "higher_is_better",
        "common_scoring_rule": True,
        "common_reference_measure": True,
    }


def _certification() -> dict[str, object]:
    return {
        "alternative": "greater",
        "familywise_lower_confidence_level": 0.95,
        "bootstrap_draws": 500,
        "seed": 20260916,
        "minimum_refits": 2,
        "minimum_shared_blocks": 8,
        "gain_tolerance": 0.0,
    }


def _freeze_plan(names: tuple[str, ...] = ("A", "B")) -> dict[str, object]:
    return {
        "schema_version": 1,
        "upstream_model_set_id": "model-set-v4",
        "external_dataset_id": "external-dataset-v4",
        "roster": {"path": "roster.csv", "format": "csv", "row_id_column": "row_id"},
        "refit_ids": ["r00", "r01"],
        "score": _score_contract(),
        "base_information": [],
        "information_blocks": _blocks(names),
        "nodes": _nodes(names),
        "certification": _certification(),
    }


def _external_validation(manifest: Path) -> dict[str, object]:
    frozen = json.loads(manifest.read_text(encoding="utf-8"))
    return {
        "dataset_role": "untouched_external_validation",
        "freeze_manifest": {
            "path": manifest.name,
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
    }


def _contract(manifest: Path, names: tuple[str, ...] = ("A", "B")) -> dict[str, object]:
    return {
        "schema_version": 1,
        "endpoint_id": "paired-lattice-v4-test",
        "upstream_model_set_id": "model-set-v4",
        "external_dataset_id": "external-dataset-v4",
        "data": {"path": "scores.csv", "format": "csv"},
        "columns": {
            "row_id": "row_id",
            "refit_id": "refit_id",
            "group": "group",
            "block": "block",
            "weight": "weight",
        },
        "score": _score_contract(),
        "external_validation": _external_validation(manifest),
        "base_information": [],
        "information_blocks": _blocks(names),
        "nodes": _nodes(names),
        "certification": _certification(),
    }


def _long_rows(
    values_by_refit: dict[str, dict[tuple[str, ...], float]],
    names: tuple[str, ...] = ("A", "B"),
    *,
    support_mismatch: bool = False,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    nodes = _nodes(names)
    for refit_id, mapping in values_by_refit.items():
        for group_index in range(3):
            for block_index in range(8):
                shared_block = f"b{block_index}"
                if support_mismatch and group_index == 2 and block_index == 7:
                    shared_block = "b-mismatch"
                row: dict[str, object] = {
                    "row_id": f"g{group_index}-b{block_index}",
                    "refit_id": refit_id,
                    "group": f"g{group_index}",
                    "block": shared_block,
                    "weight": 1.0,
                }
                for node in nodes:
                    subset = tuple(node["blocks"])
                    row[str(node["score_column"])] = mapping[subset]
                rows.append(row)
    return rows


def _setup(
    tmp_path: Path,
    values_by_refit: dict[str, dict[tuple[str, ...], float]],
    names: tuple[str, ...] = ("A", "B"),
    *,
    support_mismatch: bool = False,
):
    roster = tmp_path / "roster.csv"
    _write_csv(roster, [{"row_id": row_id} for row_id in _row_ids()])
    plan = tmp_path / "freeze-plan.json"
    plan.write_text(json.dumps(_freeze_plan(names)), encoding="utf-8")
    manifest = tmp_path / "freeze-lattice.json"
    create_paired_external_lattice_freeze_manifest(plan, manifest)
    scores = tmp_path / "scores.csv"
    _write_csv(scores, _long_rows(values_by_refit, names, support_mismatch=support_mismatch))
    contract = tmp_path / "endpoint.json"
    contract.write_text(json.dumps(_contract(manifest, names)), encoding="utf-8")
    return manifest, scores, contract


def test_runtime_model_set_and_dataset_ids_must_match_frozen_manifest(tmp_path: Path):
    mapping = {(): 0.0, ("A",): 0.4, ("B",): 0.4, ("A", "B"): 0.8}
    _, _, contract_path = _setup(tmp_path, {"r00": mapping, "r01": mapping})
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["upstream_model_set_id"] = "post-outcome-model-switch"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(ValueError, match="upstream_model_set_id"):
        run_untouched_external_paired_all_refit_lattice_contract_v4(contract_path)


def test_two_block_external_lattice_reaches_universal_all_refit_path(tmp_path: Path):
    mapping = {(): 0.0, ("A",): 0.4, ("B",): 0.4, ("A", "B"): 0.8}
    manifest, _, contract = _setup(tmp_path, {"r00": mapping, "r01": mapping})
    receipt = run_untouched_external_paired_all_refit_lattice_contract_v4(contract)
    assert receipt["receipt_type"] == "odsp_untouched_external_paired_all_refit_positive_lattice_endpoint_v4"
    assert receipt["freeze_manifest_sha256"] == _sha256(manifest)
    assert receipt["edge_count"] == 4
    assert receipt["result"]["all_refit_robust_full_transfer_path_count"] == 2
    assert receipt["result"]["all_refit_certified_path_status"] == "universal_full_transfer"
    assert receipt["boundaries"]["different_refit_paths_can_be_combined"] is False


def test_different_refit_paths_do_not_form_external_global_path(tmp_path: Path):
    r0 = {(): 0.0, ("A",): 0.4, ("B",): -0.1, ("A", "B"): 0.8}
    r1 = {(): 0.0, ("A",): -0.1, ("B",): 0.4, ("A", "B"): 0.8}
    _, _, contract = _setup(tmp_path, {"r00": r0, "r01": r1})
    receipt = run_untouched_external_paired_all_refit_lattice_contract_v4(contract)
    assert receipt["result"]["refit_robust_full_transfer_path_counts"] == [1, 1]
    assert receipt["result"]["all_refit_robust_full_transfer_path_count"] == 0
    assert receipt["result"]["all_refit_certified_path_status"] == "no_full_transfer"


def test_shared_block_support_mismatch_hard_stops_external_lattice(tmp_path: Path):
    mapping = {(): 0.0, ("A",): 0.4, ("B",): 0.4, ("A", "B"): 0.8}
    _, _, contract = _setup(
        tmp_path,
        {"r00": mapping, "r01": mapping},
        support_mismatch=True,
    )
    with pytest.raises(ValueError, match="identical positive-mass block support"):
        run_untouched_external_paired_all_refit_lattice_contract_v4(contract)


def test_node_semantic_tamper_fails_even_when_manifest_hash_is_updated(tmp_path: Path):
    mapping = {(): 0.0, ("A",): 0.4, ("B",): 0.4, ("A", "B"): 0.8}
    manifest, _, contract_path = _setup(tmp_path, {"r00": mapping, "r01": mapping})
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["nodes"][1]["score_column"], contract["nodes"][2]["score_column"] = (
        contract["nodes"][2]["score_column"],
        contract["nodes"][1]["score_column"],
    )
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(ValueError, match="nodes"):
        run_untouched_external_paired_all_refit_lattice_contract_v4(contract_path)


def test_freeze_rejects_four_block_32_edge_lattice(tmp_path: Path):
    roster = tmp_path / "roster.csv"
    _write_csv(roster, [{"row_id": row_id} for row_id in _row_ids()])
    plan = _freeze_plan(("A", "B", "C", "D"))
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="qualified only for 2 or 3 information blocks"):
        create_paired_external_lattice_freeze_manifest(plan_path, tmp_path / "freeze.json")
