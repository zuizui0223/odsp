import unittest,math
from datetime import datetime,timedelta
from scripts.movebank_kruger_thermal_solar_20261019 import (
    within_year_slope,choose_hour_with_temperature,estimate
)
from scripts.movebank_elephant_hourly_20261019 import choose_one_per_utc_hour
class Tests(unittest.TestCase):
    def test_exact_time_only_selection_matches_old_route(self):
        t=datetime(2008,7,1,12)
        records=[(t+timedelta(minutes=m),-24,31,15+m) for m in (45,9,32,1,29)]
        actual=choose_hour_with_temperature(records)
        reference=choose_one_per_utc_hour([x[:3] for x in records])
        self.assertEqual([x[:3] for x in actual],reference)
    def test_slope_known_positive(self):
        vals=[(float(i),0.1+2.0*float(i)) for i in range(15)]
        result=within_year_slope(vals)
        self.assertAlmostEqual(result[0],2.0,places=10)
    def test_slope_known_negative(self):
        vals=[(float(i),1.0-0.5*float(i)) for i in range(15)]
        self.assertAlmostEqual(within_year_slope(vals)[0],-0.5)
    def test_no_slope_when_no_heat_gradient_variation(self):
        vals=[(2.0,i*0.01) for i in range(15)]
        self.assertIsNone(within_year_slope(vals))
    def test_few_pairs_do_not_create_effect(self):
        self.assertIsNone(within_year_slope([(float(i),float(i)) for i in range(9)]))
    def test_few_independent_animals_do_not_create_group_effect(self):
        self.assertEqual(estimate({"a":[{"slope":0.2}]} )["status"],"temperature_slope_insufficient_independent_animals")
if __name__=="__main__":unittest.main()
