"""Known truths for source-locked original GPS × ERA5 wind/shortwave ecology."""
from datetime import datetime, timedelta, date
from unittest.mock import patch
import json
import math
import unittest
from scripts.solar_azimuth_era5_wind_v0 import (
    year_request_parameters, wind_flow_to, wrap_cos_degrees,
    validate_and_parse_weather, ERA5OriginalSourceHold
)
from scripts.run_solar_wind_irradiance_shared_gps_v0 import (
    original_setup,join_one_pair,get_weather,query_frame
)


class SolarWindSharedOriginalKnownTruth(unittest.TestCase):

    def test_two_original_studies_and_four_supported_pairs_exact(self):
        contract,sources,pairs,previous=original_setup()
        self.assertEqual([r["uuid"] for r in contract["exact_studies"]],[
            "8318572a-a9d8-4d9e-b685-7db8a73bdf86",
            "cd4e676d-424f-4b40-8e4e-3681a0f26530"
        ])
        self.assertEqual(sum(len(x) for x in pairs.values()),4)
        self.assertEqual(len(pairs[contract["exact_studies"][0]["uuid"]]),3)
        self.assertEqual(len(pairs[contract["exact_studies"][1]["uuid"]]),1)

    def test_wind_from_direction_and_compass_quadrants(self):
        self.assertEqual(wind_flow_to(0),180)
        self.assertEqual(wind_flow_to(270),90)
        self.assertAlmostEqual(wrap_cos_degrees(180,180),1)
        self.assertAlmostEqual(wrap_cos_degrees(0,180),-1)
        self.assertAlmostEqual(wrap_cos_degrees(90,180),0,places=12)
        with self.assertRaises(ERA5OriginalSourceHold):
            wind_flow_to(float("nan"))

    def test_provider_year_request_no_best_match_or_local_clock(self):
        p=year_request_parameters(-4,-76,2019)
        self.assertEqual(p["models"],"era5")
        self.assertEqual(p["timezone"],"UTC")
        self.assertEqual(p["latitude"],-3.5)
        self.assertEqual(p["longitude"],-75.5)
        self.assertEqual(p["wind_speed_unit"],"ms")
        self.assertIn("shortwave_radiation",p["hourly"])

    def test_source_hourly_units_and_checksums(self):
        year=2021
        date0=datetime(year,1,1)
        hours=[(date0+timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M")
               for i in range(8760)]
        data={"utc_offset_seconds":0,
              "hourly_units":{"wind_speed_100m":"m/s",
                              "wind_direction_100m":"°",
                              "shortwave_radiation":"W/m²",
                              "temperature_2m":"°C"},
              "hourly":{"time":hours,
                        "wind_speed_100m":[3.0]*len(hours),
                        "wind_direction_100m":[0.0]*len(hours),
                        "shortwave_radiation":[200.0]*len(hours),
                        "temperature_2m":[25.0]*len(hours)}}
        weather,receipt=validate_and_parse_weather(json.dumps(data).encode(),year)
        self.assertEqual(len(weather),8760)
        self.assertEqual(receipt["source_hourly_records"],8760)
        self.assertEqual(weather[date0],(3.0,0.0,200.0,25.0))
        data["hourly_units"]["wind_speed_100m"]="km/h"
        with self.assertRaises(ERA5OriginalSourceHold):
            validate_and_parse_weather(json.dumps(data).encode(),year)

    def test_wind_and_solar_bearings_same_GPS_synthetic_cells_exact(self):
        cell=(15,20,2020,6,2)
        one=datetime(2020,6,1,10)
        climate={ (15,20,2020):{} }
        orig={"A":[],"B":[]}
        for i in range(3):
            for j in range(5):
                stamp=one+timedelta(days=j,hours=i)
                climate[(15,20,2020)][stamp]=(4.0,0.0,200.0,25.0)
                orig["A"].append({"animal":"a"+str(i),"cell":cell,"utc_hour":stamp,
                                  "bearing":180.0,"sun_azimuth":180.0})
                orig["B"].append({"animal":"b"+str(i),"cell":cell,"utc_hour":stamp,
                                  "bearing":0.0,"sun_azimuth":180.0})
        earlier={"taxa":["A","B"],"shared_source_grid_month_solar_hour_cells":1,
                 "a_minus_b_solar_relative_bearing_cosine":2.0}
        target=join_one_pair(earlier,{"A":{cell:True},"B":{cell:True}},orig,climate)
        self.assertEqual(target["status"],"SOURCE_OBSERVED_ERA5_LINKED_DESCRIPTION")
        self.assertEqual(target["registered_original_shared_cells"],1)
        self.assertTrue(target["full_original_GPS_solar_difference_replayed"])
        diff=target["environmental_differences"]["A_minus_B"]
        self.assertAlmostEqual(diff["solar_cos"],2)
        self.assertAlmostEqual(diff["windflow_cos"],2)
        self.assertAlmostEqual(diff["wind_sun_cos"],0)
        self.assertAlmostEqual(diff["shortwave_W_m2"],0)
        self.assertFalse(any(key in target for key in ("original_cell_latitude", "original_cell_longitude", "original_GPS_ids", "source_midpoint_utc")))
        self.assertNotIn(str(cell),str(target))

    def test_incomplete_climate_wont_invent_sunlight_result(self):
        cell=(15,20,2020,6,2)
        stamp=datetime(2020,6,1,10)
        orig={"A":[{"animal":"a","cell":cell,"utc_hour":stamp,
                    "bearing":180.0,"sun_azimuth":180.0}],
              "B":[{"animal":"b","cell":cell,"utc_hour":stamp,
                    "bearing":0.0,"sun_azimuth":180.0}]}
        earlier={"taxa":["A","B"],"shared_source_grid_month_solar_hour_cells":1,
                 "a_minus_b_solar_relative_bearing_cosine":2.0}
        result=join_one_pair(earlier,{"A":{cell:True},"B":{cell:True}},orig,{})
        self.assertEqual(result["status"],"WEATHER_SOURCE_HOLD")
        self.assertIsNone(result["environmental_differences"])


if __name__=="__main__":
    unittest.main()
