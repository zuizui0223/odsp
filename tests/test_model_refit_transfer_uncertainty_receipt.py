"""Recompute the frozen experiment; compare values, not just stored pass flags."""
import json
from pathlib import Path

import pytest

from odsp.model_refit_transfer_uncertainty_benchmark import run_model_refit_transfer_uncertainty_benchmark


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def replay():
    receipt = json.loads((ROOT / 'MODEL_REFIT_TRANSFER_UNCERTAINTY_VALIDATION_RECEIPT.json').read_text(encoding='utf-8'))
    cfg = receipt['benchmark_config']
    result = run_model_refit_transfer_uncertainty_benchmark(seed=cfg['seed'], nested_draws=cfg['nested_draws'])
    return receipt, result


def test_receipt_replays_all_obligations_and_matches_frozen_config(replay):
    receipt, result = replay
    contract = json.loads((ROOT / receipt['contract']).read_text(encoding='utf-8'))
    for key, value in receipt['benchmark_config'].items():
        assert value == contract['known_truth_benchmark'][key]
    obligations = contract['known_truth_benchmark']['frozen_obligations']
    assert {row['name'] for row in result['checks']} == set(obligations)
    assert len(result['checks']) == receipt['canonical_results']['obligation_count'] == 15
    assert result['passed'] is True
    assert all(row['passed'] is True for row in result['checks'])
    assert receipt['first_green_validation']['conclusion'] == 'success'
    assert len(receipt['first_green_validation']['result_json_sha256']) == 64


def test_receipt_replays_every_case_category_and_numerical_bound(replay):
    receipt, result = replay
    for name, expected in receipt['canonical_results']['cases'].items():
        actual = result[name]
        lowers = [g['nested_max_t_lower_bound'] for g in actual['groups'] if g['nested_max_t_lower_bound'] is not None]
        uppers = [g['nested_max_t_upper_bound'] for g in actual['groups'] if g['nested_max_t_upper_bound'] is not None]
        observed = {
            'reference_fit_category': actual['reference_fit_category'],
            'refit_sign_stability': actual['refit_sign_stability'],
            'refit_aware_category': actual['refit_aware_category'],
            'refit_aware_admissible': actual['refit_aware_admissible'],
            'minimum_nested_max_t_lower_bound': min(lowers) if lowers else None,
            'maximum_nested_max_t_upper_bound': max(uppers) if uppers else None,
            'nested_max_t_critical_value': actual['nested_max_t_critical_value'],
            'unavailable_group_count': actual['unavailable_group_count'],
        }
        assert set(observed) == set(expected)
        for key, value in expected.items():
            if isinstance(value, float):
                assert observed[key] == pytest.approx(value, rel=0, abs=1e-12), (name, key)
            else:
                assert observed[key] == value, (name, key)
        assert actual['same_selected_refit_shared_across_groups'] is True
        assert actual['reference_fit_can_override_refit_aware_failure'] is False
        assert actual['aggregate_confidence_score_emitted'] is False
    for key, value in receipt['canonical_results']['invariance_errors'].items():
        assert result[key] == pytest.approx(value, rel=0, abs=1e-12)
        assert result[key] <= 1e-12


def test_receipt_does_not_promote_fixture_success_to_population_or_empirical_proof(replay):
    receipt, _ = replay
    assert receipt['interpretation']['validation_type'] == 'deterministic_gain_matrix_fixtures'
    assert receipt['interpretation']['upstream_models_trained_by_frozen_benchmark'] is False
    assert receipt['interpretation']['exact_population_coverage_validated'] is False
    assert receipt['interpretation']['nested_spread_divided_by_sqrt_refit_count'] is False
    assert all(value is False for value in receipt['frozen_v4_preservation'].values())
