from __future__ import annotations

import math

import numpy as np
import pytest

from odsp.information_transfer import InformationLevelScore
from odsp.information_transfer_v2 import certify_information_transfer_v2
from odsp.multicontrast_bootstrap_t import certify_independent_group_contrasts_v2


def _two_groups(block_count: int = 12):
    groups = ["a"] * block_count + ["b"] * block_count
    blocks = [f"a-{i:02d}" for i in range(block_count)] + [
        f"b-{i:02d}" for i in range(block_count)
    ]
    return groups, blocks


def test_multicontrast_v2_certifies_full_group_by_contrast_family():
    groups, blocks = _two_groups()
    gains = []
    for group in ("a", "b"):
        for index in range(12):
            coarse = 0.35 + 0.02 * ((index % 4) - 1.5)
            fine = 0.18 + 0.01 * ((index % 3) - 1.0)
            if group == "b":
                coarse += 0.03
                fine += 0.02
            gains.append([coarse, fine])

    result = certify_independent_group_contrasts_v2(
        gains,
        groups,
        blocks=blocks,
        contrast_names=["coarse", "fine"],
        bootstrap_draws=1000,
        minimum_blocks_per_group=8,
        seed=41,
    )

    assert result.schema_version == 2
    assert result.group_count == 2
    assert result.contrast_count == 2
    assert result.cell_count == result.estimable_cell_count == 4
    assert result.replicate_studentization_recomputed is True
    assert result.same_block_draw_shared_across_contrasts_within_group is True
    assert result.validation_group_independence_assumed is True
    assert result.bootstrap_t_critical_value is not None
    assert all(row.category == "robust_generalizing" for row in result.contrasts)


def test_one_failed_fine_group_cannot_be_rescued_by_other_contrasts():
    groups, blocks = _two_groups()
    gains = []
    for group in ("a", "b"):
        for index in range(12):
            coarse = 0.30 + 0.01 * ((index % 4) - 1.5)
            fine = 0.15 if group == "a" else -0.15
            gains.append([coarse, fine])

    result = certify_independent_group_contrasts_v2(
        gains,
        groups,
        blocks=blocks,
        contrast_names=["coarse", "fine"],
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )

    by_name = {row.contrast: row for row in result.contrasts}
    assert by_name["coarse"].category == "robust_generalizing"
    assert by_name["fine"].category == "mixed"


def test_nonfinite_one_cell_is_unavailable_without_erasing_other_contrast():
    groups, blocks = _two_groups()
    gains = [[0.3, 0.2] for _ in groups]
    gains[-1][1] = -math.inf
    result = certify_independent_group_contrasts_v2(
        gains,
        groups,
        blocks=blocks,
        contrast_names=["coarse", "fine"],
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )
    by_name = {row.contrast: row for row in result.contrasts}
    assert by_name["coarse"].category == "robust_generalizing"
    assert by_name["fine"].category == "unavailable"
    assert by_name["fine"].unavailable_group_count == 1


def test_multicontrast_v2_is_row_order_invariant():
    groups, blocks = _two_groups()
    gains = np.asarray(
        [
            [0.2 + 0.01 * (index % 5), 0.1 + 0.005 * (index % 4)]
            for index in range(len(groups))
        ]
    )
    first = certify_independent_group_contrasts_v2(
        gains,
        groups,
        blocks=blocks,
        contrast_names=["x", "y"],
        bootstrap_draws=1000,
        seed=77,
    )
    order = np.arange(len(groups))[::-1]
    second = certify_independent_group_contrasts_v2(
        gains[order],
        [groups[index] for index in order],
        blocks=[blocks[index] for index in order],
        contrast_names=["x", "y"],
        bootstrap_draws=1000,
        seed=77,
    )
    assert second.bootstrap_t_critical_value == pytest.approx(
        first.bootstrap_t_critical_value,
        abs=1e-12,
    )
    left = {
        (summary.contrast, cell.group): cell
        for summary in first.contrasts
        for cell in summary.groups
    }
    right = {
        (summary.contrast, cell.group): cell
        for summary in second.contrasts
        for cell in summary.groups
    }
    for key in left:
        assert right[key].mean_gain == pytest.approx(left[key].mean_gain, abs=1e-12)
        assert right[key].lower_bound == pytest.approx(left[key].lower_bound, abs=1e-12)
        assert right[key].upper_bound == pytest.approx(left[key].upper_bound, abs=1e-12)


def test_information_transfer_v2_has_non_skippable_certified_ceiling():
    groups, blocks = _two_groups()
    n = len(groups)
    pooled = np.zeros(n)
    species = np.full(n, 0.4)
    full = np.empty(n)
    for index, group in enumerate(groups):
        full[index] = 0.6 if group == "a" else 0.3

    result = certify_information_transfer_v2(
        [
            InformationLevelScore("pooled", (), pooled),
            InformationLevelScore("species", ("species",), species),
            InformationLevelScore(
                "species_context",
                ("species", "context"),
                full,
            ),
        ],
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )

    assert result.point_result.predictive_result.total_gain_category == "generalizing"
    assert result.point_result.predictive_result.all_group_point_transfer_ceiling == "species"
    assert result.certified_transfer_ceiling == "species"
    assert result.bootstrap_t_audit.contrasts[0].category == "robust_generalizing"
    assert result.bootstrap_t_audit.contrasts[1].category == "mixed"
    assert result.upstream_refit_uncertainty_included is False


def test_information_transfer_v2_rejects_non_nested_filtration():
    groups, blocks = _two_groups()
    n = len(groups)
    with pytest.raises(ValueError, match="not nested"):
        certify_information_transfer_v2(
            [
                InformationLevelScore("species", ("species",), np.zeros(n)),
                InformationLevelScore("context", ("context",), np.ones(n)),
            ],
            groups,
            blocks=blocks,
            bootstrap_draws=500,
        )
