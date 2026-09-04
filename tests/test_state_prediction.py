import math

import numpy as np
import pytest

from odsp.state_prediction import (
    encode_state_events,
    fit_state_resolved_events,
    fit_state_resolved_model,
    score_state_prediction_groups,
    score_state_probability_field,
)
from odsp.transferability import base_added_mutual_information


def test_native_state_model_returns_rich_probability_summary():
    support = np.array([[90.0, 10.0], [10.0, 90.0]])
    model = fit_state_resolved_model(
        support,
        base_axes=(0,),
        added_axes=(1,),
        alpha=0.0,
    )

    summary = model.summarize((0,))
    assert summary.probabilities == pytest.approx((0.9, 0.1))
    assert summary.dominant_added_state == (0,)
    assert summary.dominant_probability == pytest.approx(0.9)
    expected_entropy = -(0.9 * math.log(0.9) + 0.1 * math.log(0.1))
    assert summary.entropy_nats == pytest.approx(expected_entropy)
    assert summary.effective_states == pytest.approx(math.exp(expected_entropy))
    assert summary.training_mass == pytest.approx(100.0)
    assert summary.seen_in_training is True


def test_same_process_prediction_gain_matches_mutual_information():
    support = np.array([[90.0, 10.0], [10.0, 90.0]])
    model = fit_state_resolved_model(
        support,
        base_axes=(0,),
        added_axes=(1,),
        alpha=0.0,
    )
    score = model.score(support)
    mutual_information = base_added_mutual_information(
        support,
        base_axes=(0,),
        added_axes=(1,),
    )

    assert score.mean_log_score_gain == pytest.approx(mutual_information)
    assert score.conditional_brier_score == pytest.approx(0.18)
    assert score.marginal_brier_score == pytest.approx(0.5)
    assert score.brier_improvement == pytest.approx(0.32)
    assert score.top1_accuracy == pytest.approx(0.9)
    assert score.marginal_top1_accuracy == pytest.approx(0.5)
    assert score.top1_improvement == pytest.approx(0.4)
    assert score.seen_base_mass_fraction == pytest.approx(1.0)


def test_shifted_state_structure_has_negative_heldout_gain():
    training = np.array([[90.0, 10.0], [10.0, 90.0]])
    reversed_test = np.array([[10.0, 90.0], [90.0, 10.0]])
    model = fit_state_resolved_model(
        training,
        base_axes=(0,),
        added_axes=(1,),
        alpha=0.0,
    )
    score = model.score(reversed_test)

    assert score.mean_log_score_gain < 0
    assert score.brier_improvement < 0
    assert score.top1_accuracy == pytest.approx(0.1)


def test_multi_added_axis_prediction_returns_joint_state():
    support = np.zeros((2, 2, 3), dtype=float)
    support[0, 1, 2] = 8.0
    support[0, 0, 0] = 2.0
    support[1, 0, 1] = 7.0
    support[1, 1, 2] = 3.0
    model = fit_state_resolved_model(
        support,
        base_axes=(0,),
        added_axes=(1, 2),
        alpha=0.0,
    )

    summary = model.summarize((0,))
    assert summary.added_shape == (2, 3)
    assert len(summary.probabilities) == 6
    assert summary.dominant_added_state == (1, 2)
    assert summary.dominant_probability == pytest.approx(0.8)


def test_unseen_base_state_backs_off_to_marginal_distribution():
    support = np.array([[8.0, 2.0], [2.0, 8.0], [0.0, 0.0]])
    model = fit_state_resolved_model(
        support,
        base_axes=(0,),
        added_axes=(1,),
        alpha=0.5,
        unseen_base_policy="marginal",
    )

    assert model.seen_base_mask.tolist() == [True, True, False]
    assert model.predict_distribution((2,)) == pytest.approx(model.marginal_probability)
    summary = model.summarize((2,))
    assert summary.seen_in_training is False
    assert summary.training_mass == pytest.approx(0.0)


def test_unseen_base_error_policy_fails_closed():
    support = np.array([[8.0, 2.0], [0.0, 0.0]])
    model = fit_state_resolved_model(
        support,
        base_axes=(0,),
        added_axes=(1,),
        alpha=0.5,
        unseen_base_policy="error",
    )
    with pytest.raises(ValueError, match="not seen in training"):
        model.predict_distribution((1,))


def test_groupwise_state_prediction_preserves_conflicting_groups():
    training = np.array([[90.0, 10.0], [10.0, 90.0]])
    stable = training.copy()
    reversed_test = np.array([[10.0, 90.0], [90.0, 10.0]])
    model = fit_state_resolved_model(
        training,
        base_axes=(0,),
        added_axes=(1,),
        alpha=0.5,
    )

    grouped = score_state_prediction_groups(
        model,
        {"stable": stable, "shifted": reversed_test},
    )
    assert grouped.gain_category == "mixed"
    assert grouped.groups[0][1].mean_log_score_gain > 0
    assert grouped.groups[1][1].mean_log_score_gain < 0


def test_external_probability_field_uses_same_odsp_metrics():
    probability = np.array([[0.8, 0.2], [0.2, 0.8]])
    heldout = np.array([[8.0, 2.0], [2.0, 8.0]])
    score = score_state_probability_field(
        probability,
        heldout,
        base_ndim=1,
        marginal_probability=np.array([0.5, 0.5]),
        seen_base_mask=np.array([True, True]),
    )

    assert score.mean_log_score_gain > 0
    assert score.conditional_brier_score == pytest.approx(0.32)
    assert score.marginal_brier_score == pytest.approx(0.5)
    assert score.top1_accuracy == pytest.approx(0.8)
    assert score.mean_assigned_probability == pytest.approx(0.68)


def test_zero_unsmoothed_probability_is_recorded_as_predictive_failure():
    training = np.array([[10.0, 0.0], [0.0, 10.0]])
    heldout = np.array([[0.0, 10.0], [0.0, 10.0]])
    model = fit_state_resolved_model(
        training,
        base_axes=(0,),
        added_axes=(1,),
        alpha=0.0,
    )
    score = model.score(heldout)
    assert score.mean_log_score == float("-inf")
    assert score.mean_log_score_gain == float("-inf")


def test_event_table_encoder_and_label_prediction():
    base = ["site-a", "site-a", "site-b", "site-b", "site-b"]
    added = ["night", "night", "day", "day", "night"]
    encoded = encode_state_events(base, added)
    assert encoded.support.shape == (2, 2)
    assert encoded.base_levels == (("site-a", "site-b"),)
    assert encoded.added_levels == (("night", "day"),)

    fitted = fit_state_resolved_events(base, added, alpha=0.5)
    site_a = fitted.summarize(("site-a",))
    assert site_a["dominant_added_state_labels"] == ("night",)
    assert site_a["dominant_probability"] > 0.5


def test_event_weights_are_preserved_in_support():
    encoded = encode_state_events(
        ["a", "a", "b"],
        ["night", "day", "day"],
        weights=[5.0, 1.0, 2.0],
    )
    assert float(encoded.support.sum()) == pytest.approx(8.0)
    assert encoded.support[0, 0] == pytest.approx(5.0)
    assert encoded.support[0, 1] == pytest.approx(1.0)
    assert encoded.support[1, 1] == pytest.approx(2.0)
