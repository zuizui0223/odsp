"""Independent synthetic tests for solar-calendar conditional ecological effects."""
import unittest,math,json
from scripts.movebank_utah_calendar_condition_20261022 import (
    CONTRACT,residuals,partial_slope,block_results
)
class Tests(unittest.TestCase):
    def test_frozen_six_taxon_pairs(self):
        c=json.loads(CONTRACT.read_text())
        self.assertEqual(c["version"],"utah-six-pair-calendar-conditioned-ecology-v0")
        self.assertEqual(len(c["all_six_frozen_previous_results"]),6)
    def test_daylight_removes_artificial_temperature_effect(self):
        # Y varies ONLY with astronomical solar daylight L; T correlated L.
        # Retain temperature deviations independent of L; Y has only sunlight effect.
        rows=[(5+2*i+(i%3-1)*1.2,0.5*i,9+i,3*(9+i),2019,i+1) for i in range(10)]
        self.assertAlmostEqual(partial_slope(rows,0,[2]),0,places=10)
    def test_predictor_survives_solar_adjustment_if_independent(self):
        # temperature deviations have independent pattern, true slope 2.
        rows=[]
        for i in range(12):
            light=10+0.3*i
            temperature=3+.5*i+(i%3-1)*1.3
            water=i*0.1+(i%4-1)*0.5
            q=2*temperature+5*light
            rows.append((temperature,water,light,q,2019,1+i))
        self.assertAlmostEqual(partial_slope(rows,0,[2]),2,places=9)
        self.assertAlmostEqual(partial_slope(rows,0,[2,1],minimum_n=8),2,places=9)
    def test_collinear_solar_adjustment_fail_closed(self):
        rows=[(5+i,2.0*i,10+0.2*i,float(i),2019,i+1) for i in range(12)]
        self.assertIsNone(partial_slope(rows,0,[2]))
        self.assertIsNone(partial_slope(rows,0,[2,1],minimum_n=8))
    def test_untestable_monthly_support_undefined_not_zero(self):
        c=(40,-111,2019,5)
        a={c:(.1,.2,.1)};b={c:(.0,.1,.1)}
        x=block_results(a,b,{})
        self.assertEqual(x["missing_weather_shared_grid_year_months"],1)
        self.assertIsNone(x["daylength_conditioned_and_joint"]["partial_temperature_daylength"]["mean_equal_geographic_block_slope"])
    def test_complete_one_month_not_inventing_solar_slope(self):
        c=(40,-111,2019,5)
        a={c:(.1,.2,.1)};b={c:(.0,.1,.1)}
        e={c:{"temperature_mean":14.,"precip_minus_et0":-40.,"temperature_max":19.}}
        x=block_results(a,b,e)
        self.assertEqual(x["weather_qualified_shared_grid_year_months"],1)
        self.assertEqual(x["same_cell_same_calendar_month_between_year_contrasts"],0)
        self.assertIsNone(x["daylength_conditioned_and_joint"]["partial_water_daylength"]["mean_equal_geographic_block_slope"])
if __name__=="__main__":unittest.main()
