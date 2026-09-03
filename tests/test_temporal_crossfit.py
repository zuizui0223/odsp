import math

import numpy as np
import pytest

from odsp.crossfitted_transferability import score_crossfitted_independent_groups
from odsp.temporal_crossfit import score_identity_temporal_crossfitted_groups
from odsp.temporal_partition import classify_grouped_temporal_partition_result


def _stable_model(strength: float) -> np.ndarray:
    model = np.zeros((2, 2), dtype=float)
    model[0, :] = [strength, 1.0]
    model[1, :] = [1.0, strength]
    return model


def test_crossfitted_groups_allow_distinct_training_models():
    model_a = _stable_model(3.0)
    model_b = _stable_model(9.0)
    result = score_crossfitted_independent_groups(
        {
            "fold-0": (model_a, model_a.copy()),
            "fold-1": (model_b, model_b.copy()),
        },
        base_axes=(0,),
        added_axes=(1,),
        gain_tolerance=0.0,
    )

    assert result.classification == "generalizing"
    assert result.groups[0].score.model_total_mass != result.groups[1].score.model_total_mass
    assert all(gain > 0.0 for gain in result.gains)


def test_temporal_crossfit_preserves_mixed_fold_failure():
    stable_a = _stable_model(3.0)
    stable_b = _stable_model(9.0)
    shifted = stable_b[::-1].copy()

    grouped = score_identity_temporal_crossfitted_groups(
        {
            "site-fold-0": (stable_a, stable_a.copy()),
            "site-fold-1": (stable_b, stable_b.copy()),
            "site-fold-2": (stable_b, shifted),
        },
        identity_axis=0,
        time_axis=1,
        gain_tolerance=0.0,
    )

    assert grouped.gains[0] > 0.0
    assert grouped.gains[1] > 0.0
    assert grouped.gains[2] < 0.0
    assert grouped.classification == "mixed"

    decision = classify_grouped_temporal_partition_result(
        math.log(2.0),
        [0.0] * 199,
        grouped,
        alpha=0.05,
    )
    assert decision.terminal_category == "temporal_partition_present_mixed_transfer"
    assert decision.heldout_group_ids == (
        "site-fold-0",
        "site-fold-1",
        "site-fold-2",
    )
    assert decision.gain_tolerance == 0.0


def test_crossfit_unknown_masks_fail_closed():
    stable = _stable_model(3.0)
    mask = np.zeros_like(stable, dtype=bool)
    with pytest.raises(ValueError, match="unknown groups"):
        score_crossfitted_independent_groups(
            {"fold-0": (stable, stable.copy())},
            base_axes=(0,),
            added_axes=(1,),
            model_unavailable_masks={"other": mask},
        )


def test_temporal_crossfit_rejects_identity_time_axis_collision():
    stable = _stable_model(3.0)
    with pytest.raises(ValueError, match="must be distinct"):
        score_identity_temporal_crossfitted_groups(
            {"fold-0": (stable, stable.copy())},
            identity_axis=0,
            time_axis=0,
        )
