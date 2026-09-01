import json
import math

import pytest

from odsp.n2_bat_thickness import (
    evaluate_thickness_configuration,
    finite_height_fraction_among_structural_joint_events,
    height_bin_index,
    structural_eligible_cells,
    terminal_category_from_primary,
)


def _row(iid, x, z, *, outlier="false"):
    return {
        "individual_local_identifier": iid,
        "location_long": str(x),
        "location_lat": "0",
        "height_above_msl": str(z),
        "manually_marked_outlier": outlier,
    }


def test_fixed_bins_are_left_closed_right_open_with_explicit_tails():
    edges = (-math.inf, 0, 50, 100, math.inf)
    assert height_bin_index(-1, edges) == 0
    assert height_bin_index(0, edges) == 1
    assert height_bin_index(49.999, edges) == 1
    assert height_bin_index(50, edges) == 2
    assert height_bin_index(100, edges) == 3
    assert height_bin_index(999999, edges) == 3


def test_structural_eligibility_uses_height_presence_not_numeric_outcome():
    rows = [
        _row("m1", 0.1, "not-a-number"),
        _row("m2", 0.1, 10),
        _row("m1", 0.1, "not-a-number"),
        _row("m2", 0.1, 10),
    ]
    split = {"m1": "model", "m2": "model"}
    cells, _ = structural_eligible_cells(
        rows,
        height_field="height_above_msl",
        projector=lambda lon, lat: (lon, lat),
        cell_size_m=1,
        minimum_events_per_cell=4,
        minimum_distinct_model_individuals_per_cell=2,
        split=split,
    )
    assert cells == {(0, 0)}
    finite, denominator, fraction = finite_height_fraction_among_structural_joint_events(
        rows,
        height_field="height_above_msl",
    )
    assert (finite, denominator, fraction) == (2, 4, 0.5)


def _synthetic_generalizing_rows():
    rows = []
    # Three model bats. Each uses both cells, but low z dominates cell 0 and
    # high z dominates cell 1. Event counts differ strongly among bats so the
    # calculation must retain the individual-equal contract rather than pooling
    # all events as if they were independent bats.
    for iid, repetitions in (("m1", 20), ("m2", 6), ("m3", 3)):
        rows.extend(_row(iid, 0.1, 10) for _ in range(repetitions))
        rows.extend(_row(iid, 1.1, 300) for _ in range(repetitions))
        # A little within-cell spread keeps the example non-degenerate.
        rows.append(_row(iid, 0.1, 70))
        rows.append(_row(iid, 1.1, 150))
    # Two sealed bats reproduce the same x-y-resolved vertical pattern.
    for iid in ("s1", "s2"):
        rows.extend(_row(iid, 0.1, 10) for _ in range(8))
        rows.extend(_row(iid, 1.1, 300) for _ in range(8))
    return rows


def test_configuration_reports_thickness_and_independent_positive_sealed_gains():
    rows = _synthetic_generalizing_rows()
    split = {"m1": "model", "m2": "model", "m3": "model", "s1": "sealed", "s2": "sealed"}
    result = evaluate_thickness_configuration(
        rows,
        height_field="height_above_msl",
        projector=lambda lon, lat: (lon, lat),
        cell_size_m=1,
        z_edges=(-math.inf, 0, 50, 100, 200, 400, math.inf),
        minimum_events_per_cell=3,
        minimum_distinct_model_individuals_per_cell=3,
        minimum_scored_events_per_sealed_individual=4,
        split=split,
    )
    assert result.evaluable
    assert result.answer_check_category == "estimable_and_generalizing"
    assert result.eligible_cell_count == 2
    assert result.model_individual_count_with_eligible_events == 3
    assert result.sealed_individual_count == 2
    assert result.information_nats is not None and result.information_nats > 0
    assert result.effective_vertical_states is not None and result.effective_vertical_states > 1
    assert len(result.local_cells) == 2
    assert all(score.scored_event_count == 16 for score in result.sealed_scores)
    assert all(score.mean_log_score_gain > 0 for score in result.sealed_scores)
    assert result.sealed_mean_log_score_gain > 0


def test_sealed_individuals_not_event_count_are_replication_units():
    rows = _synthetic_generalizing_rows()
    # Add many wrong-pattern events to s2 so its own mean becomes adverse. The
    # final category must be mixed rather than allowing s1's event count or the
    # pooled event total to vote it away.
    rows.extend(_row("s2", 0.1, 300) for _ in range(100))
    rows.extend(_row("s2", 1.1, 10) for _ in range(100))
    split = {"m1": "model", "m2": "model", "m3": "model", "s1": "sealed", "s2": "sealed"}
    result = evaluate_thickness_configuration(
        rows,
        height_field="height_above_msl",
        projector=lambda lon, lat: (lon, lat),
        cell_size_m=1,
        z_edges=(-math.inf, 0, 50, 100, 200, 400, math.inf),
        minimum_events_per_cell=3,
        minimum_distinct_model_individuals_per_cell=3,
        minimum_scored_events_per_sealed_individual=4,
        split=split,
    )
    gains = [score.mean_log_score_gain for score in result.sealed_scores]
    assert gains[0] > 0
    assert gains[1] < 0
    assert result.answer_check_category == "estimable_but_generalization_mixed"


