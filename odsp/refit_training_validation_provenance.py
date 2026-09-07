"""Training/validation row-overlap provenance for declared model refits."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class RefitTrainingProvenanceRow:
    scheme_name: str
    refit_id: str
    training_row_count: int
    unique_training_row_count: int
    duplicate_training_row_count: int
    overlapping_validation_row_count: int
    status: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RefitTrainingSchemeProvenance:
    scheme_name: str
    refit_count: int
    overlapping_refit_count: int
    unique_overlapping_validation_row_count: int
    maximum_refit_overlap_count: int
    duplicate_training_row_count: int
    separation_category: str
    refits: tuple[RefitTrainingProvenanceRow, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["refits"] = [row.as_dict() for row in self.refits]
        return payload


@dataclass(frozen=True)
class RefitTrainingValidationProvenanceAudit:
    validation_row_count: int
    scheme_count: int
    refit_count: int
    scheme_names: tuple[str, ...]
    overlapping_refit_count: int
    affected_scheme_count: int
    unique_overlapping_validation_row_count: int
    maximum_refit_overlap_count: int
    duplicate_training_row_count: int
    separation_category: str
    training_validation_separated: bool
    expected_refit_coverage_checked: bool
    overlapping_row_ids_emitted: bool
    automatic_training_row_inference: bool
    aggregate_confidence_score_emitted: bool
    schemes: tuple[RefitTrainingSchemeProvenance, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "validation_row_count": self.validation_row_count,
            "scheme_count": self.scheme_count,
            "refit_count": self.refit_count,
            "scheme_names": list(self.scheme_names),
            "overlapping_refit_count": self.overlapping_refit_count,
            "affected_scheme_count": self.affected_scheme_count,
            "unique_overlapping_validation_row_count": self.unique_overlapping_validation_row_count,
            "maximum_refit_overlap_count": self.maximum_refit_overlap_count,
            "duplicate_training_row_count": self.duplicate_training_row_count,
            "separation_category": self.separation_category,
            "training_validation_separated": self.training_validation_separated,
            "expected_refit_coverage_checked": self.expected_refit_coverage_checked,
            "overlapping_row_ids_emitted": self.overlapping_row_ids_emitted,
            "automatic_training_row_inference": self.automatic_training_row_inference,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "schemes": [row.as_dict() for row in self.schemes],
        }


def _validate_row_id(value: object, *, label: str) -> None:
    if value is None:
        raise ValueError(f"{label} must not contain missing row IDs")
    try:
        hash(value)
    except TypeError as exc:
        raise ValueError(f"{label} row IDs must be hashable scalar values") from exc
    if isinstance(value, (float, np.floating)) and bool(np.isnan(value)):
        raise ValueError(f"{label} must not contain missing row IDs")


def _row_ids(
    values: Sequence[object],
    *,
    label: str,
    require_nonempty: bool,
) -> tuple[object, ...]:
    rows = tuple(values)
    if require_nonempty and not rows:
        raise ValueError(f"{label} must contain at least one row ID")
    for value in rows:
        _validate_row_id(value, label=label)
    return rows


def _scheme_name(value: object) -> str:
    name = str(value).strip()
    if not name:
        raise ValueError("scheme names must be non-empty")
    return name


def _refit_id(value: object) -> str:
    refit = str(value).strip()
    if not refit:
        raise ValueError("refit IDs must be non-empty")
    return refit


def _canonical_training_memberships(
    training_row_ids_by_scheme: Mapping[str, Mapping[object, Sequence[object]]],
) -> dict[str, dict[str, tuple[object, ...]]]:
    if not training_row_ids_by_scheme:
        raise ValueError("training_row_ids_by_scheme must contain at least one scheme")
    result: dict[str, dict[str, tuple[object, ...]]] = {}
    for raw_scheme, raw_refits in training_row_ids_by_scheme.items():
        scheme = _scheme_name(raw_scheme)
        if scheme in result:
            raise ValueError("scheme names must be unique after canonicalization")
        if not raw_refits:
            raise ValueError("each scheme must contain at least one declared refit")
        refits: dict[str, tuple[object, ...]] = {}
        for raw_refit, raw_rows in raw_refits.items():
            refit = _refit_id(raw_refit)
            if refit in refits:
                raise ValueError("refit IDs must be unique within each scheme after canonicalization")
            refits[refit] = _row_ids(
                raw_rows,
                label=f"training rows for {scheme}/{refit}",
                require_nonempty=True,
            )
        result[scheme] = dict(sorted(refits.items()))
    return dict(sorted(result.items()))


def _canonical_expected_refits(
    expected_refit_ids_by_scheme: Mapping[str, Sequence[object]],
) -> dict[str, tuple[str, ...]]:
    if not expected_refit_ids_by_scheme:
        raise ValueError("expected_refit_ids_by_scheme must contain at least one scheme")
    result: dict[str, tuple[str, ...]] = {}
    for raw_scheme, raw_ids in expected_refit_ids_by_scheme.items():
        scheme = _scheme_name(raw_scheme)
        if scheme in result:
            raise ValueError("expected scheme names must be unique after canonicalization")
        ids = tuple(_refit_id(value) for value in raw_ids)
        if not ids:
            raise ValueError("each expected scheme must contain at least one refit ID")
        if len(set(ids)) != len(ids):
            raise ValueError("expected refit IDs must be unique within each scheme")
        result[scheme] = tuple(sorted(ids))
    return dict(sorted(result.items()))


def audit_refit_training_validation_provenance(
    validation_row_ids: Sequence[object],
    training_row_ids_by_scheme: Mapping[str, Mapping[object, Sequence[object]]],
    *,
    expected_refit_ids_by_scheme: Mapping[str, Sequence[object]] | None = None,
) -> RefitTrainingValidationProvenanceAudit:
    """Check declared refit training memberships for direct validation-row overlap.

    Training rows may repeat within a refit, as in bootstrap resampling. Repeats
    are reported but do not multiply the number of unique leaked validation rows.
    The audit checks only caller-supplied memberships; a disjoint result does not
    prove that the declarations exhaust the model's actual training history.
    """

    validation = _row_ids(
        validation_row_ids,
        label="validation_row_ids",
        require_nonempty=True,
    )
    if len(set(validation)) != len(validation):
        raise ValueError("validation_row_ids must be unique")
    validation_set = set(validation)

    memberships = _canonical_training_memberships(training_row_ids_by_scheme)
    expected_checked = expected_refit_ids_by_scheme is not None
    if expected_refit_ids_by_scheme is not None:
        expected = _canonical_expected_refits(expected_refit_ids_by_scheme)
        if set(expected) != set(memberships):
            raise ValueError("expected scheme coverage must exactly match declared training schemes")
        for scheme in memberships:
            if tuple(memberships[scheme]) != expected[scheme]:
                raise ValueError(
                    f"expected refit coverage for scheme {scheme!r} must exactly match declared training refits"
                )

    scheme_results: list[RefitTrainingSchemeProvenance] = []
    global_overlap: set[object] = set()
    total_duplicate_count = 0
    total_overlapping_refits = 0
    maximum_overlap = 0

    for scheme, refits in memberships.items():
        refit_results: list[RefitTrainingProvenanceRow] = []
        scheme_overlap: set[object] = set()
        scheme_duplicates = 0
        overlapping_refits = 0
        scheme_maximum_overlap = 0

        for refit, training_rows in refits.items():
            unique_training = set(training_rows)
            duplicate_count = len(training_rows) - len(unique_training)
            overlap = unique_training & validation_set
            overlap_count = len(overlap)
            status = "leakage_detected" if overlap_count else "training_validation_disjoint"
            if overlap_count:
                overlapping_refits += 1
                scheme_overlap.update(overlap)
                global_overlap.update(overlap)
            scheme_duplicates += duplicate_count
            total_duplicate_count += duplicate_count
            scheme_maximum_overlap = max(scheme_maximum_overlap, overlap_count)
            maximum_overlap = max(maximum_overlap, overlap_count)
            refit_results.append(
                RefitTrainingProvenanceRow(
                    scheme_name=scheme,
                    refit_id=refit,
                    training_row_count=len(training_rows),
                    unique_training_row_count=len(unique_training),
                    duplicate_training_row_count=duplicate_count,
                    overlapping_validation_row_count=overlap_count,
                    status=status,
                )
            )

        total_overlapping_refits += overlapping_refits
        scheme_category = (
            "leakage_detected" if overlapping_refits else "training_validation_disjoint"
        )
        scheme_results.append(
            RefitTrainingSchemeProvenance(
                scheme_name=scheme,
                refit_count=len(refit_results),
                overlapping_refit_count=overlapping_refits,
                unique_overlapping_validation_row_count=len(scheme_overlap),
                maximum_refit_overlap_count=scheme_maximum_overlap,
                duplicate_training_row_count=scheme_duplicates,
                separation_category=scheme_category,
                refits=tuple(refit_results),
            )
        )

    affected_schemes = sum(
        row.separation_category == "leakage_detected" for row in scheme_results
    )
    category = "leakage_detected" if total_overlapping_refits else "training_validation_disjoint"
    return RefitTrainingValidationProvenanceAudit(
        validation_row_count=len(validation),
        scheme_count=len(scheme_results),
        refit_count=sum(row.refit_count for row in scheme_results),
        scheme_names=tuple(row.scheme_name for row in scheme_results),
        overlapping_refit_count=total_overlapping_refits,
        affected_scheme_count=affected_schemes,
        unique_overlapping_validation_row_count=len(global_overlap),
        maximum_refit_overlap_count=maximum_overlap,
        duplicate_training_row_count=total_duplicate_count,
        separation_category=category,
        training_validation_separated=bool(total_overlapping_refits == 0),
        expected_refit_coverage_checked=expected_checked,
        overlapping_row_ids_emitted=False,
        automatic_training_row_inference=False,
        aggregate_confidence_score_emitted=False,
        schemes=tuple(scheme_results),
    )
