import math

import numpy as np
import pytest

from odsp.temporal_crossfit import score_identity_temporal_crossfitted_groups
from odsp.temporal_partition import (
    classify_grouped_temporal_partition_result,
    classify_temporal_partition_result,
)
from scripts import run_n2_serengeti_temporal_partition as lane


def _support(*, shift_last_site: bool) -> tuple[np.ndarray, np.ndarray]:
    support = np.zeros((3, 2, 4), dtype=float)
    for site in range(3):
        support[site, 0, 0:2] = [3.0, 1.0]
        support[site, 1, 2:4] = [1.0, 3.0]
    if shift_last_site:
        support[2] = support[2, ::-1, :]
    folds = np.asarray([0, 1, 2], dtype=int)
    return support, folds


def _crossfit_pairs(
    support: np.ndarray,
    folds: np.ndarray,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    pairs = {}
    for fold in range(lane.N_FOLDS):
        model = support[folds != fold].sum(axis=0) + lane.PSEUDOCOUNT
        heldout = support[folds == fold].sum(axis=0)
        pairs[f"site-fold-{fold}"] = (model, heldout)
    return pairs


@pytest.mark.parametrize("shift_last_site", [False, True])
def test_frozen_runner_gains_equal_crossfitted_api(shift_last_site: bool):
    support, folds = _support(shift_last_site=shift_last_site)

    frozen_gains = lane._heldout_gains(support, folds)
    grouped = score_identity_temporal_crossfitted_groups(
        _crossfit_pairs(support, folds),
        identity_axis=0,
        time_axis=1,
        gain_tolerance=0.0,
    )

    assert grouped.gains == pytest.approx(frozen_gains, abs=1e-12)
    assert tuple(group.group_id for group in grouped.groups) == (
        "site-fold-0",
        "site-fold-1",
        "site-fold-2",
    )


@pytest.mark.parametrize("shift_last_site", [False, True])
def test_frozen_and_grouped_terminal_classifiers_are_equivalent(shift_last_site: bool):
    support, folds = _support(shift_last_site=shift_last_site)
    frozen_gains = lane._heldout_gains(support, folds)
    grouped = score_identity_temporal_crossfitted_groups(
        _crossfit_pairs(support, folds),
        identity_axis=0,
        time_axis=1,
        gain_tolerance=0.0,
    )

    observed = math.log(2.0)
    null = [0.0] * lane.N_PERMUTATIONS
    frozen = classify_temporal_partition_result(
        observed,
        null,
        frozen_gains,
        alpha=lane.ALPHA,
        gain_tolerance=0.0,
    )
    grouped_decision = classify_grouped_temporal_partition_result(
        observed,
        null,
        grouped,
        alpha=lane.ALPHA,
    )

    assert grouped_decision.heldout_gains == pytest.approx(frozen.heldout_gains, abs=1e-12)
    assert grouped_decision.transfer_category == frozen.transfer_category
    assert grouped_decision.terminal_category == frozen.terminal_category
    assert grouped_decision.permutation_p_value == pytest.approx(
        frozen.permutation_p_value,
        abs=1e-12,
    )
