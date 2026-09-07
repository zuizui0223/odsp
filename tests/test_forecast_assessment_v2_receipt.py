import json
from pathlib import Path

import pytest

pytest.importorskip('sklearn')

from odsp.forecast_assessment_v2_benchmark import run_forecast_assessment_v2_benchmark


ROOT=Path(__file__).resolve().parents[1]


def _min_bound(audit, field):
    return min(row[field] for row in audit['groups'] if row[field] is not None)


def _max_bound(audit, field):
    return max(row[field] for row in audit['groups'] if row[field] is not None)


def test_forecast_assessment_v2_receipt_replays():
    receipt=json.loads((ROOT/'FORECAST_ASSESSMENT_V2_VALIDATION_RECEIPT.json').read_text(encoding='utf-8'))
    result=run_forecast_assessment_v2_benchmark(seed=20260907)
    canonical=receipt['canonical_results']
    assert result['passed'] is canonical['passed'] is True
    assert len(result['checks'])==canonical['obligation_count']==14
    assert all(row['passed'] for row in result['checks'])

    strong=result['strong'];expected=canonical['strong'];ext=strong['extended_certification']
    assert ext['base_validation_status']==expected['base_validation_status']
    assert ext['certification_status']==expected['certification_status']
    assert ext['operational_status']==expected['operational_status']
    sim=strong['simultaneous_group_audit'];refit=strong['model_refit_audit'];block=strong['block_definition_audit']
    assert sim['max_t_transfer_category']==expected['simultaneous_category']
    assert sim['max_t_critical_value']==pytest.approx(expected['simultaneous_max_t_critical_value'],abs=1e-15)
    assert _min_bound(sim,'max_t_lower_bound')==pytest.approx(expected['simultaneous_minimum_lower_bound'],abs=1e-15)
    assert refit['refit_aware_category']==expected['model_refit_category']
    assert refit['reference_fit_category']==expected['model_refit_reference_category']
    assert refit['nested_max_t_critical_value']==pytest.approx(expected['model_refit_max_t_critical_value'],abs=1e-15)
    assert _min_bound(refit,'nested_max_t_lower_bound')==pytest.approx(expected['model_refit_minimum_lower_bound'],abs=1e-15)
    assert block['sensitivity_category']==expected['block_definition_category']
    assert block['group_status_flip_count']==expected['block_definition_group_status_flip_count']

    trap=result['multiplicity_trap'];expected=canonical['multiplicity_trap'];ext=trap['extended_certification'];sim=trap['simultaneous_group_audit']
    assert ext['base_validation_status']==expected['base_validation_status']
    assert ext['certification_status']==expected['certification_status']
    assert ext['operational_status']==expected['operational_status']
    assert sim['max_t_transfer_category']==expected['simultaneous_category']
    assert sim['max_t_critical_value']==pytest.approx(expected['simultaneous_max_t_critical_value'],abs=1e-15)
    assert _min_bound(sim,'max_t_lower_bound')==pytest.approx(expected['simultaneous_minimum_lower_bound'],abs=1e-15)
    assert ext['extended_blocking_reasons']==expected['blocking_reasons']

    fragile=result['refit_fragile'];expected=canonical['refit_fragile'];ext=fragile['extended_certification'];refit=fragile['model_refit_audit']
    assert ext['base_validation_status']==expected['base_validation_status']
    assert ext['certification_status']==expected['certification_status']
    assert ext['operational_status']==expected['operational_status']
    assert refit['reference_fit_category']==expected['reference_fit_category']
    assert refit['refit_aware_category']==expected['model_refit_category']
    assert refit['nested_max_t_critical_value']==pytest.approx(expected['model_refit_max_t_critical_value'],abs=1e-15)
    assert _min_bound(refit,'nested_max_t_lower_bound')==pytest.approx(expected['model_refit_minimum_lower_bound'],abs=1e-15)
    assert _max_bound(refit,'nested_max_t_upper_bound')==pytest.approx(expected['model_refit_maximum_upper_bound'],abs=1e-15)

    pseudo=result['block_definition_sensitive'];expected=canonical['block_definition_sensitive'];ext=pseudo['extended_certification'];block=pseudo['block_definition_audit']
    assert ext['base_validation_status']==expected['base_validation_status']
    assert ext['warning_reasons']==expected['warning_reasons']
    assert block['sensitivity_category']==expected['block_definition_category']
    assert block['group_status_flip_count']==expected['group_status_flip_count']
    by_name={row['name']:row for row in block['definitions']}
    assert by_name['primary']['minimum_group_lower_bound']==pytest.approx(expected['primary_minimum_group_lower_bound'],abs=1e-15)
    assert by_name['eight_clusters']['minimum_group_lower_bound']==pytest.approx(expected['eight_cluster_minimum_group_lower_bound'],abs=1e-15)

    few=result['too_few_refits'];expected=canonical['too_few_refits'];ext=few['extended_certification']
    assert ext['certification_status']==expected['certification_status']
    assert ext['operational_status']==expected['operational_status']
    assert few['model_refit_audit']['refit_aware_category']==expected['model_refit_category']

    optional=result['optional_layers_omitted']['extended_certification']
    assert optional['certification_status']==canonical['optional_layers_omitted']['certification_status']

    strict=result['strict_extrapolation'];expected=canonical['strict_extrapolation'];ext=strict['extended_certification']
    assert ext['certification_status']==expected['certification_status']
    assert ext['operational_status']==expected['operational_status']
    assert ext['warning_reasons']==expected['warning_reasons']
    deployment=strict['base_assessment']['dossier']['deployment']
    assert deployment['status']==expected['deployment_status']
    assert deployment['strict_extrapolation_fraction']==pytest.approx(expected['strict_extrapolation_fraction'],abs=1e-15)

    assert result['refit_reference_mismatch_rejected'] is canonical['refit_reference_mismatch_rejected'] is True
    assert receipt['claim_boundary']['aggregate_confidence_score_emitted'] is False
    assert all(value is False for value in receipt['frozen_v4_preservation'].values())
