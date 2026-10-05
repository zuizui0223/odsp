from __future__ import annotations

import json

import numpy as np
import pytest

from odsp.refit_information_transfer import RefitInformationLevelScores
from odsp.training_process_positive_cv3max_iut import (
    _cv3max_components,
    _student_t_cdf,
    _student_t_ppf,
    certify_training_process_positive_cv3max_iut_v4,
    certify_training_process_positive_information_cv3max_iut_v4,
)


PROCESS_SHA = "4" * 64


def _rows(group_count: int = 2, block_count: int = 8):
    groups, blocks = [], []
    for g in range(group_count):
        for b in range(block_count):
            groups.append(f"g{g}")
            blocks.append(f"g{g}-b{b}")
    return tuple(groups), tuple(blocks)


def _audit(gain, **kwargs):
    groups, blocks = _rows()
    count = np.asarray(gain).shape[0]
    return certify_training_process_positive_cv3max_iut_v4(
        gain,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i:02d}" for i in range(count)),
        training_process_id="process-v4",
        training_process_manifest_sha256=PROCESS_SHA,
        minimum_refits=8,
        minimum_blocks_per_group=8,
        **kwargs,
    )


def test_student_t_quantiles_match_known_values():
    assert _student_t_ppf(0.95, 7) == pytest.approx(
        1.894578605061305, abs=2e-12
    )
    assert _student_t_ppf(0.95, 19) == pytest.approx(
        1.729132811521367, abs=2e-12
    )
    for df in (7, 19, 40):
        q = _student_t_ppf(0.95, df)
        assert _student_t_cdf(q, df) == pytest.approx(0.95, abs=2e-13)


def test_cv3max_is_max_of_three_term_and_one_way_jackknife_variances():
    rng = np.random.default_rng(12)
    numerator = rng.normal(size=(8, 9, 3))
    weight = rng.uniform(0.5, 2.0, size=9)
    point, vr, vb, vi, vmax, source = _cv3max_components(numerator, weight)
    three = vr + vb - vi
    np.testing.assert_allclose(vmax, np.maximum.reduce([three, vr, vb]))
    assert point.shape == (3,)
    assert len(source) == 3
    assert all(x in {"three_term", "training_one_way", "validation_one_way"} for x in source)


def test_translation_invariance_of_cv3max_component_bound():
    groups, _ = _rows()
    rng = np.random.default_rng(44)
    base = rng.normal(size=(8, len(groups), 2))
    first = _audit(base, contrast_names=("a", "b"))
    shift = 0.73
    second = _audit(base + shift, contrast_names=("a", "b"))
    for lc, rc in zip(first.contrasts, second.contrasts):
        for left, right in zip(lc.groups, rc.groups):
            assert right.cv3max_standard_error == pytest.approx(
                left.cv3max_standard_error, abs=1e-12
            )
            assert right.one_sided_t_critical_value == pytest.approx(
                left.one_sided_t_critical_value, abs=1e-14
            )
            assert right.lower_bound == pytest.approx(
                left.lower_bound + shift, abs=1e-12
            )


def test_v4_uses_iut_and_min_cluster_t_df():
    groups, _ = _rows()
    result = _audit(np.full((8, len(groups), 2), 0.5))
    assert result.compound_intersection_union_test is True
    assert result.additional_component_multiplicity_correction_applied is False
    assert result.component_lower_bounds_are_simultaneous is False
    assert result.cv3_delete_one_center_is_full_estimate is True
    assert result.cv3max_uses_max_of_three_term_and_two_one_way_variances is True
    for contrast in result.contrasts:
        for cell in contrast.groups:
            assert cell.t_degrees_of_freedom == 7
            assert cell.one_sided_t_critical_value == pytest.approx(
                1.894578605061305, abs=2e-12
            )
    json.dumps(result.as_dict(), allow_nan=False)


def test_refit_order_with_ids_is_invariant():
    groups, blocks = _rows()
    rng = np.random.default_rng(51)
    gain = rng.normal(loc=0.4, scale=0.2, size=(8, len(groups), 2))
    ids = tuple(f"r{i}" for i in range(8))
    settings = dict(
        groups=groups,
        blocks=blocks,
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("a", "b"),
    )
    first = certify_training_process_positive_cv3max_iut_v4(
        gain, refit_ids=ids, **settings
    )
    second = certify_training_process_positive_cv3max_iut_v4(
        gain[::-1], refit_ids=ids[::-1], **settings
    )
    assert first.as_dict() == second.as_dict()


def test_too_few_refits_fail_closed():
    groups, blocks = _rows()
    result = certify_training_process_positive_cv3max_iut_v4(
        np.full((4, len(groups)), 0.5),
        groups,
        blocks=blocks,
        refit_ids=("a", "b", "c", "d"),
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
        minimum_refits=8,
    )
    assert result.all_cells_estimable is False
    assert result.contrasts[0].category == "unavailable"


def test_information_wrapper_keeps_non_skippable_ceiling():
    groups, blocks = _rows()
    n = len(groups)
    pooled = np.zeros((8, n))
    coarse = pooled + 0.5
    fine = coarse + 0.4
    result = certify_training_process_positive_information_cv3max_iut_v4(
        (
            RefitInformationLevelScores("pooled", (), pooled),
            RefitInformationLevelScores("coarse", ("species",), coarse),
            RefitInformationLevelScores("fine", ("species", "context"), fine),
        ),
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i}" for i in range(8)),
        training_process_id="p",
        training_process_manifest_sha256=PROCESS_SHA,
    )
    assert result.process_mean_certified_transfer_ceiling == "fine"
    assert result.fixed_set_intersection_used is False
    assert result.historical_fixed_set_results_reclassified is False
