from odsp.forecast_assessment_v4 import (
    ForecastAssessmentV4Certification,
    ForecastAssessmentV4Result,
    assess_state_forecast_v4,
)


def test_forecast_assessment_v4_public_module_surface_exists():
    assert ForecastAssessmentV4Certification is not None
    assert ForecastAssessmentV4Result is not None
    assert callable(assess_state_forecast_v4)
