"""Climate/temporal ecological association known-truth controls, no GPS outcomes."""
import json,math,unittest
from scripts.movebank_utah_era5_climate_20261019 import (
   CONTRACT,centered_slope,paired_environment,timezone_name
)
class Tests(unittest.TestCase):
    def test_source_registration(self):
        f=json.loads(CONTRACT.read_text())
        self.assertEqual(f["version"],"utah-original-source-shared-cellmonth-era5-ecology-v0")
        self.assertIn("post-original-diel-outcome",f["stage"])
    def test_timezone_fixed(self):
        self.assertEqual(timezone_name(-110.5),"Etc/GMT+7")
    def test_slope_known_truth(self):
        xy=[(float(i),3+2*float(i)) for i in range(10)]
        self.assertAlmostEqual(centered_slope(xy,.25),2.)
    def test_insufficient_daylight_or_monthly_variation(self):
        self.assertIsNone(centered_slope([(1.,float(i)) for i in range(12)],.25))
        self.assertIsNone(centered_slope([(float(i),2.*float(i)) for i in range(3)],.25))
    def test_source_missing_ERA5_not_imputed(self):
        cell=(40,-111,2019,6)
        src={"A":{cell:(.1,.2,.1)},"B":{cell:(.0,.1,.1)}}
        x=paired_environment("A","B",src,{})
        self.assertEqual(x["source_original_shared_cell_months"],1)
        self.assertEqual(x["weather_supported_common_cell_months"],0)
        self.assertEqual(x["source_months_missing_climate"],1)
        self.assertIsNone(x["mean_q_difference_on_weather_qualified_source_months"])
    def test_two_species_share_exact_same_regional_climate(self):
        cell=(40,-111,2020,5)
        src={"A":{cell:(.2,.3,.1)},"B":{cell:(.1,.1,0.)}}
        env={cell:{"temperature_mean":15.,"temperature_max":23.,"precip_minus_et0":-24.}}
        x=paired_environment("A","B",src,env)
        self.assertAlmostEqual(x["mean_q_difference_on_weather_qualified_source_months"],.1)
        self.assertEqual(x["shared_geographic_blocks_with_weather"],1)
        self.assertIsNone(x["within_geogrid_temp_slope_95_block_bootstrap"])
if __name__=="__main__":unittest.main()
