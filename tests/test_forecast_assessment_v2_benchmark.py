import pytest

pytest.importorskip('sklearn')

from odsp.forecast_assessment_v2_benchmark import run_forecast_assessment_v2_benchmark


def test_frozen_forecast_assessment_v2_benchmark_passes():
    result=run_forecast_assessment_v2_benchmark(seed=20260907)
    assert result['passed'] is True
    assert len(result['checks'])==14
    assert all(row['passed'] for row in result['checks'])
    assert result['strong']['extended_certification']['certification_status']=='certified'
    assert result['multiplicity_trap']['extended_certification']['certification_status']=='not_certified'
    assert result['refit_fragile']['extended_certification']['certification_status']=='not_certified'
    assert result['too_few_refits']['extended_certification']['certification_status']=='unavailable'
    assert result['refit_reference_mismatch_rejected'] is True
