"""Frozen empirical N2 bat thickness calculations.

This module implements the estimand frozen in ``N2_BAT_THICKNESS_CONTRACT.json``.
It is intentionally model-pool/sealed aware and gives individual bats equal
weight.  Source I/O lives outside this module so the scientific calculations can
be tested on synthetic data before the one-shot empirical outcome is opened.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import bisect
import hashlib
import math
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np

from .n2_bat_preflight import deterministic_individual_split
from .niche_geometry import axis_thickness_map, niche_thickness_profile

Cell = tuple[int, int]


@dataclass(frozen=True)
class SealedIndividualScore:
    individual_id: str
    scored_event_count: int
    mean_log_score_gain: float | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ThicknessConfigurationResult:
    cell_size_m: float
    z_edges: tuple[float, ...]
    eligible_cell_count: int
    model_individual_count_with_eligible_events: int
    sealed_individual_count: int
    information_nats: float | None
    effective_vertical_states: float | None
    local_cells: tuple[dict[str, object], ...]
    sealed_scores: tuple[SealedIndividualScore, ...]
    sealed_mean_log_score_gain: float | None
    answer_check_category: str
    evaluable: bool
    unavailable_reasons: tuple[str, ...]
    fingerprint: str

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["sealed_scores"] = [score.as_dict() for score in self.sealed_scores]
        payload["local_cells"] = list(self.local_cells)
        return payload


def _text(row: Mapping[str, object], key: str) -> str:
    value = row.get(key)
    return "" if value is None else str(value).strip()


def individual_id(row: Mapping[str, object]) -> str:
    value = _text(row, "individual_local_identifier") or _text(row, "individual_id")
    if not value:
        raise ValueError("event lacks individual identifier")
    return value


def finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def xy_value(row: Mapping[str, object]) -> tuple[float, float] | None:
    lat = finite_float(row.get("location_lat"))
    lon = finite_float(row.get("location_long"))
    if lat is None or lon is None:
        return None
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None
    return lon, lat


def height_present(row: Mapping[str, object], height_field: str) -> bool:
    return bool(_text(row, height_field))


def numeric_height(row: Mapping[str, object], height_field: str) -> float | None:
    return finite_float(row.get(height_field))


def height_bin_index(value: float, edges: Sequence[float]) -> int:
    """Assign a finite z value to left-closed/right-open fixed bins."""

    fixed = tuple(float(edge) for edge in edges)
    if len(fixed) < 2 or not all(a < b for a, b in zip(fixed, fixed[1:])):
        raise ValueError("z edges must be strictly increasing")
    if not math.isinf(fixed[0]) or fixed[0] >= 0:
        raise ValueError("first z edge must be -inf")
    if not math.isinf(fixed[-1]) or fixed[-1] <= 0:
        raise ValueError("last z edge must be +inf")
    if not math.isfinite(value):
        raise ValueError("z value must be finite")
    return bisect.bisect_right(fixed[1:-1], float(value))


def _cell_for_row(
    row: Mapping[str, object],
    *,
    projector: Callable[[float, float], tuple[float, float]],
    cell_size_m: float,
) -> Cell | None:
    xy = xy_value(row)
    if xy is None:
        return None
    easting, northing = projector(*xy)
    if not (math.isfinite(easting) and math.isfinite(northing)):
        raise ValueError("projector returned non-finite coordinates")
    return (math.floor(easting / cell_size_m), math.floor(northing / cell_size_m))


def _is_marked_outlier(row: Mapping[str, object]) -> bool:
    value = _text(row, "manually_marked_outlier").lower()
    if value in {"", "false", "0", "no", "n", "f"}:
        return False
    if value in {"true", "1", "yes", "y", "t"}:
        return True
    raise ValueError(f"unsupported manually_marked_outlier value: {value!r}")


def structural_eligible_cells(
    rows: Sequence[Mapping[str, object]],
    *,
    height_field: str,
    projector: Callable[[float, float], tuple[float, float]],
    cell_size_m: float,
    minimum_events_per_cell: int,
    minimum_distinct_model_individuals_per_cell: int,
    split: Mapping[str, str] | None = None,
) -> tuple[set[Cell], dict[str, str]]:
    """Reproduce the frozen model-pool-only structural cell gate.

    Height is inspected only for presence/non-missingness here, not numerically.
    """

    if not rows:
        raise ValueError("event stream is empty")
    if cell_size_m <= 0:
        raise ValueError("cell_size_m must be positive")
    if split is None:
        split = deterministic_individual_split(individual_id(row) for row in rows)
    buckets: dict[Cell, dict[str, object]] = {}
    for row in rows:
        iid = individual_id(row)
        if split.get(iid) != "model" or not height_present(row, height_field):
            continue
        cell = _cell_for_row(row, projector=projector, cell_size_m=cell_size_m)
        if cell is None:
            continue
        bucket = buckets.setdefault(cell, {"events": 0, "individuals": set()})
        bucket["events"] = int(bucket["events"]) + 1
        bucket["individuals"].add(iid)
    eligible = {
        cell
        for cell, bucket in buckets.items()
        if int(bucket["events"]) >= int(minimum_events_per_cell)
        and len(bucket["individuals"]) >= int(minimum_distinct_model_individuals_per_cell)
    }
    return eligible, dict(split)


def finite_height_fraction_among_structural_joint_events(
    rows: Sequence[Mapping[str, object]],
    *,
    height_field: str,
) -> tuple[int, int, float | None]:
    denominator = 0
    numerator = 0
    for row in rows:
        if xy_value(row) is None or not height_present(row, height_field):
            continue
        denominator += 1
        if numeric_height(row, height_field) is not None:
            numerator += 1
    fraction = None if denominator == 0 else numerator / denominator
    return numerator, denominator, fraction


def _z_counts(
    rows: Iterable[Mapping[str, object]],
    *,
    height_field: str,
    z_edges: Sequence[float],
) -> np.ndarray:
    counts = np.zeros(len(z_edges) - 1, dtype=float)
    for row in rows:
        value = numeric_height(row, height_field)
        if value is None:
            continue
        counts[height_bin_index(value, z_edges)] += 1.0
    return counts


def _smoothed_probability(counts: np.ndarray, alpha: float) -> np.ndarray:
    if alpha <= 0:
        raise ValueError("Jeffreys alpha must be positive")
    values = np.asarray(counts, dtype=float) + float(alpha)
    return values / float(values.sum())


def _configuration_fingerprint(payload: dict[str, object]) -> str:
    def convert(value: object) -> object:
        if isinstance(value, float):
            if math.isnan(value):
                return "nan"
            if math.isinf(value):
                return "inf" if value > 0 else "-inf"
            return round(value, 15)
        if isinstance(value, dict):
            return {str(k): convert(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
        if isinstance(value, (list, tuple)):
            return [convert(v) for v in value]
        return value

    import json

    data = json.dumps(convert(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def evaluate_thickness_configuration(
    rows: Sequence[Mapping[str, object]],
    *,
    height_field: str,
    projector: Callable[[float, float], tuple[float, float]],
    cell_size_m: float,
    z_edges: Sequence[float],
    minimum_events_per_cell: int = 30,
    minimum_distinct_model_individuals_per_cell: int = 3,
    minimum_scored_events_per_sealed_individual: int = 30,
    jeffreys_alpha: float = 0.5,
    split: Mapping[str, str] | None = None,
    fixed_eligible_cells: set[Cell] | None = None,
    exclude_marked_outliers: bool = False,
) -> ThicknessConfigurationResult:
    """Evaluate one predeclared grid/bin configuration.

    When ``fixed_eligible_cells`` is supplied (bin/outlier sensitivity), those
    cells are retained rather than reselected.  Grid sensitivities omit it and
    recompute structural eligibility using the same frozen rules.
    """

    if split is None:
        split = deterministic_individual_split(individual_id(row) for row in rows)
    split = dict(split)
    eligible_cells = (
        set(fixed_eligible_cells)
        if fixed_eligible_cells is not None
        else structural_eligible_cells(
            rows,
            height_field=height_field,
            projector=projector,
            cell_size_m=cell_size_m,
            minimum_events_per_cell=minimum_events_per_cell,
            minimum_distinct_model_individuals_per_cell=minimum_distinct_model_individuals_per_cell,
            split=split,
        )[0]
    )
    unavailable: list[str] = []
    if not eligible_cells:
        unavailable.append("no_frozen_eligible_cells")

    # Cache only categorical/scoring state. Numeric height values never leave
    # this function in the result.
    model_by_individual_cell: dict[str, dict[Cell, list[int]]] = {}
    sealed_events: dict[str, list[tuple[Cell, int]]] = {}
    for row in rows:
        if exclude_marked_outliers and _is_marked_outlier(row):
            continue
        iid = individual_id(row)
        cell = _cell_for_row(row, projector=projector, cell_size_m=cell_size_m)
        if cell is None or cell not in eligible_cells:
            continue
        value = numeric_height(row, height_field)
        if value is None:
            continue
        zbin = height_bin_index(value, z_edges)
        if split.get(iid) == "model":
            model_by_individual_cell.setdefault(iid, {}).setdefault(cell, []).append(zbin)
        elif split.get(iid) == "sealed":
            sealed_events.setdefault(iid, []).append((cell, zbin))

    model_ids = sorted(
        iid for iid, cell_map in model_by_individual_cell.items() if any(cell_map.values())
    )
    if not model_ids:
        unavailable.append("no_model_individual_with_finite_height_in_eligible_cells")

    k = len(z_edges) - 1
    pxy: dict[Cell, float] = {cell: 0.0 for cell in eligible_cells}
    if model_ids:
        for iid in model_ids:
            cell_map = model_by_individual_cell[iid]
            total = sum(len(values) for values in cell_map.values())
            if total <= 0:
                continue
            for cell, values in cell_map.items():
                pxy[cell] += (len(values) / total) / len(model_ids)

    pz_conditional: dict[Cell, np.ndarray] = {}
    local_individual_counts: dict[Cell, int] = {}
    for cell in sorted(eligible_cells):
        individual_probs: list[np.ndarray] = []
        for iid in model_ids:
            zbins = model_by_individual_cell.get(iid, {}).get(cell, [])
            if not zbins:
                continue
            counts = np.bincount(zbins, minlength=k).astype(float)
            individual_probs.append(_smoothed_probability(counts, jeffreys_alpha))
        local_individual_counts[cell] = len(individual_probs)
        if len(individual_probs) < minimum_distinct_model_individuals_per_cell:
            unavailable.append(
                f"cell_{cell[0]}:{cell[1]}_has_too_few_finite_height_model_individuals"
            )
            continue
        pz_conditional[cell] = np.mean(np.stack(individual_probs), axis=0)

    # The frozen cell set may not be silently reduced after numeric outcomes are
    # opened. Any finite-height support failure therefore makes this configuration
    # not evaluable rather than selecting a more convenient subset.
    if set(pz_conditional) != set(eligible_cells):
        unavailable.append("finite_height_support_does_not_cover_all_frozen_eligible_cells")

    pz_marginal: np.ndarray | None = None
    if model_ids:
        individual_marginals: list[np.ndarray] = []
        for iid in model_ids:
            all_bins = [
                zbin
                for cell_bins in model_by_individual_cell[iid].values()
                for zbin in cell_bins
            ]
            if not all_bins:
                continue
            counts = np.bincount(all_bins, minlength=k).astype(float)
            individual_marginals.append(_smoothed_probability(counts, jeffreys_alpha))
        if individual_marginals:
            pz_marginal = np.mean(np.stack(individual_marginals), axis=0)

    information = None
    effective = None
    local_cells: tuple[dict[str, object], ...] = ()
    if not unavailable and pz_marginal is not None:
        ordered_cells = sorted(eligible_cells)
        support = np.zeros((len(ordered_cells), 1, k), dtype=float)
        for index, cell in enumerate(ordered_cells):
            support[index, 0, :] = pxy[cell] * pz_conditional[cell]
        total = float(support.sum())
        if not np.isclose(total, 1.0, rtol=1e-9, atol=1e-12):
            if total <= 0:
                unavailable.append("joint_support_has_no_mass")
            else:
                support /= total
        if not unavailable:
            profile = niche_thickness_profile(
                support,
                horizontal_axes=(0, 1),
                vertical_axis=2,
            )
            thickness_map = axis_thickness_map(
                support,
                horizontal_axes=(0, 1),
                added_axes=(2,),
            )
            information = float(profile.vertical_information_nats)
            effective = float(profile.effective_vertical_states)
            local = []
            for index, cell in enumerate(ordered_cells):
                local.append(
                    {
                        "cell_id": f"{cell[0]}:{cell[1]}",
                        "model_individual_count": int(local_individual_counts[cell]),
                        "horizontal_mass": float(thickness_map.horizontal_mass[index, 0]),
                        "information_nats": float(thickness_map.information_nats[index, 0]),
                        "effective_states": float(thickness_map.effective_states[index, 0]),
                    }
                )
            local_cells = tuple(local)

    sealed_ids = sorted(iid for iid, role in split.items() if role == "sealed")
    sealed_scores: list[SealedIndividualScore] = []
    gains: list[float] = []
    coverage_pass = True
    if not unavailable and pz_marginal is not None:
        for iid in sealed_ids:
            events = sealed_events.get(iid, [])
            if len(events) < minimum_scored_events_per_sealed_individual:
                coverage_pass = False
                sealed_scores.append(
                    SealedIndividualScore(
                        individual_id=iid,
                        scored_event_count=len(events),
                        mean_log_score_gain=None,
                    )
                )
                continue
            values = [
                math.log(float(pz_conditional[cell][zbin]))
                - math.log(float(pz_marginal[zbin]))
                for cell, zbin in events
            ]
            gain = float(np.mean(values))
            gains.append(gain)
            sealed_scores.append(
                SealedIndividualScore(
                    individual_id=iid,
                    scored_event_count=len(events),
                    mean_log_score_gain=gain,
                )
            )
    else:
        coverage_pass = False
        for iid in sealed_ids:
            sealed_scores.append(
                SealedIndividualScore(
                    individual_id=iid,
                    scored_event_count=len(sealed_events.get(iid, [])),
                    mean_log_score_gain=None,
                )
            )

    if unavailable or not coverage_pass or len(gains) != len(sealed_ids):
        answer_category = "empirical_thickness_answer_check_unavailable"
        evaluable = False
        if not coverage_pass:
            unavailable.append("sealed_scoring_coverage_failed")
    elif all(value > 0.0 for value in gains):
        answer_category = "estimable_and_generalizing"
        evaluable = True
    elif all(value <= 0.0 for value in gains):
        answer_category = "estimable_but_non_generalizing"
        evaluable = True
    else:
        answer_category = "estimable_but_generalization_mixed"
        evaluable = True

    sealed_mean = None if len(gains) != len(sealed_ids) or not gains else float(np.mean(gains))
    payload = {
        "cell_size_m": float(cell_size_m),
        "z_edges": [float(value) for value in z_edges],
        "eligible_cells": [f"{cell[0]}:{cell[1]}" for cell in sorted(eligible_cells)],
        "model_ids": model_ids,
        "sealed_ids": sealed_ids,
        "information_nats": information,
        "effective_vertical_states": effective,
        "sealed_scores": [score.as_dict() for score in sealed_scores],
        "answer_check_category": answer_category,
        "unavailable_reasons": sorted(set(unavailable)),
    }
    return ThicknessConfigurationResult(
        cell_size_m=float(cell_size_m),
        z_edges=tuple(float(value) for value in z_edges),
        eligible_cell_count=len(eligible_cells),
        model_individual_count_with_eligible_events=len(model_ids),
        sealed_individual_count=len(sealed_ids),
        information_nats=information,
        effective_vertical_states=effective,
        local_cells=local_cells,
        sealed_scores=tuple(sealed_scores),
        sealed_mean_log_score_gain=sealed_mean,
        answer_check_category=answer_category,
        evaluable=evaluable,
        unavailable_reasons=tuple(sorted(set(unavailable))),
        fingerprint=_configuration_fingerprint(payload),
    )


def terminal_category_from_primary(
    *,
    finite_height_fraction: float | None,
    minimum_finite_height_fraction: float,
    primary: ThicknessConfigurationResult,
) -> str:
    if finite_height_fraction is None or finite_height_fraction < minimum_finite_height_fraction:
        return "empirical_n2_thickness_unavailable"
    mapping = {
        "estimable_and_generalizing": "empirical_n2_thickness_generalizing",
        "estimable_but_generalization_mixed": "empirical_n2_thickness_generalization_mixed",
        "estimable_but_non_generalizing": "empirical_n2_thickness_not_generalizing",
        "empirical_thickness_answer_check_unavailable": "empirical_n2_thickness_unavailable",
    }
    try:
        return mapping[primary.answer_check_category]
    except KeyError as exc:
        raise ValueError(f"unexpected answer-check category: {primary.answer_check_category}") from exc
