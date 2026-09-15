from __future__ import annotations

import numpy as np
import pytest

from odsp.refit_information_transfer import RefitInformationLevelScores
from odsp.refit_positive_robustness import (
    certify_all_refit_positive_information_transfer_v2,
    certify_all_refit_shared_block_positive_information_transfer_v2,
)


def _independent_rows(group_count: int = 3, block_count: int = 8):
    groups = []
    blocks = []
    for group_index in range(group_count):
        for block_index in range(block_count):
            groups.append(f"g{group_index}")
            blocks.append(f"g{group_index}-b{block_index}")
    return tuple(groups), tuple(blocks)


def _paired_rows(group_count: int = 3, block_count: int = 8):
    groups = []
    blocks = []
    for group_index in range(group_count):
        for block_index in range(block_count):
            groups.append(f"g{group_index}")
            blocks.append(f"b{block_index}")
    return tuple(groups), tuple(blocks)


def _levels(row_count: int, fine_gains: tuple[float, ...]):
    refit_count = len(fine_gains)
    pooled = np.zeros((refit_count, row_count), dtype=float)
    coarse = np.full((refit_count, row_count), 0.5, dtype=float)
    fine = coarse + np.asarray(fine_gains, dtype=float)[:, None]
    return (
        RefitInformationLevelScores("pooled", (), pooled),
        RefitInformationLevelScores("coarse", ("species",), coarse),
        RefitInformationLevelScores(
            "fine", ("species", "context"), fine
        ),
    )


def test_all_refits_full_reaches_full_ceiling_independent_groups():
    groups, blocks = _independent_rows()
    result = certify_all_refit_positive_information_transfer_v2(
        _levels(len(groups), (0.3, 0.3, 0.3)),
        groups,
        blocks=blocks,
        refit_ids=("r2", "r0", "r1"),
        bootstrap_draws=500,
        minimum_refits=2,
        minimum_blocks_per_group=8,
    )

    assert result.refit_ids == ("r0", "r1", "r2")
    assert result.all_refit_certified_transfer_ceiling == "fine"
    assert result.refit_certified_transfer_ceilings == ("fine", "fine", "fine")
    assert result.refit_ceiling_stability == "stable"
    assert all(row.category == "robust_across_refits" for row in result.step_robustness)
    assert result.intersection_union_rule_used is True
    assert result.additional_refit_axis_multiplicity_correction_applied is False
    assert result.refit_independence_assumed is False
    assert result.refit_sampling_distribution_assumed is False
    assert result.refit_population_generalization_claimed is False


def test_one_null_fine_refit_stops_global_ceiling_even_when_other_refits_pass():
    groups, blocks = _independent_rows()
    result = certify_all_refit_positive_information_transfer_v2(
        _levels(len(groups), (0.3, 0.3, 0.0)),
        groups,
        blocks=blocks,
        refit_ids=("good-a", "good-b", "null-fine"),
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )

    assert result.refit_certified_transfer_ceilings == ("fine", "fine", "coarse")
    assert result.refit_ceiling_stability == "refit_sensitive"
    assert result.all_refit_certified_transfer_ceiling == "coarse"
    assert result.step_robustness[0].category == "robust_across_refits"
    assert result.step_robustness[1].category == "not_robust_across_refits"
    assert result.step_robustness[1].robust_refit_count == 2
    assert result.step_robustness[1].not_robust_refit_count == 1
    assert result.reference_refit_can_override_failure is False
    assert result.refit_average_can_override_failure is False


def test_refit_id_and_matrix_reordering_is_invariant():
    groups, blocks = _independent_rows()
    first = certify_all_refit_positive_information_transfer_v2(
        _levels(len(groups), (0.3, 0.0, 0.2)),
        groups,
        blocks=blocks,
        refit_ids=("b", "a", "c"),
        bootstrap_draws=500,
    )
    second = certify_all_refit_positive_information_transfer_v2(
        _levels(len(groups), (0.2, 0.3, 0.0)),
        groups,
        blocks=blocks,
        refit_ids=("c", "b", "a"),
        bootstrap_draws=500,
    )

    assert second.refit_ids == first.refit_ids == ("a", "b", "c")
    assert second.refit_certified_transfer_ceilings == first.refit_certified_transfer_ceilings
    assert second.all_refit_certified_transfer_ceiling == first.all_refit_certified_transfer_ceiling
    assert [row.category for row in second.step_robustness] == [
        row.category for row in first.step_robustness
    ]


def test_too_few_refits_fail_global_robustness_closed_but_preserve_component_audit():
    groups, blocks = _independent_rows()
    result = certify_all_refit_positive_information_transfer_v2(
        _levels(len(groups), (0.3,)),
        groups,
        blocks=blocks,
        refit_ids=("only",),
        bootstrap_draws=500,
        minimum_refits=2,
    )

    assert result.robustness_evaluable is False
    assert result.refit_certified_transfer_ceilings == ("fine",)
    assert result.all_refit_certified_transfer_ceiling == "pooled"
    assert all(row.category == "unavailable" for row in result.step_robustness)


def test_nonfinite_richest_refit_makes_required_step_unavailable_and_stops():
    groups, blocks = _independent_rows()
    levels = list(_levels(len(groups), (0.3, 0.3)))
    fine = np.asarray(levels[-1].score, dtype=float).copy()
    fine[1, :] = -np.inf
    levels[-1] = RefitInformationLevelScores(
        "fine", ("species", "context"), fine
    )
    result = certify_all_refit_positive_information_transfer_v2(
        levels,
        groups,
        blocks=blocks,
        refit_ids=("finite", "zero-support"),
        bootstrap_draws=500,
    )

    assert result.all_refit_certified_transfer_ceiling == "coarse"
    assert result.step_robustness[1].category == "unavailable"
    assert result.step_robustness[1].unavailable_refit_count == 1


def test_nonfinite_comparator_in_any_refit_hard_stops():
    groups, blocks = _independent_rows()
    levels = list(_levels(len(groups), (0.3, 0.3)))
    coarse = np.asarray(levels[1].score, dtype=float).copy()
    coarse[1, 0] = -np.inf
    levels[1] = RefitInformationLevelScores("coarse", ("species",), coarse)

    with pytest.raises(ValueError, match="comparator level 'coarse' must be finite"):
        certify_all_refit_positive_information_transfer_v2(
            levels,
            groups,
            blocks=blocks,
            bootstrap_draws=500,
        )


def test_shared_block_refit_robustness_uses_same_intersection_rule():
    groups, shared_blocks = _paired_rows()
    result = certify_all_refit_shared_block_positive_information_transfer_v2(
        _levels(len(groups), (0.3, 0.0, 0.2)),
        groups,
        shared_blocks,
        refit_ids=("good-a", "null", "good-b"),
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )

    assert result.design == "shared_blocks"
    assert result.all_refit_certified_transfer_ceiling == "coarse"
    assert result.step_robustness[0].category == "robust_across_refits"
    assert result.step_robustness[1].category == "not_robust_across_refits"
    assert result.refit_independence_assumed is False


def test_shared_block_support_mismatch_still_hard_stops():
    groups = ("g0", "g0", "g1", "g1")
    shared_blocks = ("b0", "b1", "b0", "b2")
    with pytest.raises(ValueError, match="identical positive-mass block support"):
        certify_all_refit_shared_block_positive_information_transfer_v2(
            _levels(len(groups), (0.3, 0.3)),
            groups,
            shared_blocks,
            bootstrap_draws=500,
            minimum_shared_blocks=2,
        )
