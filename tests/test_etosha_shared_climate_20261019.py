import unittest
from datetime import date,timedelta
from scripts.etosha_shared_climate_20261019 import join_region_climate
class Tests(unittest.TestCase):
    def test_constant_climate_zero_contrast(self):
        start=date(2020,1,1)
        vals={start+timedelta(days=i):(10.0,5.0,2.0) for i in range(200)}
        r=join_region_climate({"animal":[[(start+timedelta(days=40),start+timedelta(days=80))]]},vals)
        self.assertEqual(r["status"],"matched_date_coarse_era5_descriptive")
        self.assertAlmostEqual(r["mean_delta_era5_air_temperature_C"],0)
        self.assertAlmostEqual(r["mean_delta_precip_minus_ET0_past30days_mm"],0)
    def test_missing_weather_never_zero_filled(self):
        x=date(2020,1,1)
        self.assertEqual(join_region_climate({"a":[[(x,x+timedelta(days=100))]]},{x:(1,2,3)})["status"],"source_weather_hold")
    def test_equal_animal_not_pair_weight(self):
        d=date(2020,1,1)
        w={d+timedelta(days=i):(float(i),5,2) for i in range(200)}
        a=d+timedelta(days=35);b=d+timedelta(days=65);c=d+timedelta(days=95)
        r=join_region_climate({"a":[[(a,b),(a,c)]],"b":[[(a,b)]]},w)
        self.assertAlmostEqual(r["mean_delta_era5_air_temperature_C"],37.5)
if __name__=="__main__":unittest.main()
