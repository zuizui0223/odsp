"""Semantically locked untouched external validation for paired shared blocks.

This endpoint composes three already-separated evidential layers:
1. one-sided familywise bootstrap-t within each upstream refit;
2. exact shared-block paired resampling across validation groups;
3. fixed-set all-refit intersection robustness across the supplied refits.

The pre-outcome manifest must explicitly freeze the paired validation design.
Independent-group and paired-group external endpoints are intentionally distinct.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import numpy as np

from ._confirmatory_execution_guard import verify_confirmatory_execution_route
from .information_transfer_contract import _read_rows, _score, _text, _value, _weight
from .refit_information_transfer import RefitInformationLevelScores
from .refit_positive_robustness import (
    certify_all_refit_shared_block_positive_information_transfer_v2,
)
from .untouched_external_refit_positive_contract import (
    _file_sha256,
    _identifier,
    load_untouched_external_refit_positive_contract,
)
from .untouched_external_refit_positive_contract_v2 import (
    _assert_equal,
    _normalize_manifest_certification,
    _normalize_manifest_levels,
    _normalize_manifest_score,
    _row_roster_sha256,
)


_MANIFEST_FIELDS = {
    "schema_version",
    "manifest_type",
    "frozen_at_utc",
    "upstream_model_set_id",
    "external_dataset_id",
    "external_row_ids_sha256",
    "validation_design",
    "refit_ids",
    "reference_refit_id",
    "score",
    "levels",
    "certification",
}
_VALIDATION_DESIGN = {
    "kind": "paired_shared_blocks",
    "exact_positive_mass_shared_block_support_required": True,
    "shared_block_exchangeability_assumed": True,
    "missing_shared_blocks_imputed": False,
    "validation_group_independence_assumed": False,
}


def _load_paired_manifest(path: Path) -> Mapping[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("paired freeze manifest must be valid JSON") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("paired freeze manifest must be a JSON object")
    unknown = sorted(set(raw) - _MANIFEST_FIELDS)
    if unknown:
        raise ValueError(f"paired freeze manifest contains unknown fields: {unknown!r}")
    if raw.get("schema_version") != 2 or isinstance(raw.get("schema_version"), bool):
        raise ValueError("paired freeze manifest schema_version must be 2")
    if _text(raw.get("manifest_type"), name="freeze manifest.manifest_type") != (
        "odsp_pre_external_outcome_paired_freeze_v1"
    ):
        raise ValueError(
            "freeze manifest.manifest_type must be 'odsp_pre_external_outcome_paired_freeze_v1'"
        )
    design = raw.get("validation_design")
    if design != _VALIDATION_DESIGN:
        raise ValueError(
            f"freeze manifest semantic mismatch for validation_design: frozen={design!r}, runtime={_VALIDATION_DESIGN!r}"
        )
    return raw


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
    weight_col = None if columns.get("weight") is None else str(columns["weight"])
    level_specs = contract["levels"]
    assert isinstance(level_specs, list)

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
        weight = 1.0 if weight_col is None else _weight(
            _value(row, weight_col, row_index=row_index),
            column=weight_col,
            row_index=row_index,
        )
        scores = [
            _score(
                _value(row, str(level["score_column"]), row_index=row_index),
                column=str(level["score_column"]),
                row_index=row_index,
            )
            for level in level_specs
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
        raise ValueError("external refit score table contains no refits")
    canonical_rows = tuple(sorted(table[refit_ids[0]]))
    if not canonical_rows:
        raise ValueError("external refit score table contains no held-out rows")
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
    blocks: list[str] = []
    weights: list[float] = []
    for row_id in canonical_rows:
        record = first[row_id]
        groups.append(str(record["group"]))
        blocks.append(str(record["block"]))
        weights.append(float(record["weight"]))
    if not sum(weights) > 0:
        raise ValueError("external row weights must have positive total mass")

    for refit_id in refit_ids[1:]:
        for row_index, row_id in enumerate(canonical_rows):
            record = table[refit_id][row_id]
            expected = (groups[row_index], blocks[row_index], weights[row_index])
            observed = (
                str(record["group"]),
                str(record["block"]),
                float(record["weight"]),
            )
            if observed != expected:
                raise ValueError(
                    f"external row metadata differs across refits for row_id {row_id!r}"
                )

    refit_levels: list[RefitInformationLevelScores] = []
    for level_index, level in enumerate(level_specs):
        matrix = np.asarray(
            [
                [
                    float(table[refit_id][row_id]["scores"][level_index])
                    for row_id in canonical_rows
                ]
                for refit_id in refit_ids
            ],
            dtype=float,
        )
        refit_levels.append(
            RefitInformationLevelScores(
                name=str(level["name"]),
                information=tuple(str(item) for item in level["information"]),
                score=matrix,
            )
        )
    return data_path, rows, refit_ids, canonical_rows, groups, blocks, weights, refit_levels


def verify_paired_external_freeze_semantic_lock(
    path: str | Path,
) -> dict[str, object]:
    contract_path = Path(path)
    contract = load_untouched_external_refit_positive_contract(contract_path)
    external = contract["external_validation"]
    assert isinstance(external, Mapping)
    freeze_spec = external["freeze_manifest"]
    assert isinstance(freeze_spec, Mapping)
    freeze_path = Path(str(freeze_spec["path"]))
    if not freeze_path.is_absolute():
        freeze_path = contract_path.parent / freeze_path
    if not freeze_path.is_file():
        raise FileNotFoundError(freeze_path)
    actual_sha = _file_sha256(freeze_path)
    if actual_sha != str(freeze_spec["sha256"]):
        raise ValueError("freeze manifest SHA256 does not match the declared pre-outcome artifact")
    manifest = _load_paired_manifest(freeze_path)

    _, _, refit_ids, canonical_rows, _, _, _, _ = _runtime_table(
        contract_path, contract
    )
    _assert_equal(
        _text(manifest.get("frozen_at_utc"), name="freeze manifest.frozen_at_utc"),
        str(freeze_spec["frozen_at_utc"]),
        field="frozen_at_utc",
    )
    frozen_roster_sha = _text(
        manifest.get("external_row_ids_sha256"),
        name="freeze manifest.external_row_ids_sha256",
    ).lower()
    _assert_equal(
        frozen_roster_sha,
        _row_roster_sha256(canonical_rows),
        field="external_row_ids_sha256",
    )
    frozen_refits = tuple(
        sorted(
            _text(item, name="freeze manifest.refit_ids[]")
            for item in manifest.get("refit_ids", [])
        )
    )
    _assert_equal(frozen_refits, refit_ids, field="refit_ids")

    cert = contract["certification"]
    assert isinstance(cert, Mapping)
    frozen_reference = _text(
        manifest.get("reference_refit_id"), name="freeze manifest.reference_refit_id"
    )
    _assert_equal(
        frozen_reference,
        str(cert["reference_refit_id"]),
        field="reference_refit_id",
    )
    if frozen_reference not in frozen_refits:
        raise ValueError("freeze manifest reference_refit_id is not present in frozen refit_ids")

    frozen_score = _normalize_manifest_score(manifest.get("score"))
    _assert_equal(frozen_score, dict(contract["score"]), field="score")
    frozen_levels = _normalize_manifest_levels(manifest.get("levels"))
    runtime_levels = [
        {"name": str(level["name"]), "information": list(level["information"])}
        for level in contract["levels"]
    ]
    _assert_equal(frozen_levels, runtime_levels, field="levels")
    frozen_cert = _normalize_manifest_certification(manifest.get("certification"))
    runtime_cert = {
        "alternative": str(cert["alternative"]),
        "familywise_lower_confidence_level": float(cert["familywise_lower_confidence_level"]),
        "bootstrap_draws": int(cert["bootstrap_draws"]),
        "seed": int(cert["seed"]),
        "minimum_refits": int(cert["minimum_refits"]),
        "minimum_blocks_per_group": int(cert["minimum_blocks_per_group"]),
        "gain_tolerance": float(cert["gain_tolerance"]),
    }
    _assert_equal(frozen_cert, runtime_cert, field="certification")

    return {
        "manifest_type": "odsp_pre_external_outcome_paired_freeze_v1",
        "upstream_model_set_id": _text(
            manifest.get("upstream_model_set_id"),
            name="freeze manifest.upstream_model_set_id",
        ),
        "external_dataset_id": _text(
            manifest.get("external_dataset_id"),
            name="freeze manifest.external_dataset_id",
        ),
        "external_row_ids_sha256": frozen_roster_sha,
        "validation_design": dict(_VALIDATION_DESIGN),
        "refit_ids": list(refit_ids),
        "reference_refit_id": frozen_reference,
        "score": frozen_score,
        "levels": frozen_levels,
        "certification": frozen_cert,
        "freeze_manifest_semantic_lock_verified": True,
    }


def run_untouched_external_refit_shared_block_positive_contract_v3(
    path: str | Path,
) -> dict[str, object]:
    contract_path = Path(path)
    semantic_lock = verify_paired_external_freeze_semantic_lock(contract_path)
    contract = load_untouched_external_refit_positive_contract(contract_path)
    levels = contract["levels"]
    assert isinstance(levels, list)
    confirmatory_route = verify_confirmatory_execution_route(
        validation_design="paired_shared_blocks",
        information_structure="filtration",
        canonical_surface=(
            "odsp.untouched_external_refit_shared_block_positive_contract_v3."
            "run_untouched_external_refit_shared_block_positive_contract_v3"
        ),
        contrast_count=len(levels) - 1,
    )
    data_path, rows, refit_ids, canonical_rows, groups, blocks, weights, refit_levels = (
        _runtime_table(contract_path, contract)
    )
    cert = contract["certification"]
    assert isinstance(cert, Mapping)
    result = certify_all_refit_shared_block_positive_information_transfer_v2(
        refit_levels,
        groups,
        blocks,
        refit_ids=refit_ids,
        score_name=str(contract["score"]["name"]),
        sample_weight=weights,
        familywise_lower_confidence_level=float(cert["familywise_lower_confidence_level"]),
        bootstrap_draws=int(cert["bootstrap_draws"]),
        seed=int(cert["seed"]),
        minimum_refits=int(cert["minimum_refits"]),
        minimum_shared_blocks=int(cert["minimum_blocks_per_group"]),
        gain_tolerance=float(cert["gain_tolerance"]),
    )

    external = contract["external_validation"]
    assert isinstance(external, Mapping)
    freeze_spec = external["freeze_manifest"]
    assert isinstance(freeze_spec, Mapping)
    freeze_path = Path(str(freeze_spec["path"]))
    if not freeze_path.is_absolute():
        freeze_path = contract_path.parent / freeze_path

    return {
        "receipt_type": "odsp_untouched_external_refit_shared_block_positive_validation_endpoint_v3",
        "endpoint_id": contract["endpoint_id"],
        "contract_sha256": _file_sha256(contract_path),
        "data_sha256": _file_sha256(data_path),
        "freeze_manifest_sha256": _file_sha256(freeze_path),
        "input_long_row_count": len(rows),
        "refit_count": len(refit_ids),
        "external_heldout_row_count": len(canonical_rows),
        "external_validation": external,
        "freeze_manifest_semantic_lock": semantic_lock,
        "confirmatory_route": confirmatory_route,
        "scientific_roles": {
            "alternative": "greater",
            "dataset_role": "untouched_external_validation",
            "validation_design": "paired_shared_blocks",
            "refit_uncertainty_role": "fixed_set_intersection_union_all_refits",
            "validation_uncertainty_role": "paired_one_sided_familywise_bootstrap_t_within_refit",
        },
        "result": result.as_dict(),
        "boundaries": {
            "untouched_external_validation_contract_satisfied": True,
            "freeze_manifest_hash_verified": True,
            "freeze_manifest_semantics_verified": True,
            "external_row_roster_locked_before_outcome_access": True,
            "runtime_analysis_matches_frozen_manifest": True,
            "confirmatory_route_verified": True,
            "paired_shared_block_design_frozen_before_outcome_access": True,
            "exact_positive_mass_shared_block_support_required": True,
            "missing_shared_blocks_imputed": False,
            "validation_group_independence_assumed": False,
            "shared_block_exchangeability_assumed": True,
            "refit_ensemble_probability_sample_assumed": False,
            "refit_population_generalization_claimed": False,
            "historical_no_prior_outcome_access_independently_proven_by_odsp": False,
            "development_data_disjointness_independently_proven_by_odsp": False,
            "provenance_declarations_are_user_supplied": True,
        },
    }
