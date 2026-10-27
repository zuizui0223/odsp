"""Outcome-blind, fixed-forecast, independent-group transfer-gain validation.

Freeze fitted predictor/reference *bytes* and their outcome-blind probability
forecasts for all calibration and validation rows before reading either
group's outcomes. Score one mean log probability gain per group. A finite-
sample lower rank bound is fit ONLY on calibration groups and tested on
disjoint validation groups, within declared strata.

A hash guarantees consistency with the submitted artifacts; it cannot attest
that external predictions were really produced by those artifacts, or that
the freeze chronologically preceded human access to biological outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Mapping, Sequence

from .new_group_gain_envelope import fit_new_group_gain_lower_envelope


_HEX256 = re.compile(r"^[0-9a-f]{64}$")
_FORECAST_FIELDS = frozenset(
    {"row_id", "group_id", "stratum", "conditional", "reference", "weight"}
)


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _unique_labels(values: Sequence[str], what: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{what} must be a sequence of non-empty identifiers")
    labels = tuple(values)
    if not labels or any(not isinstance(x, str) or not x.strip() or x != x.strip()
                         for x in labels):
        raise ValueError(f"{what} must contain non-empty, stripped string identifiers")
    if len(set(labels)) != len(labels):
        raise ValueError(f"{what} contains duplicates")
    return labels


def _parse_probabilities(values: object, k: int, name: str) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must provide k finite probabilities")
    try:
        raw = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must provide k finite probabilities") from exc
    if len(raw) != k or any(isinstance(x, bool) for x in raw):
        raise ValueError(f"{name} must provide k strictly positive probabilities")
    try:
        p = tuple(float(x) for x in raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain finite numeric probabilities") from exc
    if any(not math.isfinite(x) or x <= 0 or x > 1 for x in p):
        raise ValueError(f"{name} must contain strictly positive finite probabilities")
    if not math.isclose(math.fsum(p), 1.0, abs_tol=1e-8, rel_tol=0.0):
        raise ValueError(f"{name} probabilities must sum to one")
    return p


@dataclass(frozen=True)
class FrozenForecastRow:
    role: str
    row_id: str
    group_id: str
    stratum: str
    conditional: tuple[float, ...]
    reference: tuple[float, ...]
    weight: float

    def canonical(self) -> dict[str, object]:
        return {
            "role": self.role, "row_id": self.row_id,
            "group_id": self.group_id, "stratum": self.stratum,
            "conditional": list(self.conditional),
            "reference": list(self.reference), "weight": self.weight,
        }


@dataclass(frozen=True)
class FrozenGroupForecastPlan:
    """Committed prediction roster. Contains no realized calibration/validation states."""

    training_group_ids: tuple[str, ...]
    classes: tuple[str, ...]
    calibration_rows: tuple[FrozenForecastRow, ...]
    validation_rows: tuple[FrozenForecastRow, ...]
    model_sha256: str
    reference_sha256: str
    training_source_sha256: str
    miscoverage: float
    digest: str

    def canonical(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "training_group_ids": list(self.training_group_ids),
            "classes": list(self.classes),
            "calibration_forecasts": [r.canonical() for r in self.calibration_rows],
            "validation_forecasts": [r.canonical() for r in self.validation_rows],
            "model_sha256": self.model_sha256,
            "reference_sha256": self.reference_sha256,
            "training_source_sha256": self.training_source_sha256,
            "miscoverage": self.miscoverage,
            "score": "group_mean_true_state_log_conditional_minus_log_reference",
            "gain_orientation": "higher_is_better",
        }

    def assert_unchanged(self, *, model_artifact: bytes, reference_artifact: bytes) -> None:
        if _digest(self.canonical()) != self.digest:
            raise ValueError("frozen forecast plan contents changed after freeze")
        _assert_artifact(model_artifact, self.model_sha256, "model")
        _assert_artifact(reference_artifact, self.reference_sha256, "reference")

    def public_manifest(self) -> dict[str, object]:
        """No animal IDs or per-row forecast probabilities in public summary."""
        return {
            "schema_version": 1, "plan_sha256": self.digest,
            "model_sha256": self.model_sha256,
            "reference_sha256": self.reference_sha256,
            "training_source_sha256": self.training_source_sha256,
            "training_group_count": len(self.training_group_ids),
            "calibration_row_count": len(self.calibration_rows),
            "validation_row_count": len(self.validation_rows),
            "calibration_group_count": len({r.group_id for r in self.calibration_rows}),
            "validation_group_count": len({r.group_id for r in self.validation_rows}),
            "strata": sorted({r.stratum for r in self.calibration_rows}),
            "outcomes_accessed_by_freeze": False,
            "chronology_and_artifact_to_prediction_binding_attested_externally": False,
        }


@dataclass(frozen=True)
class IndividualGroupGain:
    group_id: str
    stratum: str
    row_count: int
    weighted_mean_gain: float


@dataclass(frozen=True)
class FrozenGainCalibration:
    plan_sha256: str
    gains: tuple[IndividualGroupGain, ...]
    calibration_sha256: str


@dataclass(frozen=True)
class StratumValidation:
    stratum: str
    calibration_group_count: int
    validation_group_count: int
    finite_rank: int
    bound: float
    vacuous: bool
    conservative_rank_coverage_if_exchangeable: float
    observed_group_coverage: float
    positive_validation_group_count: int

    def as_public_dict(self) -> dict[str, object]:
        return {
            "stratum": self.stratum,
            "calibration_group_count": self.calibration_group_count,
            "validation_group_count": self.validation_group_count,
            "finite_rank": self.finite_rank,
            "bound": None if self.vacuous else self.bound,
            "vacuous": self.vacuous,
            "conservative_rank_coverage_if_exchangeable": self.conservative_rank_coverage_if_exchangeable,
            "observed_group_coverage": self.observed_group_coverage,
            "positive_validation_group_count": self.positive_validation_group_count,
        }


@dataclass(frozen=True)
class FrozenGainValidation:
    plan_sha256: str
    calibration_sha256: str
    strata: tuple[StratumValidation, ...]
    covered_validation_group_count: int
    validation_group_count: int
    group_equal_coverage: float
    exchangeability_verified_by_software: bool = False

    def as_public_dict(self) -> dict[str, object]:
        return {
            "plan_sha256": self.plan_sha256,
            "calibration_sha256": self.calibration_sha256,
            "strata": [row.as_public_dict() for row in self.strata],
            "covered_validation_group_count": self.covered_validation_group_count,
            "validation_group_count": self.validation_group_count,
            "group_equal_coverage": self.group_equal_coverage,
            "exchangeability_verified_by_software": False,
            "claim_boundary": (
                "rank coverage is conditional on externally justified exchangeable "
                "independent group gains for one frozen predictor/reference"
            ),
            "historical_bop_terminal_changed": False,
        }


def _assert_artifact(payload: bytes, expected_sha: str, label: str) -> None:
    if not isinstance(payload, bytes) or not payload:
        raise ValueError(f"{label} artifact must be non-empty bytes")
    if hashlib.sha256(payload).hexdigest() != expected_sha:
        raise ValueError(f"frozen {label} artifact hash mismatch")


def _parse_rows(
    entries: Sequence[Mapping[str, object]],
    *,
    role: str,
    k: int,
) -> tuple[FrozenForecastRow, ...]:
    if not entries or isinstance(entries, (str, bytes)):
        raise ValueError(f"{role} forecasts must contain at least one row")
    rows: list[FrozenForecastRow] = []
    for index, raw in enumerate(entries):
        if not isinstance(raw, Mapping):
            raise ValueError(f"{role} forecast row must be a mapping")
        if set(raw) - _FORECAST_FIELDS or _FORECAST_FIELDS.difference(raw) - {"weight"}:
            raise ValueError("unexpected/missing forecast fields: outcomes must not be frozen")
        ids: list[str] = []
        for field in ("row_id", "group_id", "stratum"):
            value = raw[field]
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{role} {field} must be a non-empty stripped string")
            ids.append(value)
        weight_raw = raw.get("weight", 1.0)
        if isinstance(weight_raw, bool):
            raise ValueError("frozen row weight must be finite and strictly positive")
        try:
            weight = float(weight_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("frozen row weight must be numeric") from exc
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError("frozen row weight must be finite and strictly positive")
        rows.append(
            FrozenForecastRow(
                role=role, row_id=ids[0], group_id=ids[1], stratum=ids[2],
                conditional=_parse_probabilities(raw["conditional"], k, f"{role}[{index}].conditional"),
                reference=_parse_probabilities(raw["reference"], k, f"{role}[{index}].reference"),
                weight=weight,
            )
        )
    return tuple(rows)


def freeze_fixed_group_forecasts(
    *,
    training_group_ids: Sequence[str],
    calibration_forecasts: Sequence[Mapping[str, object]],
    validation_forecasts: Sequence[Mapping[str, object]],
    classes: Sequence[str],
    model_artifact: bytes,
    reference_artifact: bytes,
    training_source_sha256: str,
    miscoverage: float = 0.1,
) -> FrozenGroupForecastPlan:
    """Freeze forecasts BEFORE observing calibration and validation outcomes.

    Model/reference artifacts are identified by their actual bytes. All
    supplied forecasts are content-hashed in an immutable canonical plan;
    their production by the artifacts is a separate upstream attestation.
    """
    train = _unique_labels(training_group_ids, "training_group_ids")
    labels = _unique_labels(classes, "classes")
    if len(labels) < 2:
        raise ValueError("classes must include at least two states")
    if not isinstance(training_source_sha256, str) or not _HEX256.fullmatch(training_source_sha256):
        raise ValueError("training_source_sha256 must be a lowercase SHA256 hex digest")
    if isinstance(miscoverage, bool):
        raise ValueError("miscoverage must be between zero and one")
    try:
        alpha = float(miscoverage)
    except (ValueError, TypeError) as exc:
        raise ValueError("miscoverage must be numeric") from exc
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("miscoverage must be between zero and one")
    if not isinstance(model_artifact, bytes) or not model_artifact:
        raise ValueError("model artifact must be non-empty bytes")
    if not isinstance(reference_artifact, bytes) or not reference_artifact:
        raise ValueError("reference artifact must be non-empty bytes")
    calibration = _parse_rows(calibration_forecasts, role="calibration", k=len(labels))
    validation = _parse_rows(validation_forecasts, role="validation", k=len(labels))
    allrows = calibration + validation
    if len(set(row.row_id for row in allrows)) != len(allrows):
        raise ValueError("duplicate row_id between or within outcome-independent roles")
    assignments: dict[str, tuple[str, str]] = {}
    for row in allrows:
        new = (row.role, row.stratum)
        if row.group_id in assignments and assignments[row.group_id] != new:
            raise ValueError("one group cannot cross calibration, validation or stratum")
        assignments[row.group_id] = new
    if set(assignments) & set(train):
        raise ValueError("training group overlaps calibration or validation")
    cal_strata = {row.stratum for row in calibration}
    val_strata = {row.stratum for row in validation}
    if not val_strata.issubset(cal_strata):
        raise ValueError("validation stratum without calibration groups: no pooled fallback")
    # A stratum must be deliberately declared on each group. Do not silently
    # share the lower bound across species/populations with different supports.
    plan = FrozenGroupForecastPlan(
        training_group_ids=train,
        classes=labels,
        calibration_rows=calibration,
        validation_rows=validation,
        model_sha256=hashlib.sha256(model_artifact).hexdigest(),
        reference_sha256=hashlib.sha256(reference_artifact).hexdigest(),
        training_source_sha256=training_source_sha256,
        miscoverage=alpha,
        digest="",
    )
    object.__setattr__(plan, "digest", _digest(plan.canonical()))
    return plan


def _group_scores(
    rows: tuple[FrozenForecastRow, ...],
    outcomes: Mapping[str, str],
    classes: tuple[str, ...],
) -> tuple[IndividualGroupGain, ...]:
    if not isinstance(outcomes, Mapping) or set(outcomes) != {row.row_id for row in rows}:
        raise ValueError("outcome row IDs must match exactly this frozen role; no missing/extra rows")
    lookup = {label: i for i, label in enumerate(classes)}
    grouped: dict[str, list[tuple[FrozenForecastRow, float]]] = {}
    for row in rows:
        observed = outcomes[row.row_id]
        if not isinstance(observed, str) or observed not in lookup:
            raise ValueError("observed state was absent from frozen classes")
        i = lookup[observed]
        gain = math.log(row.conditional[i]) - math.log(row.reference[i])
        grouped.setdefault(row.group_id, []).append((row, gain))
    result: list[IndividualGroupGain] = []
    for group in sorted(grouped):
        item = grouped[group]
        weighted_gain = math.fsum(r.weight * delta for r, delta in item)
        total_weight = math.fsum(r.weight for r, _ in item)
        result.append(
            IndividualGroupGain(
                group_id=group,
                stratum=item[0][0].stratum,
                row_count=len(item),
                weighted_mean_gain=weighted_gain / total_weight,
            )
        )
    return tuple(result)


def _calibration_digest(
    plan_sha: str,
    gains: tuple[IndividualGroupGain, ...],
) -> str:
    return _digest({
        "plan_sha256": plan_sha,
        "group_gains": [
            {
                "group_id": row.group_id,
                "stratum": row.stratum,
                "row_count": row.row_count,
                "weighted_mean_gain": row.weighted_mean_gain,
            }
            for row in gains
        ],
    })


def calibrate_fixed_group_gain(
    plan: FrozenGroupForecastPlan,
    calibration_outcomes: Mapping[str, str],
    *,
    model_artifact: bytes,
    reference_artifact: bytes,
) -> FrozenGainCalibration:
    """Consume calibration-role labels; final validation labels are not accepted."""
    plan.assert_unchanged(model_artifact=model_artifact, reference_artifact=reference_artifact)
    gains = _group_scores(plan.calibration_rows, calibration_outcomes, plan.classes)
    return FrozenGainCalibration(
        plan_sha256=plan.digest,
        gains=gains,
        calibration_sha256=_calibration_digest(plan.digest, gains),
    )


def validate_fixed_group_gain(
    plan: FrozenGroupForecastPlan,
    calibration: FrozenGainCalibration,
    validation_outcomes: Mapping[str, str],
    *,
    model_artifact: bytes,
    reference_artifact: bytes,
) -> FrozenGainValidation:
    """Evaluate the *unchanged* calibrator against untouched validation groups."""
    plan.assert_unchanged(model_artifact=model_artifact, reference_artifact=reference_artifact)
    if calibration.plan_sha256 != plan.digest:
        raise ValueError("calibration was created from a different frozen plan")
    if calibration.calibration_sha256 != _calibration_digest(plan.digest, calibration.gains):
        raise ValueError("frozen calibration group scores changed")
    expected_calibration = {
        row.group_id: row.stratum for row in plan.calibration_rows
    }
    if (
        len(calibration.gains) != len(expected_calibration)
        or {row.group_id: row.stratum for row in calibration.gains} != expected_calibration
    ):
        raise ValueError("calibration group roster disagrees with frozen plan")
    tested = _group_scores(plan.validation_rows, validation_outcomes, plan.classes)
    summaries: list[StratumValidation] = []
    total_covered = 0
    for stratum in sorted(set(row.stratum for row in tested)):
        cal = [row for row in calibration.gains if row.stratum == stratum]
        val = [row for row in tested if row.stratum == stratum]
        envelope = fit_new_group_gain_lower_envelope(
            [row.weighted_mean_gain for row in cal],
            [row.group_id for row in cal],
            miscoverage=plan.miscoverage,
            source_design="fixed_predictor_groups",
        )
        covered = sum(
            envelope.covers_new_group(row.group_id, row.weighted_mean_gain)
            for row in val
        )
        total_covered += covered
        summaries.append(
            StratumValidation(
                stratum=stratum,
                calibration_group_count=len(cal),
                validation_group_count=len(val),
                finite_rank=envelope.finite_sample_rank,
                bound=envelope.lower_gain_bound,
                vacuous=envelope.bound_is_vacuous,
                conservative_rank_coverage_if_exchangeable=envelope.conservative_coverage_if_exchangeable,
                observed_group_coverage=covered / len(val),
                positive_validation_group_count=sum(
                    row.weighted_mean_gain > 0 for row in val
                ),
            )
        )
    return FrozenGainValidation(
        plan_sha256=plan.digest,
        calibration_sha256=calibration.calibration_sha256,
        strata=tuple(summaries),
        covered_validation_group_count=total_covered,
        validation_group_count=len(tested),
        group_equal_coverage=total_covered / len(tested),
    )
