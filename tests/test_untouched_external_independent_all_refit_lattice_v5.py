from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import pytest

from odsp.confirmatory_method_routing import route_confirmatory_method
from odsp.external_independent_lattice_freeze_manifest import (
    create_independent_external_lattice_freeze_manifest,
    validate_independent_external_lattice_freeze_plan,
)
from odsp.untouched_external_refit_independent_positive_lattice_contract_v5 import (
    run_untouched_external_independent_all_refit_lattice_contract_v5,
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
        "upstream_model_set_id": "independent-lattice-model-set-v1",
        "upstream_model_artifacts": [
            {"refit_id": refit_id, "artifact_id": "fit", "path": f"models/{refit_id}.bin"}
            for refit_id in ("r00", "r01")
        ],
        "external_dataset_id": "independent-lattice-external-v1",
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
            "seed": 20261003,
            "minimum_refits": 2,
            "minimum_blocks_per_group": 8,
            "gain_tolerance": 0.0,
        },
    }


def _roster_rows(group_count: int = 3, block_count: int = 8) -> list[dict[str, object]]:
    return [
        {
            "row_id": f"g{group_index}-b{block_index}",
            "group": f"g{group_index}",
            "block": f"g{group_index}-b{block_index}",
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
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for refit_id in ("r00", "r01"):
        values = _node_values(names, refit_id=refit_id, crossed_paths=crossed_paths)
        for group_index in range(3):
            for block_index in range(8):
                row: dict[str, object] = {
                    "row_id": f"g{group_index}-b{block_index}",
                    "refit_id": refit_id,
                    "group": f"g{group_index}",
                    "block": f"g{group_index}-b{block_index}",
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
        "endpoint_id": "independent-lattice-external-v5",
        "upstream_model_set_id": plan["upstream_model_set_id"],
        "upstream_model_artifacts": plan["upstream_model_artifacts"],
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
                "path": "freeze-independent-lattice.json",
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
):
    _write_csv(tmp_path / "roster.csv", _roster_rows())
    plan_payload = _plan(names)
    for artifact in plan_payload["upstream_model_artifacts"]:
        model_path = tmp_path / artifact["path"]
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_bytes(
            f"{artifact['refit_id']}:{artifact['artifact_id']}".encode("utf-8")
        )
    plan = tmp_path / "freeze-plan.json"
    plan.write_text(json.dumps(plan_payload), encoding="utf-8")
    manifest = tmp_path / "freeze-independent-lattice.json"
    create_independent_external_lattice_freeze_manifest(plan, manifest)
    scores = tmp_path / "scores.csv"
    _write_csv(scores, _long_rows(names, crossed_paths=crossed_paths))
    endpoint = tmp_path / "endpoint.json"
    endpoint.write_text(json.dumps(_external_contract(manifest, names)), encoding="utf-8")
    return manifest, scores, endpoint


def test_two_block_independent_external_lattice_is_universal(tmp_path: Path):
    manifest, _, endpoint = _setup(tmp_path)
    receipt = run_untouched_external_independent_all_refit_lattice_contract_v5(endpoint)
    assert receipt["receipt_type"] == (
        "odsp_untouched_external_independent_all_refit_positive_lattice_endpoint_v5"
    )
    assert receipt["freeze_manifest_sha256"] == _sha256(manifest)
    assert receipt["information_block_count"] == 2
    assert receipt["edge_count"] == 4
    assert receipt["result"]["all_refit_robust_full_transfer_path_count"] == 2
    assert receipt["result"]["all_refit_certified_path_status"] == "universal_full_transfer"
    assert receipt["boundaries"]["independent_row_metadata_frozen_before_outcome_access"] is True
    assert receipt["boundaries"]["runtime_independent_metadata_matches_frozen_manifest"] is True
    assert receipt["boundaries"]["different_refit_paths_can_be_combined"] is False


def test_three_block_independent_external_lattice_uses_12_edge_family(tmp_path: Path):
    _, _, endpoint = _setup(tmp_path, ("A", "B", "C"))
    receipt = run_untouched_external_independent_all_refit_lattice_contract_v5(endpoint)
    assert receipt["information_block_count"] == 3
    assert receipt["edge_count"] == 12
    assert receipt["result"]["total_admissible_path_count"] == 6
    assert receipt["result"]["all_refit_robust_full_transfer_path_count"] == 6
    assert receipt["result"]["all_refit_certified_path_status"] == "universal_full_transfer"


def test_crossed_refit_paths_do_not_create_independent_external_global_path(tmp_path: Path):
    _, _, endpoint = _setup(tmp_path, crossed_paths=True)
    receipt = run_untouched_external_independent_all_refit_lattice_contract_v5(endpoint)
    assert receipt["result"]["refit_robust_full_transfer_path_counts"] == [1, 1]
    assert receipt["result"]["all_refit_robust_full_transfer_path_count"] == 0
    assert receipt["result"]["all_refit_certified_path_status"] == "no_full_transfer"
    assert receipt["result"]["different_refit_paths_can_be_combined"] is False


def test_independent_row_group_block_weight_reassignment_fails_runtime_lock(tmp_path: Path):
    _, scores, endpoint = _setup(tmp_path)
    rows = list(csv.DictReader(scores.open(newline="", encoding="utf-8")))
    for row in rows:
        if row["row_id"] == "g0-b0":
            row["block"] = "g0-b99"
    _write_csv(scores, rows)
    with pytest.raises(ValueError, match="independent_row_metadata_sha256"):
        run_untouched_external_independent_all_refit_lattice_contract_v5(endpoint)


def test_node_semantic_tamper_fails_even_with_updated_manifest_hash(tmp_path: Path):
    manifest, _, endpoint = _setup(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["nodes"][1]["score_column"] = "score_b"
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    contract = json.loads(endpoint.read_text(encoding="utf-8"))
    contract["external_validation"]["freeze_manifest"]["sha256"] = _sha256(manifest)
    endpoint.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(ValueError, match="semantic mismatch for nodes"):
        run_untouched_external_independent_all_refit_lattice_contract_v5(endpoint)


def test_four_block_independent_external_lattice_rejected_before_outcome_access():
    with pytest.raises(ValueError, match="2 or 3 information blocks"):
        validate_independent_external_lattice_freeze_plan(_plan(("A", "B", "C", "D")))


def test_independent_lattice_roster_rejects_outcome_columns(tmp_path: Path):
    row = _roster_rows(group_count=1, block_count=1)[0]
    row["outcome"] = 1
    _write_csv(tmp_path / "roster.csv", [row])
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(_plan()), encoding="utf-8")
    with pytest.raises(ValueError, match="independent roster must contain only"):
        create_independent_external_lattice_freeze_manifest(plan, tmp_path / "freeze.json")


def test_independent_external_lattice_model_bytes_cannot_change_after_freeze(tmp_path: Path):
    manifest, _, endpoint = _setup(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["upstream_model_artifact_lock_id"] == "odsp-upstream-model-artifact-lock-v1"
    (tmp_path / "models/r00.bin").write_bytes(b"mutated-after-freeze")
    with pytest.raises(ValueError, match="upstream model artifact snapshot mismatch"):
        run_untouched_external_independent_all_refit_lattice_contract_v5(endpoint)


def test_router_promotes_independent_external_lattice_without_cli_surface_growth():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=3,
    )
    assert route.role == "primary_confirmatory"
    assert route.edge_count == 12
    assert route.canonical_surface == (
        "odsp.untouched_external_refit_independent_positive_lattice_contract_v5."
        "run_untouched_external_independent_all_refit_lattice_contract_v5"
    )
    assert route.cli_sequence == ()
