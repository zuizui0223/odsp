from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from odsp.external_freeze_manifest import create_external_freeze_manifest
from odsp.external_paired_freeze_manifest import create_paired_external_freeze_manifest
from odsp.external_paired_lattice_freeze_manifest import (
    create_paired_external_lattice_freeze_manifest,
)
from odsp.frozen_confirmatory_route import (
    build_frozen_confirmatory_route,
    verify_frozen_confirmatory_route,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _filtration_plan() -> dict[str, object]:
    return {
        "schema_version": 1,
        "upstream_model_set_id": "models-v1",
        "external_dataset_id": "external-v1",
        "roster": {"path": "roster.csv", "format": "csv", "row_id_column": "row_id"},
        "refit_ids": ["r00", "r01"],
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
            "seed": 20260921,
            "minimum_refits": 2,
            "minimum_blocks_per_group": 8,
            "gain_tolerance": 0.0,
        },
    }


def _lattice_plan() -> dict[str, object]:
    return {
        "schema_version": 1,
        "upstream_model_set_id": "models-v1",
        "external_dataset_id": "external-v1",
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
            {"blocks": [], "score_column": "score_none"},
            {"blocks": ["A"], "score_column": "score_a"},
            {"blocks": ["B"], "score_column": "score_b"},
            {"blocks": ["A", "B"], "score_column": "score_ab"},
        ],
        "certification": {
            "alternative": "greater",
            "familywise_lower_confidence_level": 0.95,
            "bootstrap_draws": 500,
            "seed": 20260921,
            "minimum_refits": 2,
            "minimum_shared_blocks": 8,
            "gain_tolerance": 0.0,
        },
    }


def test_frozen_route_builds_only_primary_external_routes():
    independent = build_frozen_confirmatory_route(
        validation_design="independent_groups",
        information_structure="filtration",
        contrast_count=2,
    )
    assert independent["role"] == "primary_confirmatory"
    assert independent["canonical_surface"] == (
        "odsp.untouched_external_refit_positive_contract_v2."
        "run_untouched_external_refit_positive_contract_v2"
    )
    assert independent["upstream_refits"] == "fixed_set"
    assert independent["external_validation"] == "untouched_frozen"

    paired = build_frozen_confirmatory_route(
        validation_design="paired_shared_blocks",
        information_structure="filtration",
        contrast_count=2,
    )
    assert paired["canonical_surface"] == (
        "odsp.untouched_external_refit_shared_block_positive_contract_v3."
        "run_untouched_external_refit_shared_block_positive_contract_v3"
    )

    lattice = build_frozen_confirmatory_route(
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        information_block_count=2,
    )
    assert lattice["edge_count"] == 4
    assert lattice["canonical_surface"] == (
        "odsp.untouched_external_refit_shared_block_positive_lattice_contract_v4."
        "run_untouched_external_paired_all_refit_lattice_contract_v4"
    )


def test_frozen_route_rejects_unqualified_external_route():
    with pytest.raises(ValueError, match="not primary_confirmatory"):
        build_frozen_confirmatory_route(
            validation_design="independent_groups",
            information_structure="complete_lattice",
            information_block_count=2,
        )


def test_frozen_route_verifier_rejects_method_family_tamper():
    frozen = build_frozen_confirmatory_route(
        validation_design="paired_shared_blocks",
        information_structure="filtration",
        contrast_count=2,
    )
    tampered = dict(frozen)
    tampered["canonical_surface"] = (
        "odsp.untouched_external_refit_positive_contract_v2."
        "run_untouched_external_refit_positive_contract_v2"
    )
    with pytest.raises(ValueError, match="confirmatory_route"):
        verify_frozen_confirmatory_route(
            tampered,
            validation_design="paired_shared_blocks",
            information_structure="filtration",
            contrast_count=2,
        )


def test_independent_generator_freezes_canonical_route(tmp_path: Path):
    _write_csv(
        tmp_path / "roster.csv",
        [{"row_id": f"g{g}-b{b}"} for g in range(2) for b in range(8)],
    )
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(_filtration_plan()), encoding="utf-8")
    manifest = tmp_path / "freeze.json"
    create_external_freeze_manifest(plan, manifest)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["confirmatory_route"] == build_frozen_confirmatory_route(
        validation_design="independent_groups",
        information_structure="filtration",
        contrast_count=2,
    )


def test_paired_generator_freezes_canonical_route(tmp_path: Path):
    _write_csv(
        tmp_path / "roster.csv",
        [{"row_id": f"g{g}-b{b}"} for g in range(3) for b in range(8)],
    )
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(_filtration_plan()), encoding="utf-8")
    manifest = tmp_path / "freeze.json"
    create_paired_external_freeze_manifest(plan, manifest)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["confirmatory_route"] == build_frozen_confirmatory_route(
        validation_design="paired_shared_blocks",
        information_structure="filtration",
        contrast_count=2,
    )


def test_paired_lattice_generator_freezes_canonical_route(tmp_path: Path):
    _write_csv(
        tmp_path / "roster.csv",
        [
            {
                "row_id": f"g{g}-b{b}",
                "group": f"g{g}",
                "block": f"b{b}",
                "weight": 1.0,
            }
            for g in range(3)
            for b in range(8)
        ],
    )
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(_lattice_plan()), encoding="utf-8")
    manifest = tmp_path / "freeze.json"
    create_paired_external_lattice_freeze_manifest(plan, manifest)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["confirmatory_route"] == build_frozen_confirmatory_route(
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        information_block_count=2,
    )


def test_machine_contracts_freeze_and_reverify_confirmatory_route():
    root = Path(".")
    generator = json.loads(
        (root / "ODSP_PREOUTCOME_EXTERNAL_FREEZE_GENERATOR_CONTRACT_V1.json").read_text(
            encoding="utf-8"
        )
    )
    semantic = json.loads(
        (root / "ODSP_UNTOUCHED_EXTERNAL_FREEZE_SEMANTIC_LOCK_V2.json").read_text(
            encoding="utf-8"
        )
    )
    paired = json.loads(
        (root / "ODSP_PAIRED_REFIT_UNTOUCHED_EXTERNAL_V3_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    lattice = json.loads(
        (root / "ODSP_UNTOUCHED_EXTERNAL_PAIRED_ALL_REFIT_LATTICE_V4_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )

    assert generator["manifest"]["confirmatory_route_frozen"] is True
    assert generator["manifest"]["unqualified_route_manifest_creation_allowed"] is False
    assert semantic["runtime_exact_match_requirements"]["confirmatory_route"] is True
    assert semantic["fail_closed"]["confirmatory_route_mismatch"] is True
    assert paired["pre_outcome_freeze"]["confirmatory_route_frozen"] is True
    assert paired["external_validation"]["runtime_confirmatory_route_must_match_frozen_manifest"] is True
    assert lattice["pre_outcome_freeze"]["confirmatory_route_frozen"] is True
    assert lattice["external_validation"]["runtime_confirmatory_route_must_match_frozen_manifest"] is True
