from __future__ import annotations

import json
import math

import numpy as np
import pytest

from odsp.refit_information_transfer import RefitInformationLevelScores
from odsp.training_process_future_refit_success_probability import (
    PROCESS_ALPHA,
    VALIDATION_ALPHA,
    certify_future_refit_success_probability_v1,
    certify_training_process_future_refit_success_probability_v1,
    exact_binomial_success_probability_lower_bound,
)


PROCESS_SHA = "6" * 64


def _rows(group_count: int = 2, block_count: int = 8):
    groups, blocks = [], []
    for group_index in range(group_count):
        for block_index in range(block_count):
            groups.append(f"g{group_index}")
            blocks.append(f"g{group_index}-b{block_index}")
    return tuple(groups), tuple(blocks)


def _audit(gain, **kwargs):
    groups, blocks = _rows()
    count = np.asarray(gain).shape[0]
    return certify_future_refit_success_probability_v1(
        gain,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i:02d}" for i in range(count)),
        training_process_id="future-refit-probability-test",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
        minimum_refits=8,
        minimum_blocks_per_group=8,
        **kwargs,
    )


def test_exact_binomial_lower_bound_known_edges_and_monotonicity():
    assert exact_binomial_success_probability_lower_bound(
        0, 8, alpha=0.025
    ) == 0.0
    assert exact_binomial_success_probability_lower_bound(
        8, 8, alpha=0.025
    ) == pytest.approx(0.6305833524471807, abs=1e-14)
    assert exact_binomial_success_probability_lower_bound(
        20, 20, alpha=0.025
    ) == pytest.approx(0.8315665290169146, abs=1e-14)

    values = [
        exact_binomial_success_probability_lower_bound(k, 8, alpha=0.025)
        for k in range(9)
    ]
    assert values == sorted(values)
    assert all(0.0 <= value <= 1.0 for value in values)


def test_all_eight_constant_positive_refits_do_not_imply_high_certainty():
    groups, _ = _rows()
    result = _audit(
        np.full((8, len(groups), 2), 0.5),
        contrast_names=("step-a", "step-b"),
    )
    assert result.certified_success_count == 8
    assert result.observed_certified_success_fraction == 1.0
    assert result.future_refit_success_probability_lower_bound == pytest.approx(
        0.6305833524471807,
        abs=1e-14,
    )
    assert (
        result.maximum_possible_lower_bound_if_all_observed_refits_certified
        == pytest.approx(0.6305833524471807, abs=1e-14)
    )
    assert result.validation_alpha == VALIDATION_ALPHA == 0.025
    assert result.process_alpha == PROCESS_ALPHA == 0.025
    assert result.overall_one_sided_alpha == pytest.approx(0.05)
    assert result.individual_future_refit_success_probability_is_estimand is True
    assert result.process_mean_is_estimand is False
    assert result.all_future_refits_positive_claimed is False
    assert result.fixed_set_intersection_used is False


def test_one_boundary_refit_is_not_certified_even_when_other_refits_pass():
    groups, _ = _rows()
    gain = np.full((8, len(groups), 2), 0.5)
    gain[7, :, :] = 0.0
    result = _audit(gain, contrast_names=("a", "b"))

    assert result.certified_success_count == 7
    assert result.per_refit[-1].certified_success is False
    assert result.per_refit[-1].robust_positive_cell_count == 0
    assert all(row.certified_success for row in result.per_refit[:-1])
    assert result.future_refit_success_probability_lower_bound < (
        result.maximum_possible_lower_bound_if_all_observed_refits_certified
    )


def test_unavailable_cell_counts_as_uncertified_not_success():
    groups, _ = _rows()
    gain = np.full((8, len(groups), 2), 0.5)
    gain[0, 0, 1] = -np.inf
    result = _audit(gain, contrast_names=("a", "b"))

    assert result.certified_success_count == 7
    first = result.per_refit[0]
    assert first.certified_success is False
    assert first.all_required_cells_estimable is False
    assert result.all_observed_refits_evaluable is False
    json.dumps(result.as_dict(), allow_nan=False)


