import math

import numpy as np
import pytest

from odsp.niche_geometry import niche_thickness_profile
from odsp.transferability import (
    base_added_mutual_information,
    classify_independent_gains,
    score_conditional_transferability,
)


def test_same_known_truth_geometry_recovers_positive_organization_gain():
    model = np.zeros((2, 1, 2), dtype=float)
    model[0, 0, :] = [9.0, 1.0]
    model[1, 0, :] = [1.0, 9.0]

    score = score_conditional_transferability(
        model,
        model,
        base_axes=(0, 1),
        added_axes=(2,),
    )
    information = base_added_mutual_information(
        model,
        base_axes=(0, 1),
        added_axes=(2,),
    )

    assert score.mean_log_score_gain > 0.0
    assert score.mean_log_score_gain == pytest.approx(information)
    assert score.in_sample_organization_information_nats == pytest.approx(information)
    assert score.gain_category == "positive"


def test_niche_can_be_thick_but_have_no_base_resolved_organization():
    support = np.ones((2, 1, 4), dtype=float)
    thickness = niche_thickness_profile(
        support,
        horizontal_axes=(0, 1),
        vertical_axis=2,
    )
    score = score_conditional_transferability(
        support,
        support,
        base_axes=(0, 1),
        added_axes=(2,),
    )

    assert thickness.effective_vertical_states == pytest.approx(4.0)
    assert thickness.vertical_information_nats == pytest.approx(math.log(4.0))
    assert score.in_sample_organization_information_nats == pytest.approx(0.0)
    assert score.mean_log_score_gain == pytest.approx(0.0)
    assert score.gain_category == "neutral"


def test_shifted_heldout_geometry_can_make_conditioning_predictively_harmful():
    model = np.zeros((2, 1, 2), dtype=float)
    model[0, 0, :] = [9.0, 1.0]
    model[1, 0, :] = [1.0, 9.0]
    heldout = model[::-1].copy()

    score = score_conditional_transferability(
        model,
        heldout,
        base_axes=(0, 1),
        added_axes=(2,),
    )

    assert score.in_sample_organization_information_nats > 0.0
    assert score.mean_log_score_gain < 0.0
    assert score.gain_category == "negative"


def test_zero_conditional_probability_is_negative_infinity_not_silently_smoothed():
    model = np.zeros((2, 1, 2), dtype=float)
    model[0, 0, 0] = 1.0
    model[1, 0, 1] = 1.0
    heldout = np.zeros_like(model)
    heldout[0, 0, 1] = 1.0

    score = score_conditional_transferability(
        model,
        heldout,
        base_axes=(0, 1),
        added_axes=(2,),
    )

    assert score.mean_log_score_gain == float("-inf")
    assert score.gain_category == "negative"


def test_globally_unseen_heldout_added_state_fails_closed():
    model = np.zeros((1, 1, 2), dtype=float)
    model[0, 0, 0] = 1.0
    heldout = np.zeros_like(model)
    heldout[0, 0, 1] = 1.0

    with pytest.raises(ValueError, match="zero model marginal support"):
        score_conditional_transferability(
            model,
            heldout,
            base_axes=(0, 1),
            added_axes=(2,),
        )


def test_model_unavailable_state_cannot_receive_heldout_mass():
    model = np.ones((1, 1, 2), dtype=float)
    heldout = np.zeros_like(model)
    heldout[0, 0, 1] = 1.0
    unavailable = np.zeros_like(model, dtype=bool)
    unavailable[0, 0, 1] = True

    with pytest.raises(ValueError, match="model-unavailable"):
        score_conditional_transferability(
            model,
            heldout,
            base_axes=(0, 1),
            added_axes=(2,),
            model_unavailable_mask=unavailable,
        )


def test_axis_order_and_unlisted_axes_are_handled_explicitly():
    model = np.ones((2, 3, 4, 5), dtype=float)
    score = score_conditional_transferability(
        model,
        model,
        base_axes=(1, 0),
        added_axes=(3,),
    )

    assert score.base_axes == (1, 0)
    assert score.added_axes == (3,)
    assert score.mean_log_score_gain == pytest.approx(0.0)


def test_independent_gain_classification_is_conservative():
    assert classify_independent_gains([0.2, 0.1]) == "generalizing"
    assert classify_independent_gains([-0.2, 0.0]) == "non_generalizing"
    assert classify_independent_gains([0.2, -0.1]) == "mixed"
    assert classify_independent_gains([0.01, 0.02], tolerance=0.015) == "mixed"

    with pytest.raises(ValueError, match="at least one"):
        classify_independent_gains([])
