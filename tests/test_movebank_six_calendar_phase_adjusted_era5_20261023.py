"""Known-truth partial OLS and unchanged source guard tests ONLY.

No original GPS individual row, source ERA5 historical value, or signed
biological output is inspected during this test stage.
"""
from datetime import date, timedelta
import json
import math
from pathlib import Path
import statistics
import unittest

from scripts.movebank_six_calendar_phase_adjusted_era5_20261023 import (
    CONTRACT, ORIGINAL, LABELS, PREDICTORS, RESPONSES,
    seasonal_distance_from_june_solstice, calendar_adjusted_ols,
    calendar_phase_year, nested_calendar_phase_effects,
)
from scripts.movebank_six_source_within_animal_era5_date_slopes_20261019 import (
    centered_slope
)


def known_truth():
    k=[20+2*i for i in range(20)]
    x=[.24*ki+(-3 if i%2==0 else 3) for i,ki in enumerate(k)]
    return k,x


class TestSixMovebankSolsticeDistanceFalsifier(unittest.TestCase):
    def test_frozen_post_outcome_contract_and_six_original_sources(self):
        cfg=json.loads(CONTRACT.read_text())
        prior=json.loads(ORIGINAL.read_text())
        self.assertEqual(tuple(cfg["cohorts"]),LABELS)
        self.assertEqual(tuple(prior["cohorts"]),LABELS)
        self.assertEqual(sum(prior["original_group_n_animals"].values()),197)
        self.assertEqual(cfg["calendar_control"]["minimum_temperature_residual_sd_C"],.5)
        self.assertEqual(cfg["calendar_control"]["minimum_source_solar_phase_sd_days"],7.)
        self.assertIn("POST-OUTCOME",cfg["prior_outcomes"])
        self.assertTrue(cfg["reporting"]["no_p_values"])
        self.assertTrue(cfg["source_lock"]["never_refresh_model_time_or_regions"])
        self.assertEqual(len(RESPONSES),3)
        self.assertEqual(PREDICTORS,("temp_C","water_per_100mm"))

    def test_phase_is_original_calendar_distance_not_outcome_or_gps_location(self):
        yr=2020
        rising=date(yr,5,20)
        falling=date(yr,7,22)
        self.assertEqual(seasonal_distance_from_june_solstice(rising,falling),31.)
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_PAIR_NOT_JUNE"):
            seasonal_distance_from_june_solstice(date(yr,7,1),date(yr,8,1))
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_NORTHERN_PAIR_STRADDLES"):
            seasonal_distance_from_june_solstice(date(yr,5,20),date(yr+1,7,22))

    def test_calendar_only_gps_and_x_common_season_trend_vanishes_after_phase(self):
        k,x=known_truth()
        y=[.4*ki for ki in k]  # no x-causal relation, only calendar
        raw=centered_slope([(a,0,b) for a,b in zip(x,y)],"temp_C")
        self.assertIsNotNone(raw)
        self.assertGreater(abs(raw),.1)
        adjusted=calendar_adjusted_ols(k,x,y,"temp_C")
        self.assertEqual(adjusted["status"],"ELIGIBLE_PHASE_CONTROL")
        self.assertAlmostEqual(adjusted["beta"],0,places=10)
        self.assertGreater(adjusted["climate_phase_R2"],.2)

    def test_valid_temperature_signal_survives_and_components_add_exactly(self):
        k,x=known_truth()
        day=[.2*ki-.8*xx for ki,xx in zip(k,x)]
        night=[.9*ki+1.1*xx for ki,xx in zip(k,x)]
        rel=[n-d for n,d in zip(night,day)]
        rd=calendar_adjusted_ols(k,x,day,"temp_C")
        rn=calendar_adjusted_ols(k,x,night,"temp_C")
        rr=calendar_adjusted_ols(k,x,rel,"temp_C")
        self.assertEqual(rr["status"],"ELIGIBLE_PHASE_CONTROL")
        self.assertAlmostEqual(rd["beta"],-.8,places=10)
        self.assertAlmostEqual(rn["beta"],1.1,places=10)
        self.assertAlmostEqual(rr["beta"],1.9,places=10)
        self.assertAlmostEqual(rr["beta"],rn["beta"]-rd["beta"],places=12)

    def test_collinear_low_spread_and_low_n_report_undefined_no_rescue(self):
        k,x=known_truth()
        y=[float(i) for i in range(len(k))]
        perfect=[.9*ki+2 for ki in k]
        collinear=calendar_adjusted_ols(k,perfect,y,"temp_C")
        self.assertEqual(collinear["status"],"CLIMATE_RESIDUAL_NEAR_COLLINEAR_WITH_SOLAR_PHASE")
        self.assertIsNone(collinear["beta"])
        unchanging=[20]*len(k)
        self.assertEqual(calendar_adjusted_ols(unchanging,x,y,"temp_C")["status"],"INSUFFICIENT_PHASE_VARIATION")
        self.assertEqual(calendar_adjusted_ols(k[:8],x[:8],y[:8],"temp_C")["status"],"INSUFFICIENT_CALENDAR_PAIRS")
        self.assertEqual(calendar_adjusted_ols(k,[ki*.1+(.04 if j%2 else -.04) for j,ki in enumerate(k)],y,"water_per_100mm")["status"],"CLIMATE_RESIDUAL_NEAR_COLLINEAR_WITH_SOLAR_PHASE")
        with self.assertRaisesRegex(ValueError,"HOLD_UNREGISTERED"):
            calendar_adjusted_ols(k,x,y,"not_registered")

    def test_year_requires_actual_archive_weather_and_identical_response_parts(self):
        rising=date(2020,4,1)
        falling=date(2020,9,1)
        pairs=[(rising+timedelta(days=i),falling+timedelta(days=i),.1,.03,.13) for i in range(10)]
        # Source climate missing must never trigger extra dates/future model.
        res=calendar_phase_year(pairs,{})
        self.assertEqual(res["status"],"HOLD_MISSING_ORIGINAL_CLIMATE_DAY")
        assert res.get("temp_C") is None
        broken=[(pairs[0][0],pairs[0][1],.1,.03,.2),*pairs[1:]]
        from scripts.movebank_regional_climate_link_20261019 import weather_rolling_30
        # Exact dates are required for source weather, no inferred fields.
        w={}
        for d in (rising,falling):
            for j in range(-29,20):
                w[d+timedelta(days=j)]=(10.+j,.1,.05)
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_NIGHT_MINUS_DAY_PAIR_IDENTITY"):
            calendar_phase_year(broken,w)

    def test_source_output_zero_support_kept_not_turned_into_inferential_CI(self):
        result=nested_calendar_phase_effects([[]],{})
        self.assertEqual(result["temp_C"]["original_animal_count"],1)
        self.assertIsNone(result["temp_C"]["new_phase_adjusted_slopes"]["relative"]["mean"])
        self.assertEqual(result["temp_C"]["new_phase_adjusted_slopes"]["relative"]["undefined_animal_slope"],1)
        self.assertTrue(all(k in result for k in PREDICTORS))


if __name__=="__main__":
    unittest.main()
