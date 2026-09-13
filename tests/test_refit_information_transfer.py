from __future__ import annotations

import math

import numpy as np
import pytest

from odsp.refit_information_transfer import (
    RefitInformationLevelScores,
    certify_refit_information_transfer,
)


def _fixture(*, reverse_refits: bool = False, reverse_rows: bool = False):
    refit_ids = [f"r{index}" for index in range(8)]
    fine_increment = np.asarray([0.30, 0.20, 0.10, -0.30, -0.40, -0.20, -0.10, 0.00])
    groups = np.asarray(["g1"] * 4 + ["g2"] * 4, dtype=object)
    blocks = np.asarray(
        [f"g1-b{i}" for i in range(4)] + [f"g2-b{i}" for i in range(4)],
        dtype=object,
    )
    pooled = np.full((8, 8), -1.0)
    species = np.full((8, 8), -0.5)
    full = species + fine_increment[:, None]

    if reverse_refits:
        order = np.arange(7, -1, -1)
        refit_ids = [refit_ids[index] for index in order]
        pooled = pooled[order]
        species = species[order]
        full = full[order]
    if reverse_rows:
        order = np.arange(7, -1, -1)
        groups = groups[order]
        blocks = blocks[order]
        pooled = pooled[:, order]
        species = species[:, order]
        full = full[:, order]

    levels = (
        RefitInformationLevelScores("pooled", (), pooled),
        RefitInformationLevelScores("species", ("species",), species),
        RefitInformationLevelScores(
            "species_context",
            ("species", "context"),
            full,
        ),
    )
    return levels, groups, blocks, refit_ids


def _run(*, reverse_refits: bool = False, reverse_rows: bool = False, minimum_refits: int = 8):
    levels, groups, blocks, refit_ids = _fixture(
        reverse_refits=reverse_refits,
        reverse_rows=reverse_rows,
    )
    return certify_refit_information_transfer(
        levels,
        groups,
        blocks=blocks,
        refit_ids=refit_ids,
        reference_refit_id="r0",
        nested_draws=1200,
        seed=20260913,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=2,
    )


def test_reference_fit_can_reach_full_resolution_while_refit_aware_ceiling_stops():
    result = _run()

    assert result.reference_refit_id == "r0"
    assert result.reference_fit_point_transfer_ceiling == "species_context"
    assert result.reference_fit_certified_transfer_ceiling == "species_context"
    assert result.ensemble_point_transfer_ceiling == "species"
    assert result.refit_aware_certified_transfer_ceiling == "species"
    assert result.refit_ceiling_stability == "refit_sensitive"
    assert set(result.refit_point_transfer_ceilings) == {"species", "species_context"}

    first, second = result.steps
    assert first.ensemble_point_category == "generalizing"
    assert first.refit_aware_category == "robust_generalizing"
    assert first.refit_category_stability == "stable"
    assert second.ensemble_point_category == "non_generalizing"
    assert second.refit_aware_category != "robust_generalizing"
    assert second.refit_category_stability == "refit_sensitive"

    assert result.same_selected_refit_shared_across_all_group_step_cells is True
    assert result.same_block_draw_shared_across_steps_within_group is True
    assert result.reference_fit_can_override_refit_aware_failure is False
    assert result.total_gain_can_override_failed_step is False
    assert result.automatic_refit_scheme_inference is False
    assert sum(result.selected_refit_draw_counts) == result.nested_draws


def test_refit_and_row_order_do_not_change_certification():
    reference = _run()
    reversed_refits = _run(reverse_refits=True)
    reversed_rows = _run(reverse_rows=True)

    for other in (reversed_refits, reversed_rows):
        assert other.refit_ids == reference.refit_ids
        assert other.reference_refit_id == reference.reference_refit_id
        assert other.refit_aware_certified_transfer_ceiling == reference.refit_aware_certified_transfer_ceiling
        assert other.ensemble_point_transfer_ceiling == reference.ensemble_point_transfer_ceiling
        assert other.max_t_critical_value == pytest.approx(reference.max_t_critical_value)
        assert [step.refit_aware_category for step in other.steps] == [
            step.refit_aware_category for step in reference.steps
        ]


def test_too_few_refits_fail_closed_without_destroying_reference_fit_result():
    result = _run(minimum_refits=9)

    assert result.all_cells_estimable is False
    assert result.estimable_cell_count == 0
    assert result.max_t_critical_value is None
    assert result.refit_aware_certified_transfer_ceiling == "pooled"
    assert result.reference_fit_certified_transfer_ceiling == "species_context"
    assert all(step.refit_aware_category == "unavailable" for step in result.steps)


def test_zero_support_in_one_richest_refit_stops_only_the_affected_fine_step():
    levels, groups, blocks, refit_ids = _fixture()
    full = np.asarray(levels[-1].score, dtype=float).copy()
    full[3, 0] = -math.inf
    levels = (
        levels[0],
        levels[1],
        RefitInformationLevelScores(
            "species_context",
            ("species", "context"),
            full,
        ),
    )

    result = certify_refit_information_transfer(
        levels,
        groups,
        blocks=blocks,
        refit_ids=refit_ids,
        reference_refit_id="r0",
        nested_draws=600,
        seed=13,
        minimum_refits=8,
        minimum_blocks_per_group=2,
    )

    assert result.steps[0].refit_aware_category == "robust_generalizing"
    assert result.steps[1].refit_aware_category == "unavailable"
    assert result.refit_aware_certified_transfer_ceiling == "species"
    assert result.reference_fit_certified_transfer_ceiling == "species_context"


def test_non_nested_information_filtration_is_rejected_before_resampling():
    levels, groups, blocks, refit_ids = _fixture()
    invalid = (
        levels[0],
        levels[1],
        RefitInformationLevelScores("context_only", ("context",), levels[2].score),
    )
    with pytest.raises(ValueError, match="not nested"):
        certify_refit_information_transfer(
            invalid,
            groups,
            blocks=blocks,
            refit_ids=refit_ids,
            nested_draws=500,
            minimum_refits=2,
            minimum_blocks_per_group=2,
        )


def test_comparator_zero_support_in_any_refit_fails_closed():
    levels, groups, blocks, refit_ids = _fixture()
    species = np.asarray(levels[1].score, dtype=float).copy()
    species[2, 0] = -math.inf
    invalid = (
        levels[0],
        RefitInformationLevelScores("species", ("species",), species),
        levels[2],
    )
    with pytest.raises(ValueError, match="comparator level 'species' must be finite"):
        certify_refit_information_transfer(
            invalid,
            groups,
            blocks=blocks,
            refit_ids=refit_ids,
            nested_draws=500,
            minimum_refits=2,
            minimum_blocks_per_group=2,
        )
