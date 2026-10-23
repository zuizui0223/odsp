"""Source-independent known truth on original 4-taxon daily climate route."""
import json,unittest
from datetime import date
from scripts.movebank_utah_four_daily_climate_20261023 import (
    CONTRACT,collect_animal_observed_grids
)
from scripts.movebank_wyoming_daily_climate_20261023 import (
    climate_at_gps_day,adjusted_daily_effects
)
class Tests(unittest.TestCase):
    def test_original_four_taxa_and_single_source(self):
        obj=json.loads(CONTRACT.read_text())
        self.assertEqual(obj["version"],"utah-all-four-daily-original-gps-era5-daylight-v1")
        self.assertEqual(len(obj["source_reference_results"]),4)
        self.assertEqual(len({x["taxon"] for x in obj["source_reference_results"]}),4)
    def test_source_only_original_calendar_geometry(self):
        d=date(2019,6,1)
        obs={"first":[("a",2019,[(d,14,-.1,(40,-111),(2019,6))])],
             "second":[("b",2019,[(d,14,-.2,(40,-111),(2019,6))])]}
        scope=collect_animal_observed_grids(obs)
        self.assertEqual(len(scope),1)
        self.assertEqual(scope[(40,-111)],{d})
    def test_past_only_30day_ERA5_reused_verbatim(self):
        d=date(2019,5,3)
        self.assertIsNone(climate_at_gps_day({},d))
    def test_original_no_ERA5_cannot_create_slope(self):
        d=date(2019,1,1)
        years=[("a",2019,[(d,10,-.1,(40,-111),(2019,1))])]
        out=adjusted_daily_effects(years,{})
        self.assertEqual(out["weather_complete_original_animal_days"],0)
        self.assertEqual(out["source_dates_without_30day_complete_ERA5"],1)
        self.assertIsNone(out["daylight_given_tmax_and_water"]["mean"])
if __name__=="__main__":unittest.main()
