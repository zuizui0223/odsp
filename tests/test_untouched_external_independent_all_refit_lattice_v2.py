from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import pytest

from odsp.external_independent_lattice_freeze_manifest import (
    create_independent_external_lattice_freeze_manifest,
)
from odsp.untouched_external_refit_independent_positive_lattice_contract_v2 import (
    run_untouched_external_independent_all_refit_lattice_contract_v2,
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
                writer.writerow(
                    {
                        "row_id": f"g{g}-r{b:02d}",
                        "group": f"g{g}",
                        "block": f"g{g}-b{b:02d}",
                        "weight": "1",
                    }
                )
    return path


def _lattice(names: tuple[str, ...]):
    blocks = [{"name": name, "variables": [name.lower()]} for name in names]
    nodes = []
    for size in range(len(names) + 1):
        for subset in itertools.combinations(names, size):
            suffix = "".join(subset) or "0"
            nodes.append({"blocks": list(subset), "score_column": f"s{suffix}"})
    return blocks, nodes


def _plan(tmp_path: Path, roster: Path, *, names: tuple[str, ...]) -> Path:
    blocks, nodes = _lattice(names)
    path = tmp_path / "plan.json"
    path.write_text(
        json.dumps(
            {
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
                    "kind": "log",
                    "name": "log",
                    "orientation": "higher_is_better",
                    "common_scoring_rule": True,
                    "common_reference_measure": True,
                },
                "base_information": ["base"],
                "information_blocks": blocks,
                "nodes": nodes,
                "certification": {
                    "alternative": "greater",
                    "familywise_lower_confidence_level": 0.95,
                    "bootstrap_draws": 500,
                    "seed": 20261003,
                    "minimum_refits": 2,
                    "minimum_blocks_per_group": 8,
                    "gain_tolerance": 0.0,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _scores(
    tmp_path: Path,
    roster: Path,
    *,
    names: tuple[str, ...],
    swap_group: bool = False,
) -> Path:
    base_rows = list(csv.DictReader(roster.open(encoding="utf-8")))
    _, nodes = _lattice(names)
    score_columns = [row["score_column"] for row in nodes]
    path = tmp_path / "scores.csv"
    fields = ["row_id", "refit_id", "group", "block", "weight", *score_columns]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for refit in ("r0", "r1"):
            for index, row in enumerate(base_rows):
                out = dict(row)
                if swap_group and index == 0:
                    out["group"] = "g1"
                out["refit_id"] = refit
                for node in nodes:
                    out[node["score_column"]] = 0.4 * len(node["blocks"])
                writer.writerow(out)
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


def _contract(
    tmp_path: Path,
    scores: Path,
    manifest: Path,
) -> Path:
    plan = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    path = tmp_path / "contract.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "endpoint_id": "independent-lattice-external-v2",
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
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(("names", "edge_count"), [(("A", "B"), 4), (("A", "B", "C"), 12)])
def test_independent_external_lattice_freeze_and_run(
    tmp_path: Path,
    names: tuple[str, ...],
    edge_count: int,
):
    roster = _roster(tmp_path)
    plan = _plan(tmp_path, roster, names=names)
    manifest = tmp_path / "manifest.json"
    freeze = create_independent_external_lattice_freeze_manifest(plan, manifest)
    assert freeze["edge_count"] == edge_count
    route = freeze["confirmatory_route"]
    assert route["role"] == "primary_confirmatory"
    assert route["qualification_evidence_artifacts"]
    assert route["implementation_source_snapshot"]

    scores = _scores(tmp_path, roster, names=names)
    receipt = run_untouched_external_independent_all_refit_lattice_contract_v2(
        _contract(tmp_path, scores, manifest)
    )
    assert receipt["edge_count"] == edge_count
    assert receipt["result"]["all_refit_certified_path_status"] == "universal_full_transfer"
    assert receipt["boundaries"]["runtime_row_design_metadata_matches_frozen_manifest"] is True
    assert receipt["boundaries"]["runtime_confirmatory_route_matches_frozen_manifest"] is True
    assert receipt["boundaries"]["validation_group_independence_assumed"] is True


def test_post_outcome_group_reassignment_is_rejected(tmp_path: Path):
    names = ("A", "B")
    roster = _roster(tmp_path)
    plan = _plan(tmp_path, roster, names=names)
    manifest = tmp_path / "manifest.json"
    create_independent_external_lattice_freeze_manifest(plan, manifest)
    scores = _scores(tmp_path, roster, names=names, swap_group=True)
    with pytest.raises(ValueError, match="row_design_metadata_sha256"):
        run_untouched_external_independent_all_refit_lattice_contract_v2(
            _contract(tmp_path, scores, manifest)
        )


def test_tampered_frozen_confirmatory_route_is_rejected_even_with_updated_manifest_hash(
    tmp_path: Path,
):
    names = ("A", "B")
    roster = _roster(tmp_path)
    plan = _plan(tmp_path, roster, names=names)
    manifest = tmp_path / "manifest.json"
    create_independent_external_lattice_freeze_manifest(plan, manifest)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["confirmatory_route"]["qualification_evidence_artifacts"][0]["sha256"] = "0" * 64
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    scores = _scores(tmp_path, roster, names=names)
    contract = _contract(tmp_path, scores, manifest)
    contract_payload = json.loads(contract.read_text(encoding="utf-8"))
    contract_payload["external_validation"]["freeze_manifest"]["sha256"] = _sha(manifest)
    contract.write_text(json.dumps(contract_payload, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="confirmatory_route"):
        run_untouched_external_independent_all_refit_lattice_contract_v2(contract)


def test_four_block_freeze_is_rejected(tmp_path: Path):
    roster = _roster(tmp_path)
    plan = _plan(tmp_path, roster, names=("A", "B", "C", "D"))
    with pytest.raises(ValueError, match="2 or 3 information blocks"):
        create_independent_external_lattice_freeze_manifest(
            plan, tmp_path / "manifest.json"
        )
