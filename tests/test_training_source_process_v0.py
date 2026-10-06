from __future__ import annotations

import json
import numpy as np
import pytest

from odsp.training_source_process_v0 import (
    evaluate_training_source_process_positive_iut_v0,
)


PROCESS_SHA = "6" * 64


def _design(group_count=2, blocks_per_group=8):
    groups = []
    blocks = []
    for g in range(group_count):
        for b in range(blocks_per_group):
            groups.append(f"g{g}")
            blocks.append(f"g{g}-b{b}")
    return tuple(groups), tuple(blocks)


def _audit(gain, **kwargs):
    groups, blocks = _design()
    array = np.asarray(gain)
    source_count, inner_count = array.shape[:2]
    contrast_names = (
        ("a", "b")
        if array.ndim == 4 and array.shape[-1] == 2
        else None
    )
    return evaluate_training_source_process_positive_iut_v0(
        gain,
        groups,
        blocks=blocks,
        source_draw_ids=tuple(f"s{i:02d}" for i in range(source_count)),
        inner_refit_ids_by_source=tuple(
            tuple(f"r{j:02d}" for j in range(inner_count))
            for _ in range(source_count)
        ),
        source_process_id="source-process-v0",
        source_process_manifest_sha256=PROCESS_SHA,
        contrast_names=contrast_names,
        **kwargs,
    )


def test_inner_refits_are_averaged_before_outer_source_inference():
    groups, _ = _design()
    rng = np.random.default_rng(10)
    gain = rng.normal(size=(8, 8, len(groups), 2))
    result = _audit(gain)
    assert result.inner_refits_nested_within_source is True
    assert result.inner_refits_pooled_as_independent_source_draws is False
    assert result.source_draws_equally_weighted is True
    assert result.effective_training_cluster_count == 8
    assert result.source_draw_count == 8
    assert result.inner_refit_count_per_source == 8
    assert result.primary_confirmatory is False
    assert result.qualification_status == "experimental_prequalification"


def test_duplicating_identical_inner_refits_does_not_change_outer_inference():
    groups, _ = _design()
    rng = np.random.default_rng(11)
    base = rng.normal(loc=0.2, scale=0.3, size=(8, 8, len(groups), 2))
    doubled = np.repeat(base, 2, axis=1)
    first = _audit(base)
    second = _audit(doubled, minimum_inner_refits_per_source=8)
    for left_contrast, right_contrast in zip(first.contrasts, second.contrasts):
        for left, right in zip(left_contrast.groups, right_contrast.groups):
            assert right.source_process_mean_gain == pytest.approx(
                left.source_process_mean_gain, abs=1e-12
            )
            assert right.source_jackknife_variance == pytest.approx(
                left.source_jackknife_variance, abs=1e-12
            )
            assert right.validation_jackknife_variance == pytest.approx(
                left.validation_jackknife_variance, abs=1e-12
            )
            assert right.cv3two_standard_error == pytest.approx(
                left.cv3two_standard_error, abs=1e-12
            )
            assert right.lower_bound == pytest.approx(
                left.lower_bound, abs=1e-12
            )


def test_source_order_and_inner_order_are_invariant():
    groups, blocks = _design()
    rng = np.random.default_rng(12)
    gain = rng.normal(size=(8, 8, len(groups), 2))
    source_ids = tuple(f"s{i}" for i in range(8))
    inner = tuple(tuple(f"r{j}" for j in range(8)) for _ in range(8))

    first = evaluate_training_source_process_positive_iut_v0(
        gain,
        groups,
        blocks=blocks,
        source_draw_ids=source_ids,
        inner_refit_ids_by_source=inner,
        source_process_id="p",
        source_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("a", "b"),
    )
    second = evaluate_training_source_process_positive_iut_v0(
        gain[::-1, ::-1],
        groups,
        blocks=blocks,
        source_draw_ids=source_ids[::-1],
        inner_refit_ids_by_source=tuple(
            tuple(reversed(ids)) for ids in inner[::-1]
        ),
        source_process_id="p",
        source_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("a", "b"),
    )
    assert first.source_draw_ids == second.source_draw_ids
    assert first.effective_training_cluster_count == second.effective_training_cluster_count
    assert first.group_count == second.group_count
    assert first.contrast_count == second.contrast_count
    for left_contrast, right_contrast in zip(first.contrasts, second.contrasts):
        assert left_contrast.contrast == right_contrast.contrast
        assert left_contrast.category == right_contrast.category
        for left, right in zip(left_contrast.groups, right_contrast.groups):
            assert left.group == right.group
            assert left.status == right.status
            assert left.estimable == right.estimable
            assert left.t_degrees_of_freedom == right.t_degrees_of_freedom
            for field in (
                "source_process_mean_gain",
                "source_jackknife_variance",
                "validation_jackknife_variance",
                "cv3two_variance",
                "cv3two_standard_error",
                "one_sided_t_critical_value",
                "lower_bound",
            ):
                assert getattr(right, field) == pytest.approx(
                    getattr(left, field), abs=1e-12
                )


def test_too_few_source_draws_fail_closed_even_with_many_inner_refits():
    groups, blocks = _design()
    gain = np.full((4, 40, len(groups), 1), 0.5)
    result = evaluate_training_source_process_positive_iut_v0(
        gain,
        groups,
        blocks=blocks,
        source_draw_ids=("s0", "s1", "s2", "s3"),
        inner_refit_ids_by_source=tuple(
            tuple(f"r{j}" for j in range(40)) for _ in range(4)
        ),
        source_process_id="p",
        source_process_manifest_sha256=PROCESS_SHA,
        minimum_source_draws=8,
        minimum_inner_refits_per_source=8,
    )
    assert result.all_cells_estimable is False
    assert result.effective_training_cluster_count == 4
    assert result.contrasts[0].category == "unavailable"


def test_v0_output_is_json_safe_and_does_not_claim_superpopulation():
    groups, _ = _design()
    result = _audit(np.full((8, 8, len(groups), 2), 0.5))
    assert result.original_source_superpopulation_generalization_claimed is False
    assert result.fixed_set_results_reclassified is False
    assert result.qualified_v5_results_reclassified is False
    json.dumps(result.as_dict(), allow_nan=False)
