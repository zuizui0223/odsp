from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from odsp.external_independent_lattice_freeze_manifest import (
    create_independent_external_lattice_freeze_manifest,
)
from odsp.untouched_external_refit_independent_positive_lattice_contract_v1 import (
    run_untouched_external_independent_all_refit_lattice_contract_v1,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _roster(tmp_path: Path) -> Path:
    path = tmp_path / "roster.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_id", "group", "block", "weight"])
        writer.writeheader()
        for g in range(3):
            for b in range(8):
                writer.writerow({
                    "row_id": f"g{g}-r{b:02d}",
                    "group": f"g{g}",
                    "block": f"g{g}-b{b:02d}",
                    "weight": "1",
                })
    return path


def _plan(tmp_path: Path, roster: Path) -> Path:
    path = tmp_path / "plan.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "upstream_model_set_id": "models-v1",
        "external_dataset_id": "external-v1",
        "roster": {
            "path": roster.name,
            "format": "csv",
            "row_id_column": "row_id",
            "group_column": "group",
            "block_column": "block",
            "weight_column": "weight",
        },
        "refit_ids": ["r1", "r0"],
        "score": {
            "kind": "proper_score",
            "name": "log",
            "orientation": "higher_is_better",
            "common_scoring_rule": True,
            "common_reference_measure": True,
        },
        "base_information": ["base"],
        "information_blocks": [
            {"name": "A", "variables": ["a"]},
            {"name": "B", "variables": ["b"]},
        ],
        "nodes": [
            {"blocks": [], "score_column": "s0"},
            {"blocks": ["A"], "score_column": "sA"},
            {"blocks": ["B"], "score_column": "sB"},
            {"blocks": ["A", "B"], "score_column": "sAB"},
        ],
        "certification": {
            "alternative": "greater",
            "familywise_lower_confidence_level": 0.95,
            "bootstrap_draws": 500,
            "seed": 20260919,
            "minimum_refits": 2,
            "minimum_blocks_per_group": 8,
            "gain_tolerance": 0.0,
        },
    }, indent=2), encoding="utf-8")
    return path


def _scores(tmp_path: Path, roster: Path, *, swap_group: bool = False) -> Path:
    base_rows = list(csv.DictReader(roster.open(encoding="utf-8")))
    path = tmp_path / "scores.csv"
    fields = ["row_id", "refit_id", "group", "block", "weight", "s0", "sA", "sB", "sAB"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for refit in ("r0", "r1"):
            for i, row in enumerate(base_rows):
                group = row["group"]
                if swap_group and i == 0:
                    group = "g1"
                writer.writerow({
                    **row,
                    "group": group,
                    "refit_id": refit,
                    "s0": 0.0,
                    "sA": 0.4,
                    "sB": 0.4,
                    "sAB": 0.8,
                })
    return path


def _external(manifest: Path) -> dict[str, object]:
    frozen = json.loads(manifest.read_text(encoding="utf-8"))["frozen_at_utc"]
    return {
        "dataset_role": "untouched_external_validation",
        "freeze_manifest": {
            "path": manifest.name,
            "sha256": _sha(manifest),
            "frozen_at_utc": frozen,
        },
        "external_outcomes_first_accessed_at_utc": "2099-01-01T00:00:00Z",
        "development_data_disjoint": True,
        "models_frozen_before_external_outcome_access": True,
        "refit_ensemble_frozen_before_external_outcome_access": True,
        "filtration_frozen_before_external_outcome_access": True,
        "score_rule_frozen_before_external_outcome_access": True,
        "gain_tolerance_frozen_before_external_outcome_access": True,
        "alternative_frozen_before_external_outcome_access": True,
        "external_rows_used_for_upstream_fit": False,
        "external_rows_used_for_refit_generation": False,
        "external_rows_used_for_model_selection": False,
        "external_rows_used_for_filtration_selection": False,
        "external_outcomes_used_for_threshold_selection": False,
        "external_outcomes_used_for_score_rule_selection": False,
        "external_outcomes_used_for_any_development_decision": False,
    }


def _contract(tmp_path: Path, scores: Path, manifest: Path) -> Path:
    plan = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    path = tmp_path / "contract.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "endpoint_id": "independent-lattice-external-v1",
        "upstream_model_set_id": "models-v1",
        "external_dataset_id": "external-v1",
        "data": {"path": scores.name, "format": "csv"},
        "columns": {
            "row_id": "row_id",
            "refit_id": "refit_id",
            "group": "group",
            "block": "block",
            "weight": "weight",
        },
        "score": plan["score"],
        "external_validation": _external(manifest),
        "base_information": plan["base_information"],
        "information_blocks": plan["information_blocks"],
        "nodes": plan["nodes"],
        "certification": plan["certification"],
    }, indent=2), encoding="utf-8")
    return path


def test_independent_external_lattice_freeze_and_run(tmp_path: Path):
    roster = _roster(tmp_path)
    plan = _plan(tmp_path, roster)
    manifest = tmp_path / "manifest.json"
    freeze = create_independent_external_lattice_freeze_manifest(plan, manifest)
    assert freeze["edge_count"] == 4
    assert freeze["boundaries"]["row_design_metadata_frozen_before_outcome_access"] is True

    scores = _scores(tmp_path, roster)
    receipt = run_untouched_external_independent_all_refit_lattice_contract_v1(
        _contract(tmp_path, scores, manifest)
    )
    assert receipt["edge_count"] == 4
    assert receipt["result"]["all_refit_certified_path_status"] == "universal_full_transfer"
    assert receipt["boundaries"]["runtime_row_design_metadata_matches_frozen_manifest"] is True
    assert receipt["boundaries"]["validation_group_independence_assumed"] is True


def test_post_outcome_group_reassignment_is_rejected(tmp_path: Path):
    roster = _roster(tmp_path)
    plan = _plan(tmp_path, roster)
    manifest = tmp_path / "manifest.json"
    create_independent_external_lattice_freeze_manifest(plan, manifest)
    scores = _scores(tmp_path, roster, swap_group=True)
    with pytest.raises(ValueError, match="row_design_metadata_sha256"):
        run_untouched_external_independent_all_refit_lattice_contract_v1(
            _contract(tmp_path, scores, manifest)
        )


def test_three_block_freeze_is_rejected(tmp_path: Path):
    roster = _roster(tmp_path)
    plan = _plan(tmp_path, roster)
    payload = json.loads(plan.read_text(encoding="utf-8"))
    payload["information_blocks"].append({"name": "C", "variables": ["c"]})
    payload["nodes"] = [
        {"blocks": [], "score_column": "s0"},
        {"blocks": ["A"], "score_column": "sA"},
        {"blocks": ["B"], "score_column": "sB"},
        {"blocks": ["C"], "score_column": "sC"},
        {"blocks": ["A", "B"], "score_column": "sAB"},
        {"blocks": ["A", "C"], "score_column": "sAC"},
        {"blocks": ["B", "C"], "score_column": "sBC"},
        {"blocks": ["A", "B", "C"], "score_column": "sABC"},
    ]
    plan.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly 2 information blocks"):
        create_independent_external_lattice_freeze_manifest(
            plan, tmp_path / "manifest.json"
        )