def test_refit_id_reordering_is_invariant():
    groups, blocks = _rows()
    rng = np.random.default_rng(73)
    gain = rng.normal(loc=0.45, scale=0.08, size=(8, len(groups), 2))
    ids = tuple(f"r{i}" for i in range(8))
    settings = dict(
        groups=groups,
        blocks=blocks,
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("a", "b"),
        bootstrap_draws=500,
        seed=991,
        minimum_refits=8,
        minimum_blocks_per_group=8,
    )
    first = certify_future_refit_success_probability_v1(
        gain,
        refit_ids=ids,
        **settings,
    )
    second = certify_future_refit_success_probability_v1(
        gain[::-1],
        refit_ids=ids[::-1],
        **settings,
    )
    assert first.as_dict() == second.as_dict()


def test_common_gain_shift_moves_every_estimable_validation_bound_exactly():
    groups, _ = _rows()
    rng = np.random.default_rng(88)
    base = rng.normal(loc=0.0, scale=0.15, size=(8, len(groups), 2))
    first = _audit(base, contrast_names=("a", "b"), seed=440)
    shift = 0.73
    second = _audit(base + shift, contrast_names=("a", "b"), seed=440)

    assert second.validation_bootstrap_t_critical_value == pytest.approx(
        first.validation_bootstrap_t_critical_value,
        abs=1e-12,
    )
    for left, right in zip(first.cells, second.cells):
        if left.lower_bound is None:
            assert right.lower_bound is None
        else:
            assert right.lower_bound == pytest.approx(
                left.lower_bound + shift,
                abs=1e-12,
            )


def test_validation_family_includes_refit_group_and_contrast_axes():
    groups, _ = _rows(group_count=3, block_count=8)
    result = certify_future_refit_success_probability_v1(
        np.full((8, len(groups), 2), 0.4),
        groups,
        blocks=tuple(
            f"g{group_index}-b{block_index}"
            for group_index in range(3)
            for block_index in range(8)
        ),
        refit_ids=tuple(f"r{i}" for i in range(8)),
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("a", "b"),
        bootstrap_draws=500,
    )
    assert result.required_cell_count_per_refit == 6
    assert result.total_validation_family_cell_count == 48
    assert result.training_refits_resampled_in_validation_stage is False
    assert (
        result.same_validation_block_draw_shared_across_refits_and_contrasts_within_group
        is True
    )
    assert result.validation_groups_resampled_independently is True


def test_information_wrapper_is_frozen_to_two_ordered_contrasts():
    groups, blocks = _rows()
    n = len(groups)
    pooled = np.zeros((8, n))
    coarse = pooled + 0.4
    fine = coarse + 0.3
    result = certify_training_process_future_refit_success_probability_v1(
        (
            RefitInformationLevelScores("pooled", (), pooled),
            RefitInformationLevelScores("coarse", ("species",), coarse),
            RefitInformationLevelScores(
                "fine", ("species", "context"), fine
            ),
        ),
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i}" for i in range(8)),
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
    )
    assert result.levels == ("pooled", "coarse", "fine")
    assert len(result.steps) == 2
    assert result.audit.certified_success_count == 8

    richer = RefitInformationLevelScores(
        "richer",
        ("species", "context", "time"),
        fine + 0.2,
    )
    with pytest.raises(ValueError, match="exactly three ordered information levels"):
        certify_training_process_future_refit_success_probability_v1(
            (
                RefitInformationLevelScores("pooled", (), pooled),
                RefitInformationLevelScores("coarse", ("species",), coarse),
                RefitInformationLevelScores(
                    "fine", ("species", "context"), fine
                ),
                richer,
            ),
            groups,
            blocks=blocks,
            refit_ids=tuple(f"r{i}" for i in range(8)),
            training_process_id="p",
            training_process_manifest_sha256=PROCESS_SHA,
            bootstrap_draws=500,
        )


def test_small_refit_sample_fails_closed_by_certified_count():
    groups, blocks = _rows()
    result = certify_future_refit_success_probability_v1(
        np.full((4, len(groups), 2), 0.5),
        groups,
        blocks=blocks,
        refit_ids=("a", "b", "c", "d"),
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
        minimum_refits=8,
    )
    assert result.certified_success_count == 0
    assert result.future_refit_success_probability_lower_bound == 0.0
    assert result.all_observed_refits_evaluable is False
