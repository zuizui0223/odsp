"""Managed training-to-forecast binding for independent-group state prediction.

A narrow, auditable *categorical reference learner* fits P(state|stratum,context)
and P(state|stratum) from training-source rows. It generates all subsequent
calibration and validation probability fields from the actual fitted artifact
bytes, instead of accepting an arbitrary externally supplied probability field.

This does not rerun the historical BOP_RODENT random forest. It is intended
for controlled known-truth validation and prospectively designed new sources.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Sequence

from .fixed_group_gain_protocol import (
    FrozenGroupForecastPlan,
    FrozenGainCalibration,
    FrozenGainValidation,
    calibrate_fixed_group_gain,
    freeze_fixed_group_forecasts,
    validate_fixed_group_gain,
)


MODEL_KIND = "odsp-managed-stratum-context-categorical-v1"
REF_KIND = "odsp-managed-stratum-categorical-reference-v1"
_TRAIN_FIELDS = frozenset(
    ("row_id", "group_id", "stratum", "context", "outcome", "weight")
)
_FEATURE_FIELDS = frozenset(
    ("row_id", "group_id", "stratum", "context", "weight")
)


def _encode(payload: object) -> bytes:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _label(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field} must be a nonempty stripped string")
    return value


def _weight(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError("weight must be finite and positive")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("weight must be finite and positive") from exc
    if not math.isfinite(result) or result <= 0:
        raise ValueError("weight must be finite and positive")
    return result


@dataclass(frozen=True)
class ManagedTrainingRow:
    row_id: str
    group_id: str
    stratum: str
    context: int
    outcome: str
    weight: float

    def canonical(self) -> dict[str, object]:
        return {
            "row_id": self.row_id, "group_id": self.group_id,
            "stratum": self.stratum, "context": self.context,
            "outcome": self.outcome, "weight": self.weight,
        }


@dataclass(frozen=True)
class ManagedFeatureRow:
    row_id: str
    group_id: str
    stratum: str
    context: int
    weight: float

    def canonical(self) -> dict[str, object]:
        return {
            "row_id": self.row_id, "group_id": self.group_id,
            "stratum": self.stratum, "context": self.context,
            "weight": self.weight,
        }


def _rows(
    items: Sequence[Mapping[str, object]],
    *,
    training: bool,
) -> tuple[ManagedTrainingRow, ...] | tuple[ManagedFeatureRow, ...]:
    if isinstance(items, (str, bytes)) or not items:
        raise ValueError("all roles must contain non-empty row sequences")
    allowed = _TRAIN_FIELDS if training else _FEATURE_FIELDS
    required = allowed - {"weight"}
    parsed: list[ManagedTrainingRow | ManagedFeatureRow] = []
    seen: set[str] = set()
    for raw in items:
        if not isinstance(raw, Mapping) or not required.issubset(raw) or set(raw) - allowed:
            raise ValueError("row fields must match role schema exactly; no hidden outcomes")
        row_id = _label(raw["row_id"], "row_id")
        if row_id in seen:
            raise ValueError("duplicate row_id in role")
        seen.add(row_id)
        group = _label(raw["group_id"], "group_id")
        stratum = _label(raw["stratum"], "stratum")
        ctx = raw["context"]
        if type(ctx) is not int or ctx not in (0, 1):
            raise ValueError("context must be exact integer 0 or 1")
        weight = _weight(raw.get("weight", 1.0))
        if training:
            outcome = _label(raw["outcome"], "outcome")
            parsed.append(
                ManagedTrainingRow(row_id, group, stratum, ctx, outcome, weight)
            )
        else:
            parsed.append(ManagedFeatureRow(row_id, group, stratum, ctx, weight))
    return tuple(sorted(parsed, key=lambda row: row.row_id))


def _validate_classes(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("classes must contain two or more distinct labels")
    classes = tuple(_label(x, "class") for x in values)
    if len(classes) < 2 or len(classes) != len(set(classes)):
        raise ValueError("classes must contain two or more distinct labels")
    return classes


def _fit_artifacts(
    training: tuple[ManagedTrainingRow, ...],
    classes: tuple[str, ...],
    pseudocount: float,
) -> tuple[bytes, bytes, str]:
    if not math.isfinite(pseudocount) or pseudocount <= 0:
        raise ValueError("pseudocount must be finite and positive")
    class_idx = {name: i for i, name in enumerate(classes)}
    group_rows: dict[str, list[ManagedTrainingRow]] = {}
    group_strata: dict[str, str] = {}
    seen_groups_by_stratum: dict[str, set[str]] = {}
    for row in training:
        if row.outcome not in class_idx:
            raise ValueError("training outcome is not in frozen class labels")
        if row.group_id in group_strata and group_strata[row.group_id] != row.stratum:
            raise ValueError("training group crosses strata")
        group_strata[row.group_id] = row.stratum
        group_rows.setdefault(row.group_id, []).append(row)
        seen_groups_by_stratum.setdefault(row.stratum, set()).add(row.group_id)
    if any(len(groups) < 2 for groups in seen_groups_by_stratum.values()):
        raise ValueError("each training stratum needs at least two independent groups")

    k = len(classes)
    contexts = {
        stratum: [[0.0] * k for _ in range(2)]
        for stratum in seen_groups_by_stratum
    }
    pooled = {
        stratum: [0.0] * k for stratum in seen_groups_by_stratum
    }
    present_contexts = {
        stratum: set() for stratum in seen_groups_by_stratum
    }
    for group in sorted(group_rows):
        rows = group_rows[group]
        stratum = group_strata[group]
        total = math.fsum(row.weight for row in rows)
        for row in rows:
            # Exactly one unit of training weight per biological individual.
            weight = row.weight / total
            idx = class_idx[row.outcome]
            contexts[stratum][row.context][idx] += weight
            pooled[stratum][idx] += weight
            present_contexts[stratum].add(row.context)
    if any(choices != {0, 1} for choices in present_contexts.values()):
        raise ValueError("both context values require training support in each stratum")
    source_sha = _hash(_encode([row.canonical() for row in training]))

    conditional: dict[str, list[list[float]]] = {}
    reference: dict[str, list[float]] = {}
    for stratum in sorted(contexts):
        conditional[stratum] = [
            [
                (value + pseudocount) /
                (math.fsum(contexts[stratum][context]) + pseudocount * k)
                for value in contexts[stratum][context]
            ]
            for context in (0, 1)
        ]
        reference[stratum] = [
            (value + pseudocount) /
            (math.fsum(pooled[stratum]) + pseudocount * k)
            for value in pooled[stratum]
        ]
    common = {
        "schema_version": 1, "classes": list(classes),
        "training_source_sha256": source_sha,
        "training_weighting": "equal_mass_per_independent_group",
        "pseudocount": pseudocount,
    }
    model = _encode({
        **common, "kind": MODEL_KIND,
        "context_levels": [0, 1], "probabilities": conditional,
    })
    baseline = _encode({
        **common, "kind": REF_KIND, "probabilities": reference,
    })
    return model, baseline, source_sha


def _prob_vector(raw: object, k: int) -> tuple[float, ...]:
    if not isinstance(raw, list) or len(raw) != k or any(
        isinstance(x, bool) or not isinstance(x, (int, float)) for x in raw
    ):
        raise ValueError("artifact class probabilities have wrong shape")
    values = tuple(float(x) for x in raw)
    if any(not math.isfinite(x) or x <= 0.0 for x in values):
        raise ValueError("artifact probabilities must be strictly positive finite")
    if not math.isclose(math.fsum(values), 1.0, rel_tol=0, abs_tol=1e-8):
        raise ValueError("artifact class probabilities must sum to one")
    return values


def _decode_artifacts(
    model: bytes,
    reference: bytes,
    classes: tuple[str, ...],
    training_sha: str,
) -> tuple[dict[str, tuple[tuple[float, ...], ...]], dict[str, tuple[float, ...]]]:
    try:
        m = json.loads(model)
        b = json.loads(reference)
    except (ValueError, TypeError) as exc:
        raise ValueError("managed model/reference bytes must encode valid JSON") from exc
    if not isinstance(m, dict) or not isinstance(b, dict):
        raise ValueError("artifact format invalid")
    common_keys = {
        "schema_version", "classes", "training_source_sha256",
        "training_weighting", "pseudocount", "kind", "probabilities",
    }
    if (
        set(m) != common_keys | {"context_levels"}
        or set(b) != common_keys
        or m["schema_version"] != 1
        or b["schema_version"] != 1
        or m["kind"] != MODEL_KIND
        or b["kind"] != REF_KIND
        or m["context_levels"] != [0, 1]
        or m["classes"] != list(classes)
        or b["classes"] != list(classes)
        or m["training_source_sha256"] != training_sha
        or b["training_source_sha256"] != training_sha
        or m["training_weighting"] != "equal_mass_per_independent_group"
        or b["training_weighting"] != "equal_mass_per_independent_group"
        or not isinstance(m["pseudocount"], (float, int))
        or isinstance(m["pseudocount"], bool)
        or m["pseudocount"] != b["pseudocount"]
    ):
        raise ValueError("model/reference artifacts lack compatible training provenance")
    if not isinstance(m["probabilities"], dict) or not isinstance(b["probabilities"], dict):
        raise ValueError("artifact probabilities must be mapped by stratum")
    if set(m["probabilities"]) != set(b["probabilities"]):
        raise ValueError("model/reference disagree on stratum support")
    k = len(classes)
    table: dict[str, tuple[tuple[float, ...], ...]] = {}
    pool: dict[str, tuple[float, ...]] = {}
    for stratum in sorted(m["probabilities"]):
        by_ctx = m["probabilities"][stratum]
        if not isinstance(by_ctx, list) or len(by_ctx) != 2:
            raise ValueError("model context probability rows must number two")
        table[stratum] = (
            _prob_vector(by_ctx[0], k), _prob_vector(by_ctx[1], k)
        )
        pool[stratum] = _prob_vector(b["probabilities"][stratum], k)
    return table, pool


def _produce_forecast_rows(
    features: tuple[ManagedFeatureRow, ...],
    model: bytes,
    reference: bytes,
    classes: tuple[str, ...],
    source_sha: str,
) -> list[dict[str, object]]:
    table, pool = _decode_artifacts(model, reference, classes, source_sha)
    forecasts = []
    for row in features:
        if row.stratum not in table:
            raise ValueError("holdout stratum absent from training model")
        forecasts.append({
            "row_id": row.row_id,
            "group_id": row.group_id,
            "stratum": row.stratum,
            "conditional": table[row.stratum][row.context],
            "reference": pool[row.stratum],
            "weight": row.weight,
        })
    return forecasts


@dataclass(frozen=True)
class ManagedGroupForecast:
    """Owns the exact training source, scored features, model and frozen plan."""

    training_rows: tuple[ManagedTrainingRow, ...]
    calibration_features: tuple[ManagedFeatureRow, ...]
    validation_features: tuple[ManagedFeatureRow, ...]
    classes: tuple[str, ...]
    pseudocount: float
    model_artifact: bytes
    reference_artifact: bytes
    plan: FrozenGroupForecastPlan
    feature_sha256: str

    def assert_replayed(self) -> None:
        model, reference, sha = _fit_artifacts(
            self.training_rows, self.classes, self.pseudocount
        )
        if model != self.model_artifact or reference != self.reference_artifact:
            raise ValueError("managed model/source retraining replay mismatch")
        if sha != self.plan.training_source_sha256:
            raise ValueError("managed training source SHA mismatch")
        roles = {
            "calibration": [r.canonical() for r in self.calibration_features],
            "validation": [r.canonical() for r in self.validation_features],
        }
        if _hash(_encode(roles)) != self.feature_sha256:
            raise ValueError("frozen feature roster modified")
        cal = _produce_forecast_rows(
            self.calibration_features, model, reference, self.classes, sha
        )
        val = _produce_forecast_rows(
            self.validation_features, model, reference, self.classes, sha
        )
        replay = freeze_fixed_group_forecasts(
            training_group_ids=sorted({r.group_id for r in self.training_rows}),
            calibration_forecasts=cal,
            validation_forecasts=val,
            classes=self.classes,
            model_artifact=model,
            reference_artifact=reference,
            training_source_sha256=sha,
            miscoverage=self.plan.miscoverage,
        )
        self.plan.assert_unchanged(
            model_artifact=self.model_artifact,
            reference_artifact=self.reference_artifact,
        )
        if replay.digest != self.plan.digest:
            raise ValueError("managed artifact-to-forecast replay mismatch")

    def public_manifest(self) -> dict[str, object]:
        self.assert_replayed()
        return {
            **self.plan.public_manifest(),
            "managed_learner": MODEL_KIND,
            "feature_roster_sha256": self.feature_sha256,
            "artifact_to_forecast_replay_verified": True,
            "training_source_to_model_replay_verified": True,
            "external_chronology_attested": False,
            "independent_external_evidence_collected": False,
        }


def freeze_managed_group_forecasts(
    *,
    training_rows: Sequence[Mapping[str, object]],
    calibration_features: Sequence[Mapping[str, object]],
    validation_features: Sequence[Mapping[str, object]],
    classes: Sequence[str],
    pseudocount: float = 0.1,
    miscoverage: float = 0.1,
) -> ManagedGroupForecast:
    """Fit training-only categorical reference and derive all holdout forecasts.

    This is an executed reference learner, not a generic trust assertion about
    random-forest or externally provided model-prediction binding.
    """
    training = _rows(training_rows, training=True)
    calibration = _rows(calibration_features, training=False)
    validation = _rows(validation_features, training=False)
    labels = _validate_classes(classes)
    if len({
        x.row_id for x in training + calibration + validation
    }) != len(training) + len(calibration) + len(validation):
        raise ValueError("training/calibration/validation row_id rosters overlap")
    if isinstance(pseudocount, bool):
        raise ValueError("pseudocount must be finite and positive")
    try:
        smoothing = float(pseudocount)
    except (TypeError, ValueError) as exc:
        raise ValueError("pseudocount must be finite and positive") from exc
    model, ref, source_sha = _fit_artifacts(training, labels, smoothing)
    cal = _produce_forecast_rows(calibration, model, ref, labels, source_sha)
    val = _produce_forecast_rows(validation, model, ref, labels, source_sha)
    plan = freeze_fixed_group_forecasts(
        training_group_ids=sorted({r.group_id for r in training}),
        calibration_forecasts=cal,
        validation_forecasts=val,
        classes=labels,
        model_artifact=model,
        reference_artifact=ref,
        training_source_sha256=source_sha,
        miscoverage=miscoverage,
    )
    features = {
        "calibration": [r.canonical() for r in calibration],
        "validation": [r.canonical() for r in validation],
    }
    result = ManagedGroupForecast(
        training_rows=training,
        calibration_features=calibration,
        validation_features=validation,
        classes=labels,
        pseudocount=smoothing,
        model_artifact=model,
        reference_artifact=ref,
        plan=plan,
        feature_sha256=_hash(_encode(features)),
    )
    result.assert_replayed()
    return result


def calibrate_managed_group_gain(
    frozen: ManagedGroupForecast,
    calibration_outcomes: Mapping[str, str],
) -> FrozenGainCalibration:
    """Reproduce model/forecast binding before consuming calibration outcomes."""
    frozen.assert_replayed()
    return calibrate_fixed_group_gain(
        frozen.plan, calibration_outcomes,
        model_artifact=frozen.model_artifact,
        reference_artifact=frozen.reference_artifact,
    )


def validate_managed_group_gain(
    frozen: ManagedGroupForecast,
    calibration: FrozenGainCalibration,
    validation_outcomes: Mapping[str, str],
) -> FrozenGainValidation:
    """Reproduce complete binding before scoring untouched validation outcomes."""
    frozen.assert_replayed()
    return validate_fixed_group_gain(
        frozen.plan, calibration, validation_outcomes,
        model_artifact=frozen.model_artifact,
        reference_artifact=frozen.reference_artifact,
    )
