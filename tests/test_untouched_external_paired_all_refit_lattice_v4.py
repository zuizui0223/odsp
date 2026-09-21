from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import pytest

from odsp.external_paired_lattice_freeze_manifest import (
    create_paired_external_lattice_freeze_manifest,
    validate_paired_external_lattice_freeze_plan,
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


def _subsets(names: tuple[str, ...]):
    for size in range(len(names) + 1):
        yield from itertools.combinations(names, size)


def _node_column(subset: tuple[str, ...]) -> str:
    return "score_base" if not subset else "score_" + "_".join(value.lower() for value in subset)


def _plan(names: tuple[str, ...] = ("A", "B")) -> dict[str, object]:
    return {
        "schema_version": 1,
        "upstream_model_set_id": "paired-lattice-model-set-v1",
        "external_dataset_id": "paired-lattice-external-v1",
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
            {"name": name, "variables": [name.lower()]}
            for name in names
        ],
        "nodes": [
            {"blocks": list(subset), "score_column": _node_column(subset)}
            for subset in _subsets(names)
        ],
        "certification": {
            "alternative": "greater",
            "familywise_lower_confidence_level": 0.95,
            "bootstrap_draws": 500,
            "seed": 20260916,
            "minimum_refits": 2,
            "minimum_shared_blocks": 8,
            "gain_tolerance": 0.0,
        },
    }


def _roster_rows(group_count: int = 3, block_count: int = 8) -> list[dict[str, object]]:
    return [
        {
            "row_id": f"g{group_index}-b{block_index}",
            "group": f"g{group_index}",
            "block": f"b{block_index}",
            "weight": 1.0,
        }
        for group_index in range(group_count)
        for block_index in range(block_count)
    ]


def _node_values(names: tuple[str, ...], *, refit_id: str, crossed_paths: bool = False):
    if names == ("A", "B") and crossed_paths:
        if refit_id == "r00":
            return {(): 0.0, ("A",): 0.4, ("B",): -0.1, ("A", "B"): 0.8}
        return {(): 0.0, ("A",): -0.1, ("B",): 0.4, ("A", "B"): 0.8}
    return {subset: 0.3 * len(subset) for subset in _subsets(names)}


