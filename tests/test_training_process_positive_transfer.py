from __future__ import annotations

import json

import numpy as np
import pytest

from odsp.positive_transfer_bootstrap_t import (
    certify_independent_group_positive_transfer_v2,
)
from odsp.refit_information_transfer import RefitInformationLevelScores
from odsp.refit_positive_robustness import (
    certify_all_refit_positive_information_transfer_v2,
)
from odsp.training_process_positive_transfer import (
    _bootstrap_components,
    _crossed_components,
    certify_training_process_positive_information_transfer_v1,
    certify_training_process_positive_transfer_v1,
)


PROCESS_SHA = "a" * 64


def _rows(group_count: int = 2, block_count: int = 8):
    groups = []
    blocks = []
    for group_index in range(group_count):
        for block_index in range(block_count):
            groups.append(f"g{group_index}")
            blocks.append(f"g{group_index}-b{block_index}")
    return tuple(groups), tuple(blocks)


def _core(gain, **kwargs):
    groups, blocks = _rows()
    return certify_training_process_positive_transfer_v1(
        gain,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i:02d}" for i in range(np.asarray(gain).shape[0])),
        training_process_id="bootstrap-training-v1",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
        minimum_refits=8,
        minimum_blocks_per_group=8,
        **kwargs,
    )


def test_vectorized_crossed_bootstrap_matches_replicate_reference():
    rng = np.random.default_rng(991)
    numerator = rng.normal(size=(5, 7, 3))
    weight = rng.uniform(0.5, 1.5, size=7)
    refit_draws = rng.integers(0, 5, size=(23, 5))
    block_draws = rng.integers(0, 7, size=(23, 7))

    means, ses = _bootstrap_components(
        numerator,
        weight,
        refit_draws,
        block_draws,
    )
    for draw_index in range(refit_draws.shape[0]):
        local = numerator[
            refit_draws[draw_index]
        ][:, block_draws[draw_index], :]
        local_weight = weight[block_draws[draw_index]]
        mean, _, _, _, se, _ = _crossed_components(local, local_weight)
        assert means[draw_index] == pytest.approx(mean, abs=1e-12)
        assert ses[draw_index] == pytest.approx(se, abs=1e-12)


def test_identical_refits_reduce_to_validation_only_one_sided_route():
    groups, blocks = _rows()
    n = len(groups)
    base = np.column_stack(
        [
            0.30 + np.linspace(-0.02, 0.02, n),
            0.45 + np.linspace(-0.01, 0.01, n),
        ]
    )
    process = _core(np.repeat(base[None, :, :], 8, axis=0))
    validation = certify_independent_group_positive_transfer_v2(
        base,
        groups,
        blocks=blocks,
        contrast_names=("contrast-000", "contrast-001"),
        bootstrap_draws=500,
        seed=20261004,
        minimum_blocks_per_group=8,
    )

    assert process.bootstrap_t_critical_value == pytest.approx(
        validation.bootstrap_t_critical_value,
        abs=1e-12,
    )
    for pcontrast, vcontrast in zip(process.contrasts, validation.contrasts):
        for pcell, vcell in zip(pcontrast.groups, vcontrast.groups):
            assert pcell.training_process_standard_error == pytest.approx(0.0)
            assert pcell.validation_block_standard_error == pytest.approx(
                vcell.studentizing_standard_error,
                abs=1e-12,
            )
            assert pcell.lower_bound == pytest.approx(vcell.lower_bound, abs=1e-12)


def test_process_mean_and_fixed_set_answer_different_questions():
    groups, blocks = _rows()
    n = len(groups)
    effects = np.array([0.42, 0.46, 0.50, 0.54, 0.58, 0.62, 0.66, -0.02])
    gain = np.repeat(effects[:, None], n, axis=1)

    process = _core(gain)
    assert process.contrasts[0].category == "robust_generalizing"
    assert process.fixed_set_intersection_used is False
    assert process.process_mean_target is True
    assert process.individual_future_refit_success_probability_claimed is False
    assert process.all_possible_refits_positive_claimed is False

    levels = (
        RefitInformationLevelScores(
            "base",
            (),
            np.zeros_like(gain),
        ),
        RefitInformationLevelScores(
            "rich",
            ("context",),
            gain,
        ),
    )
    fixed = certify_all_refit_positive_information_transfer_v2(
        levels,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i:02d}" for i in range(8)),
        bootstrap_draws=500,
        minimum_refits=2,
        minimum_blocks_per_group=8,
    )
    assert fixed.all_refit_certified_transfer_ceiling == "base"
    assert fixed.step_robustness[0].category == "not_robust_across_refits"


