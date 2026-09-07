import json
from pathlib import Path

import pytest

from odsp.model_refit_transfer_uncertainty_benchmark import run_model_refit_transfer_uncertainty_benchmark


@pytest.fixture(scope='module')
def result():
    return run_model_refit_transfer_uncertainty_benchmark()


def test_frozen_refit_benchmark_obligations(result):
    contract = json.loads((Path(__file__).resolve().parents[1] / 'MODEL_REFIT_TRANSFER_UNCERTAINTY_CONTRACT.json').read_text())
    expected_names = set(contract['known_truth_benchmark']['frozen_obligations'])
    assert {row['name'] for row in result['checks']} == expected_names
    assert len(result['checks']) == 15
    assert result['passed'] is True
    assert all(row['passed'] for row in result['checks'])
    json.dumps(result, allow_nan=False)


def test_fragile_reference_does_not_rescue_ensemble(result):
    audit = result['refit_fragile']
    assert audit['reference_fit_category'] == 'robust_generalizing'
    assert audit['point_transfer_category'] == 'generalizing'
    assert audit['refit_sign_stability'] == 'refit_sensitive'
    assert audit['refit_aware_category'] == 'uncertain'
    assert all(row['positive_refit_count'] == 10 for row in audit['groups'])
    assert all(row['nested_max_t_lower_bound'] < 0 < row['nested_max_t_upper_bound'] for row in audit['groups'])


def test_identical_reduction_and_invariances(result):
    for key in ('identical_refits_bound_error', 'refit_order_error', 'row_order_error',
                'positive_global_weight_scaling_error'):
        assert result[key] <= 1e-12
    assert sum(result['stable_positive']['selected_refit_draw_counts']) == 4000
