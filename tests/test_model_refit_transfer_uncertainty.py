import json

import numpy as np
import pytest

from odsp.model_refit_transfer_uncertainty import (
    _nested_group_samples,
    audit_model_refit_transfer_uncertainty,
)


def _inputs():
    groups = tuple(g for g in ('a', 'b') for _ in range(40))
    blocks = tuple(f'b{i:02d}' for _ in range(2) for i in range(10) for _ in range(4))
    gain = np.tile(0.3 + np.linspace(-0.02, 0.02, 80), (8, 1))
    return gain, groups, blocks


def _audit(gain=None, **kwargs):
    matrix, groups, blocks = _inputs()
    return audit_model_refit_transfer_uncertainty(
        matrix if gain is None else gain, groups, blocks=blocks, nested_draws=500, **kwargs
    )


def test_identical_refits_reduce_to_reference_and_serialize():
    result = _audit()
    assert result.refit_aware_category == result.reference_fit_category == 'robust_generalizing'
    assert result.identical_refits
    for row, reference in zip(result.groups, result.reference_audit.groups):
        assert row.nested_max_t_lower_bound == pytest.approx(reference.max_t_lower_bound, abs=1e-12)
        assert row.nested_max_t_upper_bound == pytest.approx(reference.max_t_upper_bound, abs=1e-12)
    json.dumps(result.as_dict(), allow_nan=False)


def test_shared_refit_selection_is_preserved_in_sampling_kernel():
    # Within-refit blocks are constant; output must follow the shared selection,
    # not resample refits independently per group or average across refits.
    selected = np.array([0, 1, 1, 0, 1])
    weights = np.array([1., 2.])
    gains_a = np.array([[1., 2.], [-1., -2.]])
    gains_b = 3 * gains_a
    a = _nested_group_samples(gains_a, weights, selected, seed=10)
    b = _nested_group_samples(gains_b, weights, selected, seed=20)
    np.testing.assert_allclose(a, np.where(selected == 0, 1., -1.))
    np.testing.assert_allclose(b, 3*a)


def test_refit_spread_is_not_divided_by_sqrt_number_of_refits():
    matrix, groups, blocks = _inputs()
    matrix[:4] = 0.3
    matrix[4:] = -0.3
    result = _audit(matrix)
    assert result.refit_sign_stability == 'refit_sensitive'
    assert result.refit_aware_category == 'uncertain'
    assert all(row.nested_standard_error > 0.29 for row in result.groups)
    assert not result.refit_aware_admissible


def test_common_model_variation_is_not_independently_redrawn_per_group():
    matrix, _, _ = _inputs()
    matrix[:] = np.linspace(-.3, .3, 8)[:, None]
    result = _audit(matrix)
    a, b = result.groups
    assert a.nested_standard_error == b.nested_standard_error
    assert a.nested_max_t_lower_bound == b.nested_max_t_lower_bound


def test_refit_ids_preserve_reference_and_order():
    matrix, groups, blocks = _inputs()
    matrix += np.arange(8)[:, None]*.002
    ids = tuple(f'r{i}' for i in range(8))
    a = _audit(matrix, refit_ids=ids, reference_refit_id='r2')
    b = _audit(matrix[::-1], refit_ids=ids[::-1], reference_refit_id='r2')
    assert a.as_dict() == b.as_dict()


def test_too_few_refits_cannot_be_rescued_by_reference():
    matrix, groups, blocks = _inputs()
    result = audit_model_refit_transfer_uncertainty(matrix[:3], groups, blocks=blocks, nested_draws=500)
    assert result.reference_fit_category == 'robust_generalizing'
    assert result.refit_aware_category == 'unavailable'
    assert result.selected_refit_draw_counts == ()
    assert all(row.nested_max_t_lower_bound is None for row in result.groups)


def test_one_group_without_enough_blocks_stops_global_claim():
    matrix, groups, blocks = _inputs()
    block_ids = tuple('same' if g == 'b' else b for g, b in zip(groups, blocks))
    result = audit_model_refit_transfer_uncertainty(matrix, groups, blocks=block_ids, nested_draws=500)
    assert result.refit_aware_category == 'unavailable'
    assert result.unavailable_group_count == 1


def test_zero_variance_nonpositive_and_mixed():
    matrix, _, _ = _inputs()
    matrix[:] = 0.
    zero = _audit(matrix)
    assert zero.refit_aware_category == 'robust_non_generalizing'
    assert zero.nested_max_t_critical_value == 0.
    matrix[:, :40] = .25
    matrix[:, 40:] = -.25
    assert _audit(matrix).refit_aware_category == 'mixed'


@pytest.mark.parametrize('bad', [np.ones(80), np.empty((0, 80)), np.full((8,80), np.nan), np.full((8,80), np.inf)])
def test_invalid_gain_matrix_rejected(bad):
    with pytest.raises(ValueError):
        _audit(bad)


@pytest.mark.parametrize('kw', [
    {'refit_ids': ['x']*8}, {'reference_refit_id': 'absent'},
    {'refit_ids': [None]*8}, {'sample_weight': np.ones(79)},
    {'sample_weight': np.zeros(80)}, {'sample_weight': np.full(80, -1)},
    {'familywise_confidence_level': 1.}, {'minimum_refits': True},
    {'minimum_blocks_per_group': 1}, {'gain_tolerance': -1.}, {'seed': -1},
])
def test_invalid_settings_rejected(kw):
    with pytest.raises(ValueError):
        _audit(**kw)


def test_zero_weight_block_rejected_but_zero_rows_allowed():
    weight = np.ones(80)
    weight[:4] = 0
    with pytest.raises(ValueError, match='block'):
        _audit(sample_weight=weight)
    weight[1:4] = 1
    assert _audit(sample_weight=weight).refit_aware_admissible


def test_global_weight_rescaling_and_row_permutation():
    matrix, groups, blocks = _inputs()
    p = np.random.default_rng(100).permutation(80)
    a = _audit(sample_weight=np.linspace(.5, 1.5, 80))
    b = audit_model_refit_transfer_uncertainty(
        matrix[:,p], np.asarray(groups)[p], blocks=np.asarray(blocks)[p],
        sample_weight=100*np.linspace(.5,1.5,80)[p], nested_draws=500,
    )
    for left, right in zip(a.groups, b.groups):
        assert left.nested_max_t_lower_bound == pytest.approx(right.nested_max_t_lower_bound, abs=1e-12)
