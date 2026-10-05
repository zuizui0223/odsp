from __future__ import annotations

import pytest

from odsp.training_process_positive_cv3two_iut_calibration import (
    run_training_process_positive_cv3two_iut_v5_null_calibration,
    run_training_process_positive_cv3two_iut_v5_power_calibration,
)


def test_v5_panels_reject_out_of_scope_settings():
    with pytest.raises(ValueError, match="simulations_per_scenario"):
        run_training_process_positive_cv3two_iut_v5_null_calibration(
            simulations_per_scenario=99
        )
    with pytest.raises(ValueError, match="contrast_count"):
        run_training_process_positive_cv3two_iut_v5_null_calibration(
            contrast_count=4
        )
    with pytest.raises(ValueError, match="standardized shifts"):
        run_training_process_positive_cv3two_iut_v5_power_calibration(
            moderate_standardized_shift=5,
            strong_standardized_shift=3,
        )
