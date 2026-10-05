from __future__ import annotations

import json

import numpy as np
import pytest

from odsp.refit_information_transfer import RefitInformationLevelScores
from odsp.training_process_positive_pigeonhole_iut import (
    _pigeonhole_bootstrap_means,
    certify_training_process_positive_information_pigeonhole_iut_v3,
    certify_training_process_positive_pigeonhole_iut_v3,
)


PROCESS_SHA = "3" * 64


def _rows(group_count: int = 2, block_count: int = 8):
    groups = []
    blocks = []
    for group_index in range(group_count):
        for block_index in range(block_count):
            groups.append(f"g{group_index}")
            blocks.append(f"g{group_index}-b{block_index}")
    return tuple(groups), tuple(blocks)


def _audit(gain, **kwargs):
    groups, blocks = _rows()
    count = np.asarray(gain).shape[0]
    return certify_training_process_positive_pigeonhole_iut_v3(
        gain,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i:02d}" for i in range(count)),
        training_process_id="bootstrap-process-v3",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
        minimum_refits=8,
        minimum_blocks_per_group=8,
        **kwargs,
    )


def test_pigeonhole_bootstrap_means_match_scalar_reference():
    rng = np.random.default_rng(44)
    numerator = rng.normal(size=(5, 7, 3))
    weight = rng.uniform(0.2, 2.0, size=7)
    refit_draws = rng.integers(0, 5, size=(23, 5))
    block_draws = rng.integers(0, 7, size=(23, 7))
    observed = _pigeonhole_bootstrap_means(
        numerator, weight, refit_draws, block_draws
    )
    expected = []
    for rdraw, bdraw in zip(refit_draws, block_draws):
        sampled = numerator[rdraw][:, bdraw, :]
        denom = len(rdraw) * np.sum(weight[bdraw])
        expected.append(np.sum(sampled, axis=(0, 1)) / denom)
    np.testing.assert_allclose(observed, np.asarray(expected), atol=1e-12)


def test_common_location_shift_moves_lower_bound_exactly():
    groups, _ = _rows()
    rng = np.random.default_rng(91)
    base = rng.normal(size=(8, len(groups), 2))
    first = _audit(base, contrast_names=("a", "b"), seed=777)
    shift = 0.73
    second = _audit(base + shift, contrast_names=("a", "b"), seed=777)
    for left_contrast, right_contrast in zip(first.contrasts, second.contrasts):
        for left, right in zip(left_contrast.groups, right_contrast.groups):
            assert right.bootstrap_displacement_critical_value == pytest.approx(
                left.bootstrap_displacement_critical_value, abs=1e-12
            )
            assert right.lower_bound == pytest.approx(
                left.lower_bound + shift, abs=1e-12
            )


def test_v3_is_iut_not_simultaneous_cellwise_inference():
    groups, _ = _rows()
    result = _audit(np.full((8, len(groups), 2), 0.5))
    assert result.compound_intersection_union_test is True
    assert result.all_required_components_must_reject is True
    assert result.additional_component_multiplicity_correction_applied is False
    assert result.component_test_independence_assumed is False
    assert result.component_lower_bounds_are_simultaneous is False
    assert result.arbitrary_any_cell_familywise_claim_allowed is False
    assert result.studentization_used is False
    assert result.centered_bootstrap_displacement_used is True
    assert result.quantile_method == "higher"
    json.dumps(result.as_dict(), allow_nan=False)


def test_refit_order_with_ids_is_invariant():
    groups, blocks = _rows()
    rng = np.random.default_rng(17)
    gain = rng.normal(loc=0.4, scale=0.1, size=(8, len(groups), 2))
    ids = tuple(f"r{i}" for i in range(8))
    first = certify_training_process_positive_pigeonhole_iut_v3(
        gain,
        groups,
        blocks=blocks,
        refit_ids=ids,
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("a", "b"),
        bootstrap_draws=500,
        seed=123,
    )
    second = certify_training_process_positive_pigeonhole_iut_v3(
        gain[::-1],
        groups,
        blocks=blocks,
        refit_ids=ids[::-1],
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("a", "b"),
        bootstrap_draws=500,
        seed=123,
    )
    assert first.as_dict() == second.as_dict()


def test_too_few_refits_fail_closed():
    groups, blocks = _rows()
    result = certify_training_process_positive_pigeonhole_iut_v3(
        np.full((4, len(groups)), 0.5),
        groups,
        blocks=blocks,
        refit_ids=("a", "b", "c", "d"),
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
        minimum_refits=8,
    )
    assert result.all_cells_estimable is False
    assert result.contrasts[0].category == "unavailable"
    assert all(cell.lower_bound is None for cell in result.contrasts[0].groups)


def test_information_wrapper_keeps_non_skippable_ceiling():
    groups, blocks = _rows()
    n = len(groups)
    pooled = np.zeros((8, n))
    coarse = pooled + 0.45
    fine = coarse + 0.35
    result = certify_training_process_positive_information_pigeonhole_iut_v3(
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
    assert result.process_mean_certified_transfer_ceiling == "fine"
    assert result.compound_intersection_union_test is True
    assert result.fixed_set_intersection_used is False
    assert result.historical_fixed_set_results_reclassified is False


def test_richest_nonfinite_step_is_unavailable_and_json_safe():
    groups, blocks = _rows()
    n = len(groups)
    base = np.zeros((8, n))
    rich = np.full((8, n), 0.4)
    rich[0, 0] = -np.inf
    result = certify_training_process_positive_information_pigeonhole_iut_v3(
        (
            RefitInformationLevelScores("base", (), base),
            RefitInformationLevelScores("rich", ("context",), rich),
        ),
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i}" for i in range(8)),
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
    )
    assert result.process_mean_certified_transfer_ceiling == "base"
    assert result.process_audit.contrasts[0].category == "unavailable"
    json.dumps(result.as_dict(), allow_nan=False)