def test_frozen_cell_set_cannot_silently_shrink_after_numeric_qc():
    rows = [
        _row("m1", 0.1, 10),
        _row("m2", 0.1, "nan"),
        _row("m3", 0.1, "nan"),
        _row("s1", 0.1, 10),
        _row("s2", 0.1, 10),
    ]
    split = {"m1": "model", "m2": "model", "m3": "model", "s1": "sealed", "s2": "sealed"}
    result = evaluate_thickness_configuration(
        rows,
        height_field="height_above_msl",
        projector=lambda lon, lat: (lon, lat),
        cell_size_m=1,
        z_edges=(-math.inf, 0, 50, math.inf),
        minimum_events_per_cell=3,
        minimum_distinct_model_individuals_per_cell=3,
        minimum_scored_events_per_sealed_individual=1,
        split=split,
        fixed_eligible_cells={(0, 0)},
    )
    assert not result.evaluable
    assert result.answer_check_category == "empirical_thickness_answer_check_unavailable"
    assert "finite_height_support_does_not_cover_all_frozen_eligible_cells" in result.unavailable_reasons


def test_outlier_exclusion_is_fixed_boolean_sensitivity_only():
    rows = _synthetic_generalizing_rows()
    rows.append(_row("m1", 0.1, 300, outlier="TRUE"))
    split = {"m1": "model", "m2": "model", "m3": "model", "s1": "sealed", "s2": "sealed"}
    kept = evaluate_thickness_configuration(
        rows,
        height_field="height_above_msl",
        projector=lambda lon, lat: (lon, lat),
        cell_size_m=1,
        z_edges=(-math.inf, 0, 50, 100, 200, 400, math.inf),
        minimum_events_per_cell=3,
        minimum_distinct_model_individuals_per_cell=3,
        minimum_scored_events_per_sealed_individual=4,
        split=split,
        exclude_marked_outliers=False,
    )
    excluded = evaluate_thickness_configuration(
        rows,
        height_field="height_above_msl",
        projector=lambda lon, lat: (lon, lat),
        cell_size_m=1,
        z_edges=(-math.inf, 0, 50, 100, 200, 400, math.inf),
        minimum_events_per_cell=3,
        minimum_distinct_model_individuals_per_cell=3,
        minimum_scored_events_per_sealed_individual=4,
        split=split,
        fixed_eligible_cells={(0, 0), (1, 0)},
        exclude_marked_outliers=True,
    )
    assert kept.evaluable and excluded.evaluable
    assert kept.fingerprint != excluded.fingerprint


def test_result_never_persists_raw_height_values():
    rows = _synthetic_generalizing_rows()
    rows.append(_row("m1", 0.1, 987654321.123))
    split = {"m1": "model", "m2": "model", "m3": "model", "s1": "sealed", "s2": "sealed"}
    result = evaluate_thickness_configuration(
        rows,
        height_field="height_above_msl",
        projector=lambda lon, lat: (lon, lat),
        cell_size_m=1,
        z_edges=(-math.inf, 0, 50, 100, 200, 400, math.inf),
        minimum_events_per_cell=3,
        minimum_distinct_model_individuals_per_cell=3,
        minimum_scored_events_per_sealed_individual=4,
        split=split,
    )
    serialized = json.dumps(result.as_dict(), sort_keys=True)
    assert "987654321" not in serialized
    assert "height_min" not in serialized
    assert "height_max" not in serialized
    assert "height_mean" not in serialized


def test_terminal_category_uses_frozen_qc_and_answer_check_only():
    rows = _synthetic_generalizing_rows()
    split = {"m1": "model", "m2": "model", "m3": "model", "s1": "sealed", "s2": "sealed"}
    result = evaluate_thickness_configuration(
        rows,
        height_field="height_above_msl",
        projector=lambda lon, lat: (lon, lat),
        cell_size_m=1,
        z_edges=(-math.inf, 0, 50, 100, 200, 400, math.inf),
        minimum_events_per_cell=3,
        minimum_distinct_model_individuals_per_cell=3,
        minimum_scored_events_per_sealed_individual=4,
        split=split,
    )
    assert terminal_category_from_primary(
        finite_height_fraction=1.0,
        minimum_finite_height_fraction=0.99,
        primary=result,
    ) == "empirical_n2_thickness_generalizing"
    assert terminal_category_from_primary(
        finite_height_fraction=0.98,
        minimum_finite_height_fraction=0.99,
        primary=result,
    ) == "empirical_n2_thickness_unavailable"
