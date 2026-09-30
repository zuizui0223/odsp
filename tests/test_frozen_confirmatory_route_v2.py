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
            "seed": 20260922,
            "minimum_refits": 2,
            "minimum_blocks_per_group": 8,
            "gain_tolerance": 0.0,
        },
    }


def _paired_lattice_plan() -> dict[str, object]:
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
            {"name": "C", "variables": ["c"]},
        ],
        "nodes": [
            {"blocks": [], "score_column": "s0"},
            {"blocks": ["A"], "score_column": "sA"},
            {"blocks": ["B"], "score_column": "sB"},
            {"blocks": ["C"], "score_column": "sC"},
            {"blocks": ["A", "B"], "score_column": "sAB"},
            {"blocks": ["A", "C"], "score_column": "sAC"},
            {"blocks": ["B", "C"], "score_column": "sBC"},
            {"blocks": ["A", "B", "C"], "score_column": "sABC"},
        ],
        "certification": {
            "alternative": "greater",
            "familywise_lower_confidence_level": 0.95,
            "bootstrap_draws": 500,
            "seed": 20260922,
            "minimum_refits": 2,
            "minimum_shared_blocks": 8,
            "gain_tolerance": 0.0,
        },
    }


def test_frozen_route_contains_family_specific_qualification_evidence():
    route = build_frozen_confirmatory_route(
        validation_design="independent_groups",
        information_structure="filtration",
        contrast_count=4,
    )
    assert route["role"] == "primary_confirmatory"
    assert route["qualification_key"].endswith("contrast_count=4")
    assert route["qualification_evidence"] == [
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
        "INDEPENDENT_C4_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json",
        "ODSP_REFIT_ONE_SIDED_POSITIVE_TRANSFER_CONTRACT.json",
        "ODSP_UNTOUCHED_EXTERNAL_FREEZE_SEMANTIC_LOCK_V2.json",
    ]


def test_frozen_route_rejects_qualification_evidence_tamper():
    frozen = build_frozen_confirmatory_route(
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        information_block_count=3,
    )
    tampered = dict(frozen)
    tampered["qualification_evidence"] = list(frozen["qualification_evidence"])[:-1]
    with pytest.raises(ValueError, match="confirmatory_route"):
        verify_frozen_confirmatory_route(
            tampered,
            validation_design="paired_shared_blocks",
            information_structure="complete_lattice",
            information_block_count=3,
        )


def test_independent_generator_freezes_route_and_evidence(tmp_path: Path):
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
    assert payload["confirmatory_route"]["qualification_evidence"]


def test_paired_generator_freezes_route_and_evidence(tmp_path: Path):
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


def test_paired_lattice_generator_freezes_route_and_evidence(tmp_path: Path):
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
    plan.write_text(json.dumps(_paired_lattice_plan()), encoding="utf-8")
    manifest = tmp_path / "freeze.json"
    create_paired_external_lattice_freeze_manifest(plan, manifest)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["confirmatory_route"] == build_frozen_confirmatory_route(
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        information_block_count=3,
    )
    assert payload["confirmatory_route"]["edge_count"] == 12
