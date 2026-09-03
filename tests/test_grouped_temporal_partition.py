import math

import numpy as np
import pytest

from odsp.temporal_partition import (
    TemporalPartitionDecision,
    classify_grouped_temporal_partition_result,
    classify_temporal_partition_result,
    score_identity_temporal_groups,
)


def _three_site_partition() -> np.ndarray:
    support = np.zeros((3, 2, 4), dtype=float)
    for site in range(3):
        support[site, 0, 0:2] = 1.0
        support[site, 1, 2:4] = 1.0
    return support


def test_temporal_groups_score_independent_sites_without_pooling_mass():
    support = _three_site_partition()
    model = np.zeros_like(support)
    model[0] = support[0]
    site_b = np.zeros_like(support)
    site_c = np.zeros_like(support)
    site_b[1] = support[1]
    site_c[2] = support[2] * 1000.0

    grouped = score_identity_temporal_groups(
        model,
        {"site-b": site_b, "site-c": site_c},
        identity_axis=1,
        time_axis=2,
        gain_tolerance=0.0,
    )

    assert grouped.classification == "generalizing"
    assert grouped.gains[0] == pytest.approx(math.log(2.0))
    assert grouped.gains[1] == pytest.approx(math.log(2.0))


def test_shifted_temporal_group_makes_transfer_mixed():
    support = _three_site_partition()
    model = np.zeros_like(support)
    stable = np.zeros_like(support)
    shifted = np.zeros_like(support)
    model[0] = support[0]
    stable[1] = support[1]
    shifted[2, 0, 2:4] = 1.0
    shifted[2, 1, 0:2] = 1.0

    grouped = score_identity_temporal_groups(
        model,
        {"stable": stable, "shifted": shifted},
        identity_axis=1,
        time_axis=2,
        gain_tolerance=0.0,
    )

    assert grouped.gains[0] > 0.0
    assert grouped.gains[1] == float("-inf")
    assert grouped.classification == "mixed"


def test_grouped_temporal_decision_preserves_group_ids_and_tolerance():
    support = _three_site_partition()
    model = np.zeros_like(support)
    site_b = np.zeros_like(support)
    site_c = np.zeros_like(support)
    model[0] = support[0]
    site_b[1] = support[1]
    site_c[2] = support[2]
    grouped = score_identity_temporal_groups(
        model,
        {"site-b": site_b, "site-c": site_c},
        identity_axis=1,
        time_axis=2,
        gain_tolerance=0.0,
    )

    decision = classify_grouped_temporal_partition_result(
        math.log(2.0),
        [0.0] * 99,
        grouped,
        alpha=0.05,
    )

    assert decision.terminal_category == "temporal_partition_generalizing"
    assert decision.heldout_group_ids == ("site-b", "site-c")
    assert decision.heldout_gains == pytest.approx(grouped.gains)
    assert decision.gain_tolerance == 0.0
    assert isinstance(decision.as_dict()["heldout_group_ids"], list)


def test_nonzero_gain_tolerance_is_recorded_and_reproducible():
    decision = classify_temporal_partition_result(
        math.log(2.0),
        [0.0] * 99,
        [0.01, 0.02],
        alpha=0.05,
        gain_tolerance=0.015,
        heldout_group_ids=["a", "b"],
    )

    assert decision.transfer_category == "mixed"
    assert decision.terminal_category == "temporal_partition_present_mixed_transfer"
    assert decision.gain_tolerance == pytest.approx(0.015)
    assert decision.heldout_group_ids == ("a", "b")


def test_temporal_decision_cannot_be_forged():
    with pytest.raises(ValueError, match="terminal_category is inconsistent"):
        TemporalPartitionDecision(
            observed_partition_information_nats=math.log(2.0),
            null_draw_count=99,
            permutation_p_value=0.01,
            alpha=0.05,
            heldout_gains=(0.2, 0.1),
            transfer_category="generalizing",
            terminal_category="temporal_partition_present_not_generalizing",
            gain_tolerance=0.0,
            heldout_group_ids=("a", "b"),
        )


def test_temporal_group_ids_must_align_with_gains():
    with pytest.raises(ValueError, match="one-to-one"):
        classify_temporal_partition_result(
            math.log(2.0),
            [0.0] * 99,
            [0.2, 0.1],
            heldout_group_ids=["only-one"],
        )
