"""Executable contracts for reproducible ODSP event-table analyses.

The contract layer is intentionally small.  It binds an input table to the
scientific roles required by :mod:`odsp.workflow` and records hashes of both the
contract and input data in the resulting receipt.  It never infers an
independence unit, fold, stratum, comparator, weighting policy or learner from
column names.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

from .covariate_state_prediction import make_state_classifier
from .workflow import (
    EventTableSpec,
    cross_validate_state_events,
    equal_stratum_equal_group_training_weights,
)


_TOP_LEVEL = {
    "schema_version",
    "endpoint_id",
    "data",
    "columns",
    "model",
    "baseline",
    "training_weight_policy",
    "gain_tolerance",
}
_DATA_FIELDS = {"path", "format"}
_COLUMN_FIELDS = {"state", "features", "group", "stratum", "fold", "weight"}
_MODEL_FIELDS = {"kind", "random_state", "parameters"}
_MODEL_KINDS = {"random_forest", "multinomial_logit"}
_BASELINES = {"pooled", "stratum"}
_WEIGHT_POLICIES = {"event_weight", "equal_stratum_equal_group"}


def _require_mapping(value: object, *, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _reject_unknown(mapping: Mapping[str, object], allowed: set[str], *, name: str) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise ValueError(f"{name} contains unknown fields: {', '.join(unknown)}")


def _require_text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def validate_endpoint_contract(contract: Mapping[str, object]) -> dict[str, object]:
    """Validate and normalize one endpoint contract.

    Unknown fields are rejected deliberately so a typo cannot silently change a
    scientific role.  The normalized dictionary is JSON-serializable and retains
    only explicitly supported choices.
    """

    contract = _require_mapping(contract, name="contract")
    _reject_unknown(contract, _TOP_LEVEL, name="contract")
    if int(contract.get("schema_version", -1)) != 1:
        raise ValueError("schema_version must be 1")

    endpoint_id = _require_text(contract.get("endpoint_id"), name="endpoint_id")

    data = _require_mapping(contract.get("data"), name="data")
    _reject_unknown(data, _DATA_FIELDS, name="data")
    data_path = _require_text(data.get("path"), name="data.path")
    data_format = _require_text(data.get("format"), name="data.format").lower()
    if data_format not in {"csv", "json"}:
        raise ValueError("data.format must be 'csv' or 'json'")

    columns = _require_mapping(contract.get("columns"), name="columns")
    _reject_unknown(columns, _COLUMN_FIELDS, name="columns")
    state = _require_text(columns.get("state"), name="columns.state")
    group = _require_text(columns.get("group"), name="columns.group")
    features_raw = columns.get("features")
    if not isinstance(features_raw, list) or not features_raw:
        raise ValueError("columns.features must be a non-empty JSON array")
    features = [
        _require_text(value, name=f"columns.features[{index}]")
        for index, value in enumerate(features_raw)
    ]
    optional_columns: dict[str, str | None] = {}
    for name in ("stratum", "fold", "weight"):
        value = columns.get(name)
        optional_columns[name] = (
            None if value is None else _require_text(value, name=f"columns.{name}")
        )

    model = _require_mapping(contract.get("model"), name="model")
    _reject_unknown(model, _MODEL_FIELDS, name="model")
    kind = _require_text(model.get("kind"), name="model.kind")
    if kind not in _MODEL_KINDS:
        raise ValueError("model.kind must be 'random_forest' or 'multinomial_logit'")
    random_state_raw = model.get("random_state", 20260904)
    if isinstance(random_state_raw, bool):
        raise ValueError("model.random_state must be an integer")
    try:
        random_state = int(random_state_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("model.random_state must be an integer") from exc
    parameters_raw = model.get("parameters", {})
    parameters = dict(_require_mapping(parameters_raw, name="model.parameters"))
    if "random_state" in parameters:
        raise ValueError("put random_state in model.random_state, not model.parameters")

    baseline = _require_text(contract.get("baseline", "pooled"), name="baseline")
    if baseline not in _BASELINES:
        raise ValueError("baseline must be 'pooled' or 'stratum'")
    if baseline == "stratum" and optional_columns["stratum"] is None:
        raise ValueError("baseline='stratum' requires columns.stratum")

    weight_policy = _require_text(
        contract.get("training_weight_policy", "event_weight"),
        name="training_weight_policy",
    )
    if weight_policy not in _WEIGHT_POLICIES:
        raise ValueError(
            "training_weight_policy must be 'event_weight' or "
            "'equal_stratum_equal_group'"
        )
    if weight_policy == "equal_stratum_equal_group" and optional_columns["stratum"] is None:
        raise ValueError(
            "equal_stratum_equal_group weighting requires columns.stratum"
        )

    tolerance_raw = contract.get("gain_tolerance", 0.0)
    try:
        tolerance = float(tolerance_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("gain_tolerance must be numeric") from exc
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    return {
        "schema_version": 1,
        "endpoint_id": endpoint_id,
        "data": {"path": data_path, "format": data_format},
        "columns": {
            "state": state,
            "features": features,
            "group": group,
            **optional_columns,
        },
        "model": {
            "kind": kind,
            "random_state": random_state,
            "parameters": parameters,
        },
        "baseline": baseline,
        "training_weight_policy": weight_policy,
        "gain_tolerance": tolerance,
    }


def load_endpoint_contract(path: str | Path) -> dict[str, object]:
    """Load and validate one JSON endpoint contract."""

    contract_path = Path(path)
    try:
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"contract is not valid JSON: {contract_path}") from exc
    return validate_endpoint_contract(_require_mapping(raw, name="contract"))


def _read_rows(data_path: Path, data_format: str) -> list[dict[str, object]]:
    if data_format == "csv":
        with data_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = [dict(row) for row in csv.DictReader(handle)]
    elif data_format == "json":
        raw = json.loads(data_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list) or not all(isinstance(row, Mapping) for row in raw):
            raise ValueError("JSON data must be an array of row objects")
        rows = [dict(row) for row in raw]
    else:  # pragma: no cover - contract validation prevents this branch.
        raise ValueError(f"unsupported data format: {data_format}")
    if not rows:
        raise ValueError("endpoint data contains no rows")
    return rows


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_endpoint_contract(path: str | Path) -> dict[str, object]:
    """Execute a validated endpoint contract and return an audit receipt."""

    contract_path = Path(path)
    contract = load_endpoint_contract(contract_path)
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
    spec = EventTableSpec(
        state=str(columns["state"]),
        features=tuple(str(value) for value in columns["features"]),
        group=str(columns["group"]),
        stratum=None if columns.get("stratum") is None else str(columns["stratum"]),
        fold=None if columns.get("fold") is None else str(columns["fold"]),
        weight=None if columns.get("weight") is None else str(columns["weight"]),
    )

    model_spec = contract["model"]
    assert isinstance(model_spec, Mapping)
    parameters = dict(model_spec["parameters"])
    estimator = make_state_classifier(
        str(model_spec["kind"]),
        random_state=int(model_spec["random_state"]),
        **parameters,
    )

    policy_name = str(contract["training_weight_policy"])
    policy = (
        None
        if policy_name == "event_weight"
        else equal_stratum_equal_group_training_weights
    )
    result = cross_validate_state_events(
        rows,
        spec=spec,
        estimator=estimator,
        baseline=str(contract["baseline"]),
        training_weight_policy=policy,
        gain_tolerance=float(contract["gain_tolerance"]),
    )

    return {
        "schema_version": 1,
        "receipt_type": "odsp_state_prediction_endpoint",
        "endpoint_id": contract["endpoint_id"],
        "contract_sha256": _sha256(contract_path),
        "data_sha256": _sha256(data_path),
        "data_path_declared": data_spec["path"],
        "data_format": data_spec["format"],
        "input_row_count": len(rows),
        "scientific_roles": {
            "state": columns["state"],
            "features": list(columns["features"]),
            "independence_unit": columns["group"],
            "stratum": columns.get("stratum"),
            "fold": columns.get("fold"),
            "event_weight": columns.get("weight"),
            "baseline": contract["baseline"],
            "training_weight_policy": policy_name,
            "gain_tolerance": contract["gain_tolerance"],
        },
        "model": model_spec,
        "result": result.as_dict(),
        "scientific_boundary": {
            "roles_inferred_from_column_names": False,
            "baseline_inferred": False,
            "training_weight_policy_inferred": False,
            "terminal_category_uses_independent_group_gains": True,
        },
    }
