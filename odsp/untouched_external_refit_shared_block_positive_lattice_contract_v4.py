"""Untouched external paired all-refit directional lattice endpoint.

The endpoint requires a pre-outcome semantic freeze of the complete lattice,
including information-block definitions and every subset-node score column. It
also freezes the exact row-to-group/shared-block/weight assignment used by the
paired validation design. Final validation reconstructs those semantics from the
external score table before running the calibrated 4-edge or 12-edge family in
every supplied refit and intersecting robust edges across that fixed refit set.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Mapping

import numpy as np

from .frozen_confirmatory_route import verify_frozen_confirmatory_route
from .external_paired_lattice_freeze_manifest import (
    _paired_row_metadata_sha256,
    _validate_lattice_definition,
)
from .information_lattice import InformationBlock
from .information_transfer_contract import (
    _mapping,
    _read_rows,
    _reject_unknown,
    _required_float,
    _required_int,
    _score,
    _text,
    _validate_score_contract,
    _value,
    _weight,
)
from .refit_information_lattice import RefitInformationLatticeNodeScores
from .refit_positive_lattice_robustness import (
    certify_all_refit_shared_block_positive_information_lattice_v2,
)
from .untouched_external_refit_positive_contract import (
    _file_sha256,
    _identifier,
    _validate_external_validation,
)
from .untouched_external_refit_positive_contract_v2 import (
    _assert_equal,
    _row_roster_sha256,
)
from .untouched_external_refit_shared_block_positive_contract_v3 import (
    _VALIDATION_DESIGN,
)


_TOP_LEVEL = {
    "schema_version",
    "endpoint_id",
    "upstream_model_set_id",
    "external_dataset_id",
    "data",
    "columns",
    "score",
    "external_validation",
    "base_information",
    "information_blocks",
    "nodes",
    "certification",
}
_DATA_FIELDS = {"path", "format"}
_COLUMN_FIELDS = {"row_id", "refit_id", "group", "block", "weight"}
_CERT_FIELDS = {
    "alternative",
    "familywise_lower_confidence_level",
    "bootstrap_draws",
    "seed",
    "minimum_refits",
    "minimum_shared_blocks",
    "gain_tolerance",
}
_MANIFEST_FIELDS = {
    "schema_version",
    "manifest_type",
    "frozen_at_utc",
    "upstream_model_set_id",
    "external_dataset_id",
    "external_row_ids_sha256",
    "paired_row_metadata_sha256",
    "validation_design",
    "confirmatory_route",
    "refit_ids",
    "score",
    "base_information",
    "information_blocks",
    "nodes",
    "edge_count",
    "certification",
}


def _validate_certification(raw: object) -> dict[str, object]:
    cert = _mapping(raw, name="certification")
    _reject_unknown(cert, _CERT_FIELDS, name="certification")
    alternative = _text(cert.get("alternative"), name="certification.alternative")
    if alternative != "greater":
        raise ValueError("certification.alternative must be 'greater'")
    confidence = _required_float(
        cert.get("familywise_lower_confidence_level"),
        name="certification.familywise_lower_confidence_level",
    )
    if not math.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError(
            "certification.familywise_lower_confidence_level must lie strictly between zero and one"
        )
    draws = _required_int(
        cert.get("bootstrap_draws"), name="certification.bootstrap_draws"
    )
    if draws < 500:
        raise ValueError("certification.bootstrap_draws must be >= 500")
    seed = _required_int(cert.get("seed"), name="certification.seed")
    minimum_refits = _required_int(
        cert.get("minimum_refits"), name="certification.minimum_refits"
    )
    if minimum_refits < 2:
        raise ValueError("certification.minimum_refits must be >= 2")
    minimum_shared = _required_int(
        cert.get("minimum_shared_blocks"),
        name="certification.minimum_shared_blocks",
    )
    if minimum_shared < 2:
        raise ValueError("certification.minimum_shared_blocks must be >= 2")
    tolerance = _required_float(
        cert.get("gain_tolerance"), name="certification.gain_tolerance"
    )
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("certification.gain_tolerance must be finite and non-negative")
    return {
        "alternative": "greater",
        "familywise_lower_confidence_level": confidence,
        "bootstrap_draws": draws,
        "seed": seed,
        "minimum_refits": minimum_refits,
        "minimum_shared_blocks": minimum_shared,
        "gain_tolerance": tolerance,
    }


def validate_untouched_external_paired_lattice_contract(
    raw: Mapping[str, object],
) -> dict[str, object]:
    contract = _mapping(raw, name="contract")
    _reject_unknown(contract, _TOP_LEVEL, name="contract")
    version = contract.get("schema_version")
    if isinstance(version, bool) or version != 1:
        raise ValueError("schema_version must be 1")
    endpoint_id = _text(contract.get("endpoint_id"), name="endpoint_id")
    model_set_id = _text(
        contract.get("upstream_model_set_id"), name="upstream_model_set_id"
    )
    dataset_id = _text(
        contract.get("external_dataset_id"), name="external_dataset_id"
    )

    data = _mapping(contract.get("data"), name="data")
    _reject_unknown(data, _DATA_FIELDS, name="data")
    data_path = _text(data.get("path"), name="data.path")
    data_format = _text(data.get("format"), name="data.format").lower()
    if data_format not in {"csv", "json"}:
        raise ValueError("data.format must be 'csv' or 'json'")

    columns = _mapping(contract.get("columns"), name="columns")
    _reject_unknown(columns, _COLUMN_FIELDS, name="columns")
    if columns.get("weight") is None:
        raise ValueError(
            "columns.weight is required for paired external lattice validation because row weights are frozen before outcome access"
        )
    normalized_columns = {
        "row_id": _text(columns.get("row_id"), name="columns.row_id"),
        "refit_id": _text(columns.get("refit_id"), name="columns.refit_id"),
        "group": _text(columns.get("group"), name="columns.group"),
        "block": _text(columns.get("block"), name="columns.block"),
        "weight": _text(columns.get("weight"), name="columns.weight"),
    }
    role_columns = [
        normalized_columns["row_id"],
        normalized_columns["refit_id"],
        normalized_columns["group"],
        normalized_columns["block"],
        normalized_columns["weight"],
    ]
    if len(set(role_columns)) != len(role_columns):
        raise ValueError(
            "row_id, refit_id, group, block and weight columns must be distinct"
        )

    score = _validate_score_contract(contract.get("score"))
    external = _validate_external_validation(contract.get("external_validation"))
    blocks, nodes, base, edge_count = _validate_lattice_definition(
        contract.get("information_blocks"),
        contract.get("nodes"),
        contract.get("base_information"),
    )
    score_columns = [str(node["score_column"]) for node in nodes]
    collision = sorted(set(score_columns) & set(role_columns))
    if collision:
        raise ValueError(
            "lattice score columns must be distinct from row-role columns: "
            + ", ".join(collision)
        )
    cert = _validate_certification(contract.get("certification"))
    return {
        "schema_version": 1,
        "endpoint_id": endpoint_id,
        "upstream_model_set_id": model_set_id,
        "external_dataset_id": dataset_id,
        "data": {"path": data_path, "format": data_format},
        "columns": normalized_columns,
        "score": score,
        "external_validation": external,
        "base_information": base,
        "information_blocks": blocks,
        "nodes": nodes,
        "edge_count": edge_count,
        "certification": cert,
    }


def load_untouched_external_paired_lattice_contract(
    path: str | Path,
) -> dict[str, object]:
    contract_path = Path(path)
    try:
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("paired lattice external contract is not valid JSON") from exc
    return validate_untouched_external_paired_lattice_contract(
        _mapping(raw, name="contract")
    )


def _runtime_table(contract_path: Path, contract: Mapping[str, object]):
    data_spec = contract["data"]
    assert isinstance(data_spec, Mapping)
    data_path = Path(str(data_spec["path"]))
    if not data_path.is_absolute():
        data_path = contract_path.parent / data_path
    if not data_path.is_file():
        raise FileNotFoundError(data_path)
    rows = _read_rows(data_path, str(data_spec["format"]))
    columns = contract["columns"]
    assert isinstance(columns, Mapping)
    row_id_col = str(columns["row_id"])
    refit_id_col = str(columns["refit_id"])
    group_col = str(columns["group"])
    block_col = str(columns["block"])
    weight_col = str(columns["weight"])
    nodes = contract["nodes"]
    assert isinstance(nodes, list)

    table: dict[str, dict[str, dict[str, object]]] = {}
    for row_index, row in enumerate(rows):
        refit_id = _identifier(
            _value(row, refit_id_col, row_index=row_index),
            name=f"row {row_index} refit_id",
        )
        row_id = _identifier(
            _value(row, row_id_col, row_index=row_index),
            name=f"row {row_index} row_id",
        )
        group = _identifier(
            _value(row, group_col, row_index=row_index),
            name=f"row {row_index} group",
        )
        block = _identifier(
            _value(row, block_col, row_index=row_index),
            name=f"row {row_index} block",
        )
        weight = _weight(
            _value(row, weight_col, row_index=row_index),
            column=weight_col,
            row_index=row_index,
        )
        scores = [
            _score(
                _value(row, str(node["score_column"]), row_index=row_index),
                column=str(node["score_column"]),
                row_index=row_index,
            )
            for node in nodes
        ]
        local = table.setdefault(refit_id, {})
        if row_id in local:
            raise ValueError(
                f"duplicate refit_id,row_id pair: ({refit_id!r}, {row_id!r})"
            )
        local[row_id] = {
            "group": group,
            "block": block,
            "weight": weight,
            "scores": scores,
        }

    refit_ids = tuple(sorted(table))
    if not refit_ids:
        raise ValueError("external lattice score table contains no refits")
    canonical_rows = tuple(sorted(table[refit_ids[0]]))
    if not canonical_rows:
        raise ValueError("external lattice score table contains no held-out rows")
    canonical_set = set(canonical_rows)
    for refit_id in refit_ids[1:]:
        local_set = set(table[refit_id])
        if local_set != canonical_set:
            missing = sorted(canonical_set - local_set)
            extra = sorted(local_set - canonical_set)
            raise ValueError(
                f"refit {refit_id!r} does not contain the canonical external row set; missing={missing!r}, extra={extra!r}"
            )

    first = table[refit_ids[0]]
    groups: list[str] = []
    shared_blocks: list[str] = []
    weights: list[float] = []
    for row_id in canonical_rows:
        record = first[row_id]
        groups.append(str(record["group"]))
        shared_blocks.append(str(record["block"]))
        weights.append(float(record["weight"]))
    if not sum(weights) > 0:
        raise ValueError("external row weights must have positive total mass")

    for refit_id in refit_ids[1:]:
        for index, row_id in enumerate(canonical_rows):
            record = table[refit_id][row_id]
            expected = (groups[index], shared_blocks[index], weights[index])
            observed = (
                str(record["group"]),
                str(record["block"]),
                float(record["weight"]),
            )
            if observed != expected:
                raise ValueError(
                    f"external row metadata differs across refits for row_id {row_id!r}"
                )

    refit_nodes: list[RefitInformationLatticeNodeScores] = []
    for node_index, node in enumerate(nodes):
        matrix = np.asarray(
            [
                [
                    float(table[refit_id][row_id]["scores"][node_index])
                    for row_id in canonical_rows
                ]
                for refit_id in refit_ids
            ],
            dtype=float,
        )
        refit_nodes.append(
            RefitInformationLatticeNodeScores(
                blocks=tuple(str(item) for item in node["blocks"]),
                score=matrix,
            )
        )
    return (
        data_path,
        rows,
        refit_ids,
        canonical_rows,
        groups,
        shared_blocks,
        weights,
        refit_nodes,
    )


def _load_manifest(path: Path) -> Mapping[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("paired lattice freeze manifest must be valid JSON") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("paired lattice freeze manifest must be a JSON object")
    unknown = sorted(set(raw) - _MANIFEST_FIELDS)
    if unknown:
        raise ValueError(
            f"paired lattice freeze manifest contains unknown fields: {unknown!r}"
        )
    if raw.get("schema_version") != 1 or isinstance(raw.get("schema_version"), bool):
        raise ValueError("paired lattice freeze manifest schema_version must be 1")
    if _text(raw.get("manifest_type"), name="freeze manifest.manifest_type") != (
        "odsp_pre_external_outcome_paired_lattice_freeze_v1"
    ):
        raise ValueError("freeze manifest has the wrong paired lattice manifest_type")
    if raw.get("validation_design") != _VALIDATION_DESIGN:
        raise ValueError("freeze manifest semantic mismatch for validation_design")
    return raw


def verify_paired_external_lattice_semantic_lock(
    path: str | Path,
) -> dict[str, object]:
    contract_path = Path(path)
    contract = load_untouched_external_paired_lattice_contract(contract_path)
    external = contract["external_validation"]
    assert isinstance(external, Mapping)
    freeze = external["freeze_manifest"]
    assert isinstance(freeze, Mapping)
    freeze_path = Path(str(freeze["path"]))
    if not freeze_path.is_absolute():
        freeze_path = contract_path.parent / freeze_path
    if not freeze_path.is_file():
        raise FileNotFoundError(freeze_path)
    if _file_sha256(freeze_path) != str(freeze["sha256"]):
        raise ValueError(
            "freeze manifest SHA256 does not match the declared pre-outcome artifact"
        )
    manifest = _load_manifest(freeze_path)
    (
        _,
        _,
        refit_ids,
        canonical_rows,
        groups,
        shared_blocks,
        weights,
        _,
    ) = _runtime_table(contract_path, contract)

    _assert_equal(
        str(manifest["frozen_at_utc"]),
        str(freeze["frozen_at_utc"]),
        field="frozen_at_utc",
    )
    _assert_equal(
        _text(
            manifest.get("upstream_model_set_id"),
            name="freeze manifest.upstream_model_set_id",
        ),
        str(contract["upstream_model_set_id"]),
        field="upstream_model_set_id",
    )
    _assert_equal(
        _text(
            manifest.get("external_dataset_id"),
            name="freeze manifest.external_dataset_id",
        ),
        str(contract["external_dataset_id"]),
        field="external_dataset_id",
    )
    _assert_equal(
        str(manifest["external_row_ids_sha256"]),
        _row_roster_sha256(canonical_rows),
        field="external_row_ids_sha256",
    )
    runtime_paired_metadata_sha = _paired_row_metadata_sha256(
        list(zip(canonical_rows, groups, shared_blocks, weights))
    )
    _assert_equal(
        _text(
            manifest.get("paired_row_metadata_sha256"),
            name="freeze manifest.paired_row_metadata_sha256",
        ),
        runtime_paired_metadata_sha,
        field="paired_row_metadata_sha256",
    )
    _assert_equal(
        tuple(sorted(str(item) for item in manifest["refit_ids"])),
        refit_ids,
        field="refit_ids",
    )
    _assert_equal(dict(manifest["score"]), dict(contract["score"]), field="score")
    _assert_equal(
        list(manifest["base_information"]),
        list(contract["base_information"]),
        field="base_information",
    )
    _assert_equal(
        list(manifest["information_blocks"]),
        list(contract["information_blocks"]),
        field="information_blocks",
    )
    _assert_equal(
        list(manifest["nodes"]), list(contract["nodes"]), field="nodes"
    )
    _assert_equal(
        int(manifest["edge_count"]),
        int(contract["edge_count"]),
        field="edge_count",
    )
    confirmatory_route = verify_frozen_confirmatory_route(
        manifest.get("confirmatory_route"),
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        information_block_count=len(contract["information_blocks"]),
    )
    _assert_equal(
        dict(manifest["certification"]),
        dict(contract["certification"]),
        field="certification",
    )
    return {
        "manifest_type": "odsp_pre_external_outcome_paired_lattice_freeze_v1",
        "upstream_model_set_id": str(contract["upstream_model_set_id"]),
        "external_dataset_id": str(contract["external_dataset_id"]),
        "external_row_ids_sha256": str(manifest["external_row_ids_sha256"]),
        "paired_row_metadata_sha256": runtime_paired_metadata_sha,
        "validation_design": dict(_VALIDATION_DESIGN),
        "refit_ids": list(refit_ids),
        "base_information": list(contract["base_information"]),
        "information_blocks": list(contract["information_blocks"]),
        "nodes": list(contract["nodes"]),
        "edge_count": int(contract["edge_count"]),
        "confirmatory_route": confirmatory_route,
        "certification": dict(contract["certification"]),
        "freeze_manifest_semantic_lock_verified": True,
    }


def run_untouched_external_paired_all_refit_lattice_contract_v4(
    path: str | Path,
) -> dict[str, object]:
    contract_path = Path(path)
    semantic_lock = verify_paired_external_lattice_semantic_lock(contract_path)
    contract = load_untouched_external_paired_lattice_contract(contract_path)
    (
        data_path,
        rows,
        refit_ids,
        canonical_rows,
        groups,
        shared_blocks,
        weights,
        refit_nodes,
    ) = _runtime_table(contract_path, contract)
    info_blocks = tuple(
        InformationBlock(
            name=str(row["name"]),
            variables=tuple(str(item) for item in row["variables"]),
        )
        for row in contract["information_blocks"]
    )
    cert = contract["certification"]
    assert isinstance(cert, Mapping)
    result = certify_all_refit_shared_block_positive_information_lattice_v2(
        refit_nodes,
        info_blocks,
        groups,
        shared_blocks,
        base_information=contract["base_information"],
        refit_ids=refit_ids,
        sample_weight=weights,
        familywise_lower_confidence_level=float(
            cert["familywise_lower_confidence_level"]
        ),
        bootstrap_draws=int(cert["bootstrap_draws"]),
        seed=int(cert["seed"]),
        minimum_refits=int(cert["minimum_refits"]),
        minimum_shared_blocks=int(cert["minimum_shared_blocks"]),
        gain_tolerance=float(cert["gain_tolerance"]),
    )
    external = contract["external_validation"]
    assert isinstance(external, Mapping)
    freeze = external["freeze_manifest"]
    assert isinstance(freeze, Mapping)
    freeze_path = Path(str(freeze["path"]))
    if not freeze_path.is_absolute():
        freeze_path = contract_path.parent / freeze_path
    return {
        "receipt_type": "odsp_untouched_external_paired_all_refit_positive_lattice_endpoint_v4",
        "endpoint_id": contract["endpoint_id"],
        "upstream_model_set_id": contract["upstream_model_set_id"],
        "external_dataset_id": contract["external_dataset_id"],
        "contract_sha256": _file_sha256(contract_path),
        "data_sha256": _file_sha256(data_path),
        "freeze_manifest_sha256": _file_sha256(freeze_path),
        "input_long_row_count": len(rows),
        "refit_count": len(refit_ids),
        "external_heldout_row_count": len(canonical_rows),
        "information_block_count": len(info_blocks),
        "edge_count": int(contract["edge_count"]),
        "external_validation": external,
        "freeze_manifest_semantic_lock": semantic_lock,
        "scientific_roles": {
            "alternative": "greater",
            "dataset_role": "untouched_external_validation",
            "validation_design": "paired_shared_blocks",
            "information_structure": "complete_information_lattice",
            "refit_uncertainty_role": "fixed_set_intersection_union_same_edge_all_refits",
            "validation_uncertainty_role": "paired_one_sided_familywise_bootstrap_t_all_edges_within_refit",
        },
        "result": result.as_dict(),
        "boundaries": {
            "untouched_external_validation_contract_satisfied": True,
            "freeze_manifest_hash_verified": True,
            "freeze_manifest_semantics_verified": True,
            "runtime_provenance_ids_match_frozen_manifest": True,
            "paired_row_metadata_frozen_before_outcome_access": True,
            "runtime_pairing_metadata_matches_frozen_manifest": True,
            "complete_lattice_node_table_frozen_before_outcome_access": True,
            "paired_shared_block_design_frozen_before_outcome_access": True,
            "confirmatory_route_locked_before_outcome_access": True,
            "runtime_confirmatory_route_matches_frozen_manifest": True,
            "different_refit_paths_can_be_combined": False,
            "four_or_more_information_blocks_supported": False,
            "validation_group_independence_assumed": False,
            "shared_block_exchangeability_assumed": True,
            "refit_ensemble_probability_sample_assumed": False,
            "refit_population_generalization_claimed": False,
            "historical_no_prior_outcome_access_independently_proven_by_odsp": False,
            "development_data_disjointness_independently_proven_by_odsp": False,
            "provenance_declarations_are_user_supplied": True,
        },
    }