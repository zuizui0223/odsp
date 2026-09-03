import math

import numpy as np

from odsp.temporal_partition import (
    classify_temporal_partition_result,
    score_identity_temporal_transferability,
    temporal_partition_profile,
)


def _partitioned_support() -> np.ndarray:
    # site × identity × 4-hour-like time state.
    support = np.zeros((2, 2, 4), dtype=float)
    for site in range(2):
        support[site, 0, 0:2] = 1.0
        support[site, 1, 2:4] = 1.0
    return support


def test_temporal_partition_profile_recovers_perfect_partition():
    profile = temporal_partition_profile(
        _partitioned_support(),
        context_axes=(0,),
        identity_axis=1,
        time_axis=2,
    )

    assert math.isclose(
        profile.temporal_information_given_context_nats,
        math.log(4.0),
        rel_tol=1e-12,
    )
    assert math.isclose(
        profile.effective_temporal_states_given_context,
        4.0,
        rel_tol=1e-12,
    )
    assert math.isclose(
        profile.identity_time_partition_information_nats,
        math.log(2.0),
        rel_tol=1e-12,
    )


def test_temporal_partition_is_zero_when_identities_share_time_distribution():
    support = np.ones((3, 2, 4), dtype=float)
    profile = temporal_partition_profile(
        support,
        context_axes=(0,),
        identity_axis=1,
        time_axis=2,
    )
    assert math.isclose(
        profile.identity_time_partition_information_nats,
        0.0,
        abs_tol=1e-12,
    )


def test_identity_temporal_pattern_transfers_to_independent_site():
    support = _partitioned_support()
    model = np.zeros_like(support)
    heldout = np.zeros_like(support)
    model[0] = support[0]
    heldout[1] = support[1]

    score = score_identity_temporal_transferability(
        model,
        heldout,
        identity_axis=1,
        time_axis=2,
    )
    assert math.isclose(score.mean_log_score_gain, math.log(2.0), rel_tol=1e-12)
    assert score.gain_category == "positive"


def test_shifted_temporal_partition_is_valid_negative_transfer():
    model = np.zeros((2, 2, 4), dtype=float)
    heldout = np.zeros_like(model)
    model[0, 0, 0:2] = 1.0
    model[0, 1, 2:4] = 1.0
    heldout[1, 0, 2:4] = 1.0
    heldout[1, 1, 0:2] = 1.0

    score = score_identity_temporal_transferability(
        model,
        heldout,
        identity_axis=1,
        time_axis=2,
    )
    assert score.mean_log_score_gain == float("-inf")
    assert score.gain_category == "negative"


def test_decision_requires_partition_and_all_positive_transfer():
    decision = classify_temporal_partition_result(
        math.log(2.0),
        [0.0] * 99,
        [0.2, 0.1, 0.05],
        alpha=0.05,
    )
    assert math.isclose(decision.permutation_p_value, 0.01)
    assert decision.transfer_category == "generalizing"
    assert decision.terminal_category == "temporal_partition_generalizing"


def test_detected_partition_is_not_rescued_when_transfer_fails():
    decision = classify_temporal_partition_result(
        math.log(2.0),
        [0.0] * 99,
        [-0.1, -0.2, -0.3],
        alpha=0.05,
    )
    assert decision.terminal_category == "temporal_partition_present_not_generalizing"


def test_no_detected_partition_remains_terminal_even_with_positive_gain():
    decision = classify_temporal_partition_result(
        0.0,
        [0.0] * 99,
        [0.1, 0.1, 0.1],
        alpha=0.05,
    )
    assert decision.permutation_p_value == 1.0
    assert decision.terminal_category == "temporal_partition_not_detected"
