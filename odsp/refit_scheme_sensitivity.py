"""Sensitivity of refit-aware transfer conclusions to the declared refit scheme.

Each caller-declared training-resampling/refitting scheme is evaluated using the
existing model-refit transfer uncertainty audit on the same untouched validation
rows, groups, blocks and optional weights.  This layer compares those already
validated scheme-level conclusions; it does not infer which scheme is correct.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np

from .model_refit_transfer_uncertainty import (
    ModelRefitTransferAudit,
    audit_model_refit_transfer_uncertainty,
)


@dataclass(frozen=True)
class RefitSchemeResult:
    scheme_name: str
    refit_count: int
    point_transfer_category: str
    reference_fit_category: str
    refit_sign_stability: str
    refit_aware_category: str
    refit_aware_admissible: bool
    ensemble_mean_gain: float
    minimum_nested_max_t_lower_bound: float | None
    maximum_nested_max_t_upper_bound: float | None
    audit: ModelRefitTransferAudit

    def as_dict(self) -> dict[str, object]:
        return {
            "scheme_name": self.scheme_name,
            "refit_count": self.refit_count,
            "point_transfer_category": self.point_transfer_category,
            "reference_fit_category": self.reference_fit_category,
            "refit_sign_stability": self.refit_sign_stability,
            "refit_aware_category": self.refit_aware_category,
            "refit_aware_admissible": self.refit_aware_admissible,
            "ensemble_mean_gain": self.ensemble_mean_gain,
            "minimum_nested_max_t_lower_bound": self.minimum_nested_max_t_lower_bound,
            "maximum_nested_max_t_upper_bound": self.maximum_nested_max_t_upper_bound,
            "audit": self.audit.as_dict(),
        }


@dataclass(frozen=True)
class RefitSchemeSensitivityAudit:
    row_count: int
    scheme_count: int
    scheme_names: tuple[str, ...]
    familywise_confidence_level: float
    nested_draws: int
    seed: int
    minimum_refits: int
    minimum_blocks_per_group: int
    scheme_category_set: tuple[str, ...]
    point_category_set: tuple[str, ...]
    sensitivity_category: str
    scheme_robust_admissible: bool
    any_scheme_category_change: bool
    any_point_category_change: bool
    minimum_scheme_mean_gain: float
    maximum_scheme_mean_gain: float
    minimum_nested_max_t_lower_bound: float | None
    maximum_nested_max_t_upper_bound: float | None
    unavailable_scheme_count: int
    automatic_scheme_selection: bool
    aggregate_confidence_score_emitted: bool
    schemes: tuple[RefitSchemeResult, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "row_count": self.row_count,
            "scheme_count": self.scheme_count,
            "scheme_names": list(self.scheme_names),
            "familywise_confidence_level": self.familywise_confidence_level,
            "nested_draws": self.nested_draws,
            "seed": self.seed,
            "minimum_refits": self.minimum_refits,
            "minimum_blocks_per_group": self.minimum_blocks_per_group,
            "scheme_category_set": list(self.scheme_category_set),
            "point_category_set": list(self.point_category_set),
            "sensitivity_category": self.sensitivity_category,
            "scheme_robust_admissible": self.scheme_robust_admissible,
            "any_scheme_category_change": self.any_scheme_category_change,
            "any_point_category_change": self.any_point_category_change,
            "minimum_scheme_mean_gain": self.minimum_scheme_mean_gain,
            "maximum_scheme_mean_gain": self.maximum_scheme_mean_gain,
            "minimum_nested_max_t_lower_bound": self.minimum_nested_max_t_lower_bound,
            "maximum_nested_max_t_upper_bound": self.maximum_nested_max_t_upper_bound,
            "unavailable_scheme_count": self.unavailable_scheme_count,
            "automatic_scheme_selection": self.automatic_scheme_selection,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "schemes": [row.as_dict() for row in self.schemes],
        }


def _scheme_mapping(
    schemes: Mapping[str, Sequence[Sequence[float]]],
) -> tuple[tuple[str, np.ndarray], ...]:
    if len(schemes) < 2:
        raise ValueError("refit_schemes must contain at least two named schemes")
    rows: list[tuple[str, np.ndarray]] = []
    validation_rows: int | None = None
    for raw_name, raw_matrix in schemes.items():
        name = str(raw_name).strip()
        if not name:
            raise ValueError("scheme names must be non-empty")
        matrix = np.asarray(raw_matrix, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
            raise ValueError("each scheme must be a non-empty refits x validation_rows matrix")
        if not np.isfinite(matrix).all():
            raise ValueError("scheme gain matrices must contain only finite values")
        if validation_rows is None:
            validation_rows = int(matrix.shape[1])
        elif matrix.shape[1] != validation_rows:
            raise ValueError("all schemes must use the same number of validation rows")
        rows.append((name, matrix))
    if len({name for name, _ in rows}) != len(rows):
        raise ValueError("scheme names must be unique")
    return tuple(sorted(rows, key=lambda row: row[0]))


def _lookup_optional_mapping(
    mapping: Mapping[str, object] | None,
    name: str,
):
    if mapping is None:
        return None
    unknown = set(mapping) - {name}
    # Unknown keys are validated globally by the caller below; this helper only reads.
    _ = unknown
    return mapping.get(name)


def audit_refit_scheme_sensitivity(
    refit_schemes: Mapping[str, Sequence[Sequence[float]]],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    sample_weight: Sequence[float] | None = None,
    refit_ids_by_scheme: Mapping[str, Sequence[object]] | None = None,
    reference_refit_ids_by_scheme: Mapping[str, object] | None = None,
    familywise_confidence_level: float = 0.95,
    nested_draws: int = 2500,
    seed: int = 20260907,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> RefitSchemeSensitivityAudit:
    """Compare refit-aware transfer conclusions across declared refit schemes."""

    schemes = _scheme_mapping(refit_schemes)
    names = tuple(name for name, _ in schemes)
    allowed = set(names)
    if refit_ids_by_scheme is not None and set(refit_ids_by_scheme) - allowed:
        raise ValueError("refit_ids_by_scheme contains an unknown scheme")
    if reference_refit_ids_by_scheme is not None and set(reference_refit_ids_by_scheme) - allowed:
        raise ValueError("reference_refit_ids_by_scheme contains an unknown scheme")

    results: list[RefitSchemeResult] = []
    for name, matrix in schemes:
        refit_ids = None if refit_ids_by_scheme is None else refit_ids_by_scheme.get(name)
        reference_id = (
            None if reference_refit_ids_by_scheme is None
            else reference_refit_ids_by_scheme.get(name)
        )
        audit = audit_model_refit_transfer_uncertainty(
            matrix,
            groups,
            blocks=blocks,
            refit_ids=refit_ids,
            reference_refit_id=reference_id,
            sample_weight=sample_weight,
            familywise_confidence_level=familywise_confidence_level,
            nested_draws=nested_draws,
            seed=seed,
            minimum_refits=minimum_refits,
            minimum_blocks_per_group=minimum_blocks_per_group,
            gain_tolerance=gain_tolerance,
        )
        lower = [
            row.nested_max_t_lower_bound
            for row in audit.groups
            if row.nested_max_t_lower_bound is not None
        ]
        upper = [
            row.nested_max_t_upper_bound
            for row in audit.groups
            if row.nested_max_t_upper_bound is not None
        ]
        results.append(
            RefitSchemeResult(
                scheme_name=name,
                refit_count=audit.refit_count,
                point_transfer_category=audit.point_transfer_category,
                reference_fit_category=audit.reference_fit_category,
                refit_sign_stability=audit.refit_sign_stability,
                refit_aware_category=audit.refit_aware_category,
                refit_aware_admissible=audit.refit_aware_admissible,
                ensemble_mean_gain=float(np.mean([row.ensemble_mean_gain for row in audit.groups])),
                minimum_nested_max_t_lower_bound=(
                    float(min(lower)) if len(lower) == len(audit.groups) else None
                ),
                maximum_nested_max_t_upper_bound=(
                    float(max(upper)) if len(upper) == len(audit.groups) else None
                ),
                audit=audit,
            )
        )

    categories = tuple(sorted({row.refit_aware_category for row in results}))
    point_categories = tuple(sorted({row.point_transfer_category for row in results}))
    unavailable = sum(row.refit_aware_category == "unavailable" for row in results)
    if unavailable:
        sensitivity = "unavailable"
    elif categories == ("robust_generalizing",):
        sensitivity = "scheme_robust_generalizing"
    elif categories == ("robust_non_generalizing",):
        sensitivity = "scheme_robust_non_generalizing"
    elif len(categories) == 1:
        sensitivity = f"stable_{categories[0]}"
    else:
        sensitivity = "scheme_sensitive"

    all_lower = [
        row.minimum_nested_max_t_lower_bound
        for row in results
        if row.minimum_nested_max_t_lower_bound is not None
    ]
    all_upper = [
        row.maximum_nested_max_t_upper_bound
        for row in results
        if row.maximum_nested_max_t_upper_bound is not None
    ]
    means = [row.ensemble_mean_gain for row in results]
    return RefitSchemeSensitivityAudit(
        row_count=int(schemes[0][1].shape[1]),
        scheme_count=len(results),
        scheme_names=tuple(row.scheme_name for row in results),
        familywise_confidence_level=float(familywise_confidence_level),
        nested_draws=int(nested_draws),
        seed=int(seed),
        minimum_refits=int(minimum_refits),
        minimum_blocks_per_group=int(minimum_blocks_per_group),
        scheme_category_set=categories,
        point_category_set=point_categories,
        sensitivity_category=sensitivity,
        scheme_robust_admissible=bool(sensitivity == "scheme_robust_generalizing"),
        any_scheme_category_change=len(categories) > 1,
        any_point_category_change=len(point_categories) > 1,
        minimum_scheme_mean_gain=float(min(means)),
        maximum_scheme_mean_gain=float(max(means)),
        minimum_nested_max_t_lower_bound=(float(min(all_lower)) if all_lower else None),
        maximum_nested_max_t_upper_bound=(float(max(all_upper)) if all_upper else None),
        unavailable_scheme_count=int(unavailable),
        automatic_scheme_selection=False,
        aggregate_confidence_score_emitted=False,
        schemes=tuple(results),
    )
