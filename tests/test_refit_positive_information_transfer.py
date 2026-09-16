from __future__ import annotations

import numpy as np

from odsp.refit_information_transfer import RefitInformationLevelScores
from odsp.refit_positive_information_transfer import (
    certify_refit_positive_information_transfer,
)


def _design(refit_count: int = 8, group_count: int = 3, blocks_per_group: int = 8):
    groups: list[str] = []
    blocks: list[str] = []
    for group_index in range(group_count):
        for block_index in range(blocks_per_group):
            groups.append(f"g{group_index}")
            blocks.append(f"g{group_index}-b{block_index}")
    n = len(groups)
    pooled = np.zeros((refit_count, n), dtype=float)
    coarse = np.full((refit_count, n), 0.40, dtype=float)
    fine = np.full((refit_count, n), 0.70, dtype=float)
    ids = tuple(f"r{index:02d}" for index in range(refit_count))
    levels = (
        RefitInformationLevelScores("pooled", (), pooled),
        RefitInformationLevelScores("coarse", ("coarse",), coarse),
        RefitInformationLevelScores("fine", ("coarse", "fine"), fine),
    )
    return levels, tuple(groups), tuple(blocks), ids


def test_all_refits_positive_certify_full_consensus_ceiling():
    levels, groups, blocks, ids = _design()
    result = certify_refit_positive_information_transfer(
        levels,
        groups,
        blocks=blocks,
        refit_ids=ids,
        reference_refit_id="r00",
        bootstrap_draws=500,
        minimum_refits=8,
        minimum_blocks_per_group=8,
    )
    assert result.minimum_refits_satisfied is True
    assert result.refit_consensus_certified_transfer_ceiling == "fine"
    assert result.reference_refit_certified_transfer_ceiling == "fine"
    assert result.refit_ceiling_stability == "stable"
    assert all(row.refit_consensus_category == "robust_generalizing" for row in result.steps)
    assert result.refit_ensemble_probability_sample_assumed is False
    assert result.population_refit_confidence_claimed is False
    assert result.validation_confidence_is_conditional_on_each_refit is True


def test_reference_full_cannot_rescue_one_refit_fine_failure():
    levels, groups, blocks, ids = _design()
    matrices = [np.asarray(level.score, dtype=float).copy() for level in levels]
    matrices[2][7, :] = matrices[1][7, :] - 0.20
    altered = tuple(
        RefitInformationLevelScores(level.name, level.information, matrix)
        for level, matrix in zip(levels, matrices)
    )
    result = certify_refit_positive_information_transfer(
        altered,
        groups,
        blocks=blocks,
        refit_ids=ids,
        reference_refit_id="r00",
        bootstrap_draws=500,
        minimum_refits=8,
        minimum_blocks_per_group=8,
    )
    assert result.reference_refit_certified_transfer_ceiling == "fine"
    assert result.refit_consensus_certified_transfer_ceiling == "coarse"
    assert result.refit_ceiling_stability == "variable"
    assert result.steps[0].refit_consensus_category == "robust_generalizing"
    assert result.steps[1].refit_consensus_category == "not_robust_generalizing"
    assert result.steps[1].robust_positive_refit_count == 7
    assert result.reference_refit_can_override_consensus_failure is False


def test_refit_order_does_not_change_consensus_result():
    levels, groups, blocks, ids = _design()
    forward = certify_refit_positive_information_transfer(
        levels,
        groups,
        blocks=blocks,
        refit_ids=ids,
        reference_refit_id="r03",
        bootstrap_draws=500,
    )
    reversed_levels = tuple(
        RefitInformationLevelScores(
            level.name,
            level.information,
            np.asarray(level.score, dtype=float)[::-1],
        )
        for level in levels
    )
    reverse = certify_refit_positive_information_transfer(
        reversed_levels,
        groups,
        blocks=blocks,
        refit_ids=ids[::-1],
        reference_refit_id="r03",
        bootstrap_draws=500,
    )
    assert reverse.refit_ids == forward.refit_ids
    assert reverse.per_refit_certified_transfer_ceilings == forward.per_refit_certified_transfer_ceilings
    assert reverse.refit_consensus_certified_transfer_ceiling == forward.refit_consensus_certified_transfer_ceiling
    assert [row.refit_consensus_category for row in reverse.steps] == [
        row.refit_consensus_category for row in forward.steps
    ]


def test_insufficient_refit_count_fails_consensus_closed():
    levels, groups, blocks, ids = _design(refit_count=4)
    result = certify_refit_positive_information_transfer(
        levels,
        groups,
        blocks=blocks,
        refit_ids=ids,
        reference_refit_id="r00",
        bootstrap_draws=500,
        minimum_refits=8,
    )
    assert result.minimum_refits_satisfied is False
    assert result.refit_consensus_certified_transfer_ceiling == "pooled"
    assert all(row.refit_consensus_category == "unavailable" for row in result.steps)


def test_nonfinite_richest_score_in_one_refit_stops_consensus_at_coarse():
    levels, groups, blocks, ids = _design()
    matrices = [np.asarray(level.score, dtype=float).copy() for level in levels]
    matrices[2][5, 0] = -np.inf
    altered = tuple(
        RefitInformationLevelScores(level.name, level.information, matrix)
        for level, matrix in zip(levels, matrices)
    )
    result = certify_refit_positive_information_transfer(
        altered,
        groups,
        blocks=blocks,
        refit_ids=ids,
        reference_refit_id="r00",
        bootstrap_draws=500,
    )
    assert result.refit_consensus_certified_transfer_ceiling == "coarse"
    assert result.steps[1].refit_consensus_category == "unavailable"
    assert result.steps[1].unavailable_refit_count == 1
