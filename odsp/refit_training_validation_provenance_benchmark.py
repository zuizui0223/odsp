"""Known-truth benchmark for refit training/validation provenance."""
from __future__ import annotations

from copy import deepcopy

from .refit_training_validation_provenance import (
    audit_refit_training_validation_provenance,
)


def _design():
    validation = tuple(f"v-{i:02d}" for i in range(8))
    memberships = {
        "bootstrap": {
            "bootstrap-refit-00": ("t-00", "t-01", "t-02", "t-02", "t-03"),
            "bootstrap-refit-01": ("t-04", "t-05", "t-06", "t-07", "t-08"),
            "bootstrap-refit-02": ("t-09", "t-10", "t-11", "t-11", "t-12"),
            "bootstrap-refit-03": ("t-13", "t-14", "t-15", "t-16", "t-17"),
        },
        "fold": {
            "fold-refit-00": ("t-20", "t-21", "t-22", "t-23"),
            "fold-refit-01": ("t-24", "t-25", "t-26", "t-27"),
            "fold-refit-02": ("t-28", "t-29", "t-30", "t-31"),
            "fold-refit-03": ("t-32", "t-33", "t-34", "t-35"),
        },
        "seed": {
            "seed-refit-00": ("t-40", "t-41", "t-42", "t-43"),
            "seed-refit-01": ("t-44", "t-45", "t-46", "t-47"),
            "seed-refit-02": ("t-48", "t-49", "t-50", "t-51"),
            "seed-refit-03": ("t-52", "t-53", "t-54", "t-55"),
        },
    }
    expected = {
        scheme: tuple(refits)
        for scheme, refits in memberships.items()
    }
    return validation, memberships, expected


def _reordered(mapping):
    return {
        scheme: dict(reversed(list(refits.items())))
        for scheme, refits in reversed(list(mapping.items()))
    }