def _long_rows(
    names: tuple[str, ...] = ("A", "B"),
    *,
    crossed_paths: bool = False,
    support_mismatch: bool = False,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for refit_id in ("r00", "r01"):
        values = _node_values(names, refit_id=refit_id, crossed_paths=crossed_paths)
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
                for subset in _subsets(names):
                    row[_node_column(subset)] = values[subset]
                rows.append(row)
    return rows


def _external_contract(manifest: Path, names: tuple[str, ...] = ("A", "B")) -> dict[str, object]:
    frozen = json.loads(manifest.read_text(encoding="utf-8"))
    plan = _plan(names)
    return {
        "schema_version": 1,
        "endpoint_id": "paired-lattice-external-v4",
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
                "path": "freeze-lattice.json",
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


def _setup(
    tmp_path: Path,
    names: tuple[str, ...] = ("A", "B"),
    *,
    crossed_paths: bool = False,
    support_mismatch: bool = False,
):
    roster = tmp_path / "roster.csv"
    _write_csv(roster, _roster_rows())
    plan = tmp_path / "freeze-plan.json"
    plan.write_text(json.dumps(_plan(names)), encoding="utf-8")
    manifest = tmp_path / "freeze-lattice.json"
    create_paired_external_lattice_freeze_manifest(plan, manifest)
    scores = tmp_path / "scores.csv"
    _write_csv(
        scores,
        _long_rows(
            names,
            crossed_paths=crossed_paths,
            support_mismatch=support_mismatch,
        ),
    )
    endpoint = tmp_path / "endpoint.json"
    endpoint.write_text(json.dumps(_external_contract(manifest, names)), encoding="utf-8")
    return manifest, scores, endpoint


def test_two_block_freeze_to_external_lattice_is_universal(tmp_path: Path):
    manifest, _, endpoint = _setup(tmp_path)
    receipt = run_untouched_external_paired_all_refit_lattice_contract_v4(endpoint)
    assert receipt["receipt_type"] == (
        "odsp_untouched_external_paired_all_refit_positive_lattice_endpoint_v4"
    )
    assert receipt["freeze_manifest_sha256"] == _sha256(manifest)
    assert receipt["information_block_count"] == 2
    assert receipt["edge_count"] == 4
    assert receipt["result"]["all_refit_robust_full_transfer_path_count"] == 2
    assert receipt["result"]["all_refit_certified_path_status"] == "universal_full_transfer"
    assert receipt["boundaries"]["complete_lattice_node_table_frozen_before_outcome_access"] is True
    assert receipt["boundaries"]["paired_row_metadata_frozen_before_outcome_access"] is True
    assert receipt["boundaries"]["runtime_pairing_metadata_matches_frozen_manifest"] is True
    assert receipt["boundaries"]["different_refit_paths_can_be_combined"] is False


def test_crossed_refit_paths_do_not_create_external_global_path(tmp_path: Path):
    _, _, endpoint = _setup(tmp_path, crossed_paths=True)
    receipt = run_untouched_external_paired_all_refit_lattice_contract_v4(endpoint)
    assert receipt["result"]["refit_robust_full_transfer_path_counts"] == [1, 1]
    assert receipt["result"]["all_refit_robust_full_transfer_path_count"] == 0
    assert receipt["result"]["all_refit_certified_path_status"] == "no_full_transfer"
    assert receipt["result"]["different_refit_paths_can_be_combined"] is False


def test_three_block_external_lattice_uses_calibrated_12_edge_family(tmp_path: Path):
    _, _, endpoint = _setup(tmp_path, ("A", "B", "C"))
    receipt = run_untouched_external_paired_all_refit_lattice_contract_v4(endpoint)
    assert receipt["information_block_count"] == 3
    assert receipt["edge_count"] == 12
    assert receipt["result"]["total_admissible_path_count"] == 6
    assert receipt["result"]["all_refit_robust_full_transfer_path_count"] == 6
    assert receipt["result"]["all_refit_certified_path_status"] == "universal_full_transfer"


def test_shared_block_support_mismatch_hard_stops_v4(tmp_path: Path):
    _, _, endpoint = _setup(tmp_path, support_mismatch=True)
    with pytest.raises(ValueError, match="paired_row_metadata_sha256|identical positive-mass block support"):
        run_untouched_external_paired_all_refit_lattice_contract_v4(endpoint)


def test_node_semantic_tamper_fails_even_when_manifest_hash_is_updated(tmp_path: Path):
    manifest, _, endpoint = _setup(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["nodes"][1]["score_column"] = "score_b"
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    contract = json.loads(endpoint.read_text(encoding="utf-8"))
    contract["external_validation"]["freeze_manifest"]["sha256"] = _sha256(manifest)
    endpoint.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(ValueError, match="semantic mismatch for nodes"):
        run_untouched_external_paired_all_refit_lattice_contract_v4(endpoint)


def test_missing_node_fails_freeze_plan_before_outcome_access():
    plan = _plan()
    plan["nodes"] = plan["nodes"][:-1]
    with pytest.raises(ValueError, match="complete lattice subset table"):
        validate_paired_external_lattice_freeze_plan(plan)


def test_duplicate_node_score_column_fails_freeze_plan():
    plan = _plan()
    plan["nodes"][1]["score_column"] = plan["nodes"][0]["score_column"]
    with pytest.raises(ValueError, match="score_column values must be unique"):
        validate_paired_external_lattice_freeze_plan(plan)


def test_four_block_lattice_is_rejected_during_freeze():
    with pytest.raises(ValueError, match="qualified only for 2 or 3 information blocks"):
        validate_paired_external_lattice_freeze_plan(_plan(("A", "B", "C", "D")))


def test_lattice_freeze_roster_rejects_outcome_columns(tmp_path: Path):
    roster = tmp_path / "roster.csv"
    row = _roster_rows(group_count=1, block_count=1)[0]
    row["outcome"] = 1
    _write_csv(roster, [row])
    plan_payload = _plan()
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(plan_payload), encoding="utf-8")
    with pytest.raises(ValueError, match="paired roster must contain only"):
        create_paired_external_lattice_freeze_manifest(plan, tmp_path / "freeze.json")


def test_lattice_confirmatory_route_tamper_fails_even_with_updated_manifest_hash(
    tmp_path: Path,
):
    manifest, _, endpoint = _setup(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["confirmatory_route"]["canonical_surface"] = (
        "odsp.untouched_external_refit_shared_block_positive_contract_v3."
        "run_untouched_external_refit_shared_block_positive_contract_v3"
    )
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    contract = json.loads(endpoint.read_text(encoding="utf-8"))
    contract["external_validation"]["freeze_manifest"]["sha256"] = _sha256(manifest)
    endpoint.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(ValueError, match="confirmatory_route"):
        run_untouched_external_paired_all_refit_lattice_contract_v4(endpoint)
