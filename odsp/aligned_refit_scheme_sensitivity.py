"""Row-aligned composition of refit-scheme sensitivity evidence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .heldout_row_alignment import (
    HeldoutRowAlignmentAudit,
    audit_heldout_row_alignment,
    reorder_validation_rows,
)
from .refit_scheme_sensitivity import (
    RefitSchemeSensitivityAudit,
    audit_refit_scheme_sensitivity,
)


@dataclass(frozen=True)
class AlignedRefitSchemeSensitivityAudit:
    status: str
    statistical_audit_run: bool
    row_alignment: HeldoutRowAlignmentAudit
    reordered_scheme_count: int
    scheme_sensitivity_category: str
    scheme_robust_admissible: bool
    automatic_row_imputation: bool
    automatic_scheme_selection: bool
    aggregate_confidence_score_emitted: bool
    scheme_audit: RefitSchemeSensitivityAudit | None

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "statistical_audit_run": self.statistical_audit_run,
            "row_alignment": self.row_alignment.as_dict(),
            "reordered_scheme_count": self.reordered_scheme_count,
            "scheme_sensitivity_category": self.scheme_sensitivity_category,
            "scheme_robust_admissible": self.scheme_robust_admissible,
            "automatic_row_imputation": self.automatic_row_imputation,
            "automatic_scheme_selection": self.automatic_scheme_selection,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "scheme_audit": None if self.scheme_audit is None else self.scheme_audit.as_dict(),
        }


def _canonical_mapping(mapping: Mapping[str, object], *, label: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for raw_name, value in mapping.items():
        name = str(raw_name).strip()
        if not name:
            raise ValueError(f"{label} names must be non-empty")
        if name in result:
            raise ValueError(f"{label} names must be unique after canonicalization")
        result[name] = value
    return dict(sorted(result.items()))


def _canonical_optional_mapping(
    mapping: Mapping[str, object] | None,
    *,
    label: str,
) -> dict[str, object] | None:
    if mapping is None:
        return None
    return _canonical_mapping(mapping, label=label)


def audit_aligned_refit_scheme_sensitivity(
    refit_schemes: Mapping[str, Sequence[Sequence[float]]],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    validation_row_ids: Sequence[object],
    validation_row_ids_by_scheme: Mapping[str, Sequence[object]],
    sample_weight: Sequence[float] | None = None,
    refit_ids_by_scheme: Mapping[str, Sequence[object]] | None = None,
    reference_refit_ids_by_scheme: Mapping[str, object] | None = None,
    familywise_confidence_level: float = 0.95,
    nested_draws: int = 2500,
    seed: int = 20260907,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> AlignedRefitSchemeSensitivityAudit:
    """Align each scheme to one canonical held-out row order, then audit schemes.

    Row-key mismatch is a provenance failure, so the statistical scheme audit is
    not run. A pure ordering difference is repaired only through the exact
    permutation established from caller-supplied unique row keys.
    """

    base_ids = tuple(validation_row_ids)
    base_groups = tuple(groups)
    base_blocks = tuple(blocks)
    if len(base_groups) != len(base_ids) or len(base_blocks) != len(base_ids):
        raise ValueError("groups and blocks must match validation_row_ids length")
    if sample_weight is not None and len(tuple(sample_weight)) != len(base_ids):
        raise ValueError("sample_weight must match validation_row_ids length")

    raw_schemes = _canonical_mapping(refit_schemes, label="refit_schemes")
    raw_scheme_ids = _canonical_mapping(
        validation_row_ids_by_scheme,
        label="validation_row_ids_by_scheme",
    )
    if set(raw_scheme_ids) != set(raw_schemes):
        raise ValueError("validation_row_ids_by_scheme must cover every and only declared scheme")

    matrices: dict[str, np.ndarray] = {}
    scheme_row_ids: dict[str, tuple[object, ...]] = {}
    for name, raw_matrix in raw_schemes.items():
        matrix = np.asarray(raw_matrix, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
            raise ValueError("each refit scheme must be a non-empty refits x validation_rows matrix")
        if not np.isfinite(matrix).all():
            raise ValueError("refit scheme matrices must contain only finite values")
        ids = tuple(raw_scheme_ids[name])
        if matrix.shape[1] != len(ids):
            raise ValueError("each scheme matrix column count must match its declared validation row IDs")
        matrices[name] = matrix
        scheme_row_ids[name] = ids

    optional_refit_ids = _canonical_optional_mapping(refit_ids_by_scheme, label="refit_ids_by_scheme")
    optional_reference_ids = _canonical_optional_mapping(
        reference_refit_ids_by_scheme,
        label="reference_refit_ids_by_scheme",
    )
    for mapping, label in (
        (optional_refit_ids, "refit_ids_by_scheme"),
        (optional_reference_ids, "reference_refit_ids_by_scheme"),
    ):
        if mapping is not None and set(mapping) - set(matrices):
            raise ValueError(f"{label} contains an unknown scheme")

    row_alignment = audit_heldout_row_alignment(base_ids, scheme_row_ids)
    if not row_alignment.alignment_passed:
        return AlignedRefitSchemeSensitivityAudit(
            status="row_mismatch",
            statistical_audit_run=False,
            row_alignment=row_alignment,
            reordered_scheme_count=row_alignment.reorderable_source_count,
            scheme_sensitivity_category="not_run_row_mismatch",
            scheme_robust_admissible=False,
            automatic_row_imputation=False,
            automatic_scheme_selection=False,
            aggregate_confidence_score_emitted=False,
            scheme_audit=None,
        )

    by_name = {row.source_name: row for row in row_alignment.sources}
    aligned: dict[str, np.ndarray] = {}
    for name, matrix in matrices.items():
        source = by_name[name]
        permutation = source.permutation_to_base
        if permutation is None:
            raise RuntimeError("successful row alignment must expose a permutation")
        aligned[name] = (
            matrix
            if source.status == "exact_alignment"
            else reorder_validation_rows(matrix, permutation, axis=1)
        )

    scheme_audit = audit_refit_scheme_sensitivity(
        aligned,
        base_groups,
        blocks=base_blocks,
        sample_weight=sample_weight,
        refit_ids_by_scheme=optional_refit_ids,
        reference_refit_ids_by_scheme=optional_reference_ids,
        familywise_confidence_level=familywise_confidence_level,
        nested_draws=nested_draws,
        seed=seed,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )
    status = (
        "audited_exact_alignment"
        if row_alignment.alignment_category == "exact_alignment"
        else "audited_reordered_alignment"
    )
    return AlignedRefitSchemeSensitivityAudit(
        status=status,
        statistical_audit_run=True,
        row_alignment=row_alignment,
        reordered_scheme_count=row_alignment.reorderable_source_count,
        scheme_sensitivity_category=scheme_audit.sensitivity_category,
        scheme_robust_admissible=scheme_audit.scheme_robust_admissible,
        automatic_row_imputation=False,
        automatic_scheme_selection=scheme_audit.automatic_scheme_selection,
        aggregate_confidence_score_emitted=False,
        scheme_audit=scheme_audit,
    )