def run_refit_training_validation_provenance_benchmark() -> dict[str, object]:
    validation, memberships, expected = _design()
    disjoint = audit_refit_training_validation_provenance(
        validation,
        memberships,
        expected_refit_ids_by_scheme=expected,
    )

    single = deepcopy(memberships)
    single["bootstrap"]["bootstrap-refit-01"] = (
        "t-04", "t-05", validation[3], "t-07", "t-08"
    )
    single_leak = audit_refit_training_validation_provenance(
        validation,
        single,
        expected_refit_ids_by_scheme=expected,
    )

    repeated = deepcopy(memberships)
    repeated["bootstrap"]["bootstrap-refit-01"] = (
        "t-04", validation[3], validation[3], "t-07", "t-08"
    )
    repeated_leak = audit_refit_training_validation_provenance(
        validation,
        repeated,
        expected_refit_ids_by_scheme=expected,
    )

    multiple = deepcopy(memberships)
    multiple["bootstrap"]["bootstrap-refit-01"] = (
        validation[1], validation[2], "t-06", "t-07"
    )
    multiple["fold"]["fold-refit-02"] = (
        validation[2], "t-29", "t-30", "t-31"
    )
    multiple["seed"]["seed-refit-03"] = (
        validation[4], validation[5], validation[6], "t-55"
    )
    multiple_leak = audit_refit_training_validation_provenance(
        validation,
        multiple,
        expected_refit_ids_by_scheme=expected,
    )

    duplicate_validation_rejected = False
    try:
        audit_refit_training_validation_provenance(
            validation[:-1] + (validation[0],),
            memberships,
            expected_refit_ids_by_scheme=expected,
        )
    except ValueError:
        duplicate_validation_rejected = True

    empty_training_refit_rejected = False
    empty_membership = deepcopy(memberships)
    empty_membership["fold"]["fold-refit-00"] = ()
    try:
        audit_refit_training_validation_provenance(
            validation,
            empty_membership,
            expected_refit_ids_by_scheme=expected,
        )
    except ValueError:
        empty_training_refit_rejected = True

    missing_expected_refit_rejected = False
    missing_membership = deepcopy(memberships)
    del missing_membership["seed"]["seed-refit-03"]
    try:
        audit_refit_training_validation_provenance(
            validation,
            missing_membership,
            expected_refit_ids_by_scheme=expected,
        )
    except ValueError:
        missing_expected_refit_rejected = True

    extra_expected_refit_rejected = False
    extra_expected = deepcopy(expected)
    extra_expected["seed"] = extra_expected["seed"] + ("seed-refit-extra",)
    try:
        audit_refit_training_validation_provenance(
            validation,
            memberships,
            expected_refit_ids_by_scheme=extra_expected,
        )
    except ValueError:
        extra_expected_refit_rejected = True

    extra_actual_refit_rejected = False
    extra_actual = deepcopy(memberships)
    extra_actual["seed"]["seed-refit-extra"] = ("t-60", "t-61")
    try:
        audit_refit_training_validation_provenance(
            validation,
            extra_actual,
            expected_refit_ids_by_scheme=expected,
        )
    except ValueError:
        extra_actual_refit_rejected = True

    reordered = audit_refit_training_validation_provenance(
        validation,
        _reordered(memberships),
        expected_refit_ids_by_scheme=dict(reversed(list(expected.items()))),
    )

    relabel = {row: f"R::{row}" for row in validation}
    for refits in memberships.values():
        for rows in refits.values():
            for row in rows:
                relabel.setdefault(row, f"R::{row}")
    relabeled_validation = tuple(relabel[row] for row in validation)
    relabeled_memberships = {
        scheme: {
            refit: tuple(relabel[row] for row in rows)
            for refit, rows in refits.items()
        }
        for scheme, refits in memberships.items()
    }
    relabeled = audit_refit_training_validation_provenance(
        relabeled_validation,
        relabeled_memberships,
        expected_refit_ids_by_scheme=expected,
    )

    bootstrap = next(
        row for row in disjoint.schemes if row.scheme_name == "bootstrap"
    )
    repeated_bootstrap = next(
        row for row in repeated_leak.schemes if row.scheme_name == "bootstrap"
    )
    repeated_refit = next(
        row
        for row in repeated_bootstrap.refits
        if row.refit_id == "bootstrap-refit-01"
    )

    checks = {
        "fully_disjoint_memberships_pass": disjoint.separation_category == "training_validation_disjoint" and disjoint.training_validation_separated and disjoint.overlapping_refit_count == 0,
        "bootstrap_duplicate_training_rows_are_allowed": bootstrap.duplicate_training_row_count == 2 and disjoint.duplicate_training_row_count == 2,
        "single_refit_single_row_overlap_is_detected": single_leak.separation_category == "leakage_detected" and single_leak.overlapping_refit_count == 1 and single_leak.affected_scheme_count == 1 and single_leak.unique_overlapping_validation_row_count == 1,
        "repeated_same_leaked_row_counts_one_unique_overlap": repeated_leak.unique_overlapping_validation_row_count == 1 and repeated_refit.overlapping_validation_row_count == 1 and repeated_refit.duplicate_training_row_count == 1,
        "multiple_scheme_refit_overlaps_are_aggregated": multiple_leak.overlapping_refit_count == 3 and multiple_leak.affected_scheme_count == 3 and multiple_leak.unique_overlapping_validation_row_count == 5,
        "maximum_per_refit_overlap_is_retained": multiple_leak.maximum_refit_overlap_count == 3,
        "duplicate_validation_row_id_is_rejected": duplicate_validation_rejected,
        "empty_training_refit_membership_is_rejected": empty_training_refit_rejected,
        "missing_expected_refit_is_rejected": missing_expected_refit_rejected,
        "extra_expected_or_actual_refit_is_rejected": extra_expected_refit_rejected and extra_actual_refit_rejected,
        "scheme_and_refit_mapping_order_is_invariant": reordered.as_dict() == disjoint.as_dict(),
        "consistent_row_id_relabeling_preserves_provenance_result": relabeled.as_dict() == disjoint.as_dict(),
        "overlapping_row_ids_are_not_emitted": not single_leak.overlapping_row_ids_emitted and all(row not in str(single_leak.as_dict()) for row in validation),
        "no_automatic_training_row_inference": not disjoint.automatic_training_row_inference and not single_leak.automatic_training_row_inference,
        "aggregate_confidence_score_emitted": not disjoint.aggregate_confidence_score_emitted and not single_leak.aggregate_confidence_score_emitted,
    }

    return {
        "validation_row_count": len(validation),
        "scheme_count": len(memberships),
        "refits_per_scheme": 4,
        "disjoint": disjoint.as_dict(),
        "single_leak": single_leak.as_dict(),
        "repeated_leak": repeated_leak.as_dict(),
        "multiple_leak": multiple_leak.as_dict(),
        "duplicate_validation_rejected": duplicate_validation_rejected,
        "empty_training_refit_rejected": empty_training_refit_rejected,
        "missing_expected_refit_rejected": missing_expected_refit_rejected,
        "extra_expected_refit_rejected": extra_expected_refit_rejected,
        "extra_actual_refit_rejected": extra_actual_refit_rejected,
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
