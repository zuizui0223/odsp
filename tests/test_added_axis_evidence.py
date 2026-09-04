from __future__ import annotations

import math

import numpy as np
import pytest

from odsp import evaluate_added_axis_evidence
from odsp.niche_geometry import conditional_information, effective_conditional_states
from odsp.transferability import base_added_mutual_information


def test_generic_evaluator_matches_component_metrics_for_multi_axis_partition():
    support = np.arange(1, 2 * 3 * 4 * 2 + 1, dtype=float).reshape(2, 3, 4, 2)
    result = evaluate_added_axis_evidence(
        support,
        base_axes=(0, 3),
        added_axes=(2, 1),
    )

    assert result.transferability is None
    assert result.profile.base_axes == (0, 3)
    assert result.profile.added_axes == (2, 1)
    assert result.profile.conditional_information_nats == pytest.approx(
        conditional_information(support, base_axes=(0, 3), added_axes=(2, 1))
    )
    assert result.profile.effective_added_states == pytest.approx(
        effective_conditional_states(support, base_axes=(0, 3), added_axes=(2, 1))
    )
    assert result.profile.organization_information_nats == pytest.approx(
        base_added_mutual_information(support, base_axes=(0, 3), added_axes=(2, 1))
    )


def test_same_generic_api_handles_height_time_behaviour_and_microhabitat_semantics():
    # The arrays differ only in how a caller would interpret the state axes.  The
    # generic evaluator is deliberately semantic-name agnostic.
    examples = {
        "height": np.asarray([[3.0, 1.0], [1.0, 3.0]]),
        "time": np.asarray([[5.0, 2.0, 1.0], [1.0, 2.0, 5.0]]),
        "behaviour": np.asarray([[8.0, 1.0, 1.0, 2.0], [1.0, 7.0, 2.0, 2.0]]),
        "microhabitat": np.asarray([[4.0, 2.0], [2.0, 4.0], [1.0, 5.0]]),
    }

    for semantic_name, support in examples.items():
        result = evaluate_added_axis_evidence(
            support,
            base_axes=(0,),
            added_axes=(1,),
            heldout_supports=[("replicate-a", support.copy())],
            gain_tolerance=0.0,
        )
        assert semantic_name  # documents the intended portability examples
        assert result.profile.conditional_information_nats > 0
        assert result.profile.effective_added_states > 1
        assert result.transferability is not None
        assert result.transferability.classification == "generalizing"
        assert result.transferability.gains[0] == pytest.approx(
            result.profile.organization_information_nats
        )


def test_generic_evaluator_is_group_mass_invariant():
    model = np.asarray([[3.0, 1.0], [1.0, 3.0]])
    shifted = model[::-1].copy()

    first = evaluate_added_axis_evidence(
        model,
        base_axes=(0,),
        added_axes=(1,),
        heldout_supports=[("same", model), ("shifted", shifted)],
        gain_tolerance=0.0,
    )
    second = evaluate_added_axis_evidence(
        model * 1e7,
        base_axes=(0,),
        added_axes=(1,),
        heldout_supports=[("same", model * 1e-8), ("shifted", shifted * 1e10)],
        gain_tolerance=0.0,
    )

    assert first.transferability is not None
    assert second.transferability is not None
    assert first.transferability.classification == second.transferability.classification == "mixed"
    assert second.transferability.gains == pytest.approx(first.transferability.gains)


def test_generic_evaluator_rejects_overlapping_or_empty_axis_sets():
    support = np.ones((2, 3, 4), dtype=float)

    with pytest.raises(ValueError, match="base_axes"):
        evaluate_added_axis_evidence(support, base_axes=(), added_axes=(2,))
    with pytest.raises(ValueError, match="added_axes"):
        evaluate_added_axis_evidence(support, base_axes=(0,), added_axes=())
    with pytest.raises(ValueError, match="disjoint"):
        evaluate_added_axis_evidence(support, base_axes=(0, 1), added_axes=(1, 2))


def test_effective_states_is_exact_for_uniform_arbitrary_added_joint_state():
    # One base axis and a two-axis added state with 3*4 equally likely joint
    # states.  The generic API should return exactly 12 effective added states.
    support = np.ones((5, 3, 4), dtype=float)
    result = evaluate_added_axis_evidence(
        support,
        base_axes=(0,),
        added_axes=(1, 2),
    )

    assert result.profile.conditional_information_nats == pytest.approx(math.log(12.0))
    assert result.profile.effective_added_states == pytest.approx(12.0)
    assert result.profile.organization_information_nats == pytest.approx(0.0, abs=1e-12)