def test_more_process_draws_reduce_training_component_when_empirical_spread_repeats():
    groups, _ = _rows()
    n = len(groups)
    effects = np.linspace(-0.20, 0.20, 8)
    gain8 = np.repeat((0.40 + effects)[:, None], n, axis=1)
    gain32 = np.tile(gain8, (4, 1))

    small = _core(gain8)
    large = certify_training_process_positive_transfer_v1(
        gain32,
        groups,
        blocks=_rows()[1],
        refit_ids=tuple(f"r{i:02d}" for i in range(32)),
        training_process_id="bootstrap-training-v1",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
        minimum_refits=8,
        minimum_blocks_per_group=8,
    )

    small_se = small.contrasts[0].groups[0].training_process_standard_error
    large_se = large.contrasts[0].groups[0].training_process_standard_error
    assert small_se is not None and large_se is not None
    assert large_se < small_se
    assert small.contrasts[0].groups[0].validation_block_standard_error == pytest.approx(0.0)
    assert large.contrasts[0].groups[0].validation_block_standard_error == pytest.approx(0.0)


def test_too_few_training_process_draws_fail_closed():
    groups, blocks = _rows()
    gain = np.full((4, len(groups)), 0.4)
    result = certify_training_process_positive_transfer_v1(
        gain,
        groups,
        blocks=blocks,
        refit_ids=("a", "b", "c", "d"),
        training_process_id="bootstrap-training-v1",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
        minimum_refits=8,
        minimum_blocks_per_group=8,
    )

    assert result.all_cells_estimable is False
    assert result.bootstrap_t_critical_value is None
    assert result.contrasts[0].category == "unavailable"
    assert all(cell.lower_bound is None for cell in result.contrasts[0].groups)


def test_refit_id_reordering_is_invariant():
    groups, blocks = _rows()
    n = len(groups)
    gain = np.repeat(np.linspace(0.25, 0.45, 8)[:, None], n, axis=1)
    ids = tuple(f"r{i}" for i in range(8))

    first = certify_training_process_positive_transfer_v1(
        gain,
        groups,
        blocks=blocks,
        refit_ids=ids,
        training_process_id="bootstrap-training-v1",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
    )
    second = certify_training_process_positive_transfer_v1(
        gain[::-1],
        groups,
        blocks=blocks,
        refit_ids=ids[::-1],
        training_process_id="bootstrap-training-v1",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
    )
    assert first.as_dict() == second.as_dict()


def test_crossed_axis_semantics_are_explicit_and_serializable():
    groups, _ = _rows()
    result = _core(np.full((8, len(groups)), 0.4))

    assert result.training_refit_draws_resampled_per_replicate == 8
    assert result.same_refit_resample_shared_across_all_cells is True
    assert result.same_validation_block_draw_shared_across_contrasts_within_group is True
    assert result.validation_blocks_redrawn_per_refit is False
    assert result.training_and_validation_axes_resampled_independently is True
    assert result.crossed_interaction_retained_in_bootstrap_distribution is True
    assert result.crossed_interaction_separately_identified_in_studentizer is True
    assert result.multiway_inclusion_exclusion_studentizer is True
    assert result.max_one_way_variance_safeguard is True
    assert all(
        cell.intersection_cell_standard_error is not None
        for contrast in result.contrasts
        for cell in contrast.groups
    )
    json.dumps(result.as_dict(), allow_nan=False)


def test_invalid_process_digest_is_rejected():
    groups, blocks = _rows()
    with pytest.raises(ValueError, match="SHA256"):
        certify_training_process_positive_transfer_v1(
            np.full((8, len(groups)), 0.4),
            groups,
            blocks=blocks,
            refit_ids=tuple(f"r{i}" for i in range(8)),
            training_process_id="bootstrap-training-v1",
            training_process_manifest_sha256="not-a-digest",
            bootstrap_draws=500,
        )


def test_information_wrapper_keeps_non_skippable_process_mean_ceiling():
    groups, blocks = _rows()
    n = len(groups)
    refit_count = 8
    pooled = np.zeros((refit_count, n))
    coarse = np.full((refit_count, n), 0.35)
    fine = coarse + 0.25
    levels = (
        RefitInformationLevelScores("pooled", (), pooled),
        RefitInformationLevelScores("coarse", ("species",), coarse),
        RefitInformationLevelScores(
            "fine",
            ("species", "context"),
            fine,
        ),
    )

    result = certify_training_process_positive_information_transfer_v1(
        levels,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i}" for i in range(refit_count)),
        training_process_id="bootstrap-training-v1",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
    )
    assert result.process_mean_certified_transfer_ceiling == "fine"
    assert result.fixed_set_intersection_used is False
    assert result.historical_fixed_set_results_reclassified is False


def test_richest_zero_support_makes_step_unavailable_without_nonfinite_json():
    groups, blocks = _rows()
    n = len(groups)
    refit_count = 8
    base = np.zeros((refit_count, n))
    rich = np.full((refit_count, n), 0.4)
    rich[0, 0] = -np.inf

    result = certify_training_process_positive_information_transfer_v1(
        (
            RefitInformationLevelScores("base", (), base),
            RefitInformationLevelScores("rich", ("context",), rich),
        ),
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i}" for i in range(refit_count)),
        training_process_id="bootstrap-training-v1",
        training_process_manifest_sha256=PROCESS_SHA,
        bootstrap_draws=500,
    )
    assert result.process_mean_certified_transfer_ceiling == "base"
    assert result.process_audit.contrasts[0].category == "unavailable"
    json.dumps(result.as_dict(), allow_nan=False)
