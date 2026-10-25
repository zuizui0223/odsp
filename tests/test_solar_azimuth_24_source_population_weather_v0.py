"""Original GPS multi-source environmental ecology: pre-weather and known truths."""
import math
import unittest
from collections import defaultdict
from datetime import date,datetime,timedelta
from unittest.mock import patch
from scripts.run_solar_azimuth_24_source_population_weather_v0 import (
    check_24_original_source_contract,original_directional_grid_years,
    source_siteyear_environment_response,within_animal_weather_slope,
    latitude_band,summary_from_animal_values,_original_source_replay
)


class SourceWideWeatherEcology(unittest.TestCase):

    def test_all_twentyfour_original_study_roster_preexisting_not_effect_selected(self):
        c,files,previous=check_24_original_source_contract()
        self.assertEqual(len(files),24)
        self.assertEqual(len(previous),24)
        self.assertEqual([x["package_uuid"] for x in files],list(previous))
        self.assertTrue(all(x["status"]=="ORIGINAL_FILE_METADATA_ADMISSIBLE"
                            for x in files))
        self.assertEqual(c["GPS"]["max_gridyear_weather_API_queries_per_original_source"],8)

    def test_animal_ranking_geometry_blind_and_privacy(self):
        day=datetime(2021,6,1,9)
        tracks={}
        for i in range(5):
            hrs={}
            for d in range(11):
                t=day+timedelta(days=d)
                for h in range(4):
                    ts=t+timedelta(hours=h)
                    hrs[ts]=(ts,40+.001*i,0+.03*h)
            tracks["ANIMAL_SECRETS_"+str(i)]=hrs
        selected,counts=original_directional_grid_years(tracks)
        self.assertEqual(counts["selected_top_two_gridyears"],1)
        self.assertEqual(len(selected),1)
        key,rec=selected[0]
        self.assertEqual(key,(40,0,2021))
        self.assertEqual(len(rec["animal_ids"]),5)
        self.assertGreaterEqual(len(rec["steps"]),30)
        self.assertEqual(latitude_band(40)["absolute_latitude_band_degrees"],[30,45])

    def test_month_4h_block_weather_slope_exact_per_100W(self):
        rows=[]
        for month in (1,2):
            for day in (1,2,3):
                for hour,rad in zip((9,10,11,12),(100,400,700,100)):
                    rows.append({"utc_hour":datetime(2021,month,day,hour),
                                 "solar_day":date(2021,month,day),
                                 "solar_hour":10.0,
                                 "variables":(.001*rad,.0,.0,3.0,rad,15)})
        slope=within_animal_weather_slope(rows,"shortwave_Wm2")
        self.assertAlmostEqual(slope,.1,places=12)
        self.assertIsNone(within_animal_weather_slope(rows,"windspeed_ms"))
        self.assertIsNone(within_animal_weather_slope(rows,"temperature_C"))
        self.assertIsNone(within_animal_weather_slope(rows,"wind_sun_cos"))

    def test_source_weather_join_full_and_all_original_animal_weights(self):
        year=2021
        date0=datetime(year,6,1,8)
        original=[]
        weather={}
        for i in range(5):
            for d in range(5):
                for h in range(2):
                    t=date0+timedelta(days=d,hours=h)
                    original.append(("PRIVATE_ID_"+str(i),t,t.date(),10.0,90.0,90.0))
                    weather[t]=(3.0,0.0,400.0,20.0)
        result=source_siteyear_environment_response((40,0,2021),original,weather)
        self.assertEqual(result["weather_environmental_effect_status"],
                         "SOURCE_GROUP_OBSERVED_ENVIRONMENT_DESCRIPTION")
        self.assertEqual(result["observed_weather_qualified_original_tagged_animals"],5)
        self.assertEqual(result["original_GPS_hourly_weather_join_fraction"],1)
        self.assertAlmostEqual(result["environmental_group_means"]["sunward_cos"]["mean"],1)
        self.assertAlmostEqual(result["environmental_group_means"]["windflow_cos"]["mean"],0)
        self.assertAlmostEqual(result["environmental_group_means"]["wind_sun_cos"]["mean"],0)
        self.assertNotIn("PRIVATE_ID",str(result))
        self.assertNotIn(str((40,0,2021)),str(result))

    def test_missing_weather_is_hold_not_biological_zero(self):
        data=[("A",datetime(2021,6,1,9),date(2021,6,1),10,0,0)]*50
        res=source_siteyear_environment_response((40,0,2021),data,{})
        self.assertEqual(res["weather_environmental_effect_status"],"SOURCE_WEATHER_HOLD")
        self.assertIsNone(res["environmental_group_means"])

    def test_independent_animal_bootstrap_requires_at_least_five(self):
        s=summary_from_animal_values([.1,-.1,.2,.0])
        self.assertIsNone(s["mean"])
        self.assertEqual(s["status"],"INSUFFICIENT_ANIMAL_OR_ENVIRONMENT_VARIATION")
        t=summary_from_animal_values([.1]*5)
        self.assertAlmostEqual(t["mean"],.1)
        self.assertAlmostEqual(t["source_animal_bootstrap95"][0],.1)

    @patch("scripts.run_solar_azimuth_24_source_population_weather_v0.analyze_taxon")
    def test_prior_original_directional_results_must_replay_before_weather(self,mock):
        prior={
            "source_taxa":[{"taxon":"Species A","result_status":"descriptive_source_estimated",
              "qualified_individuals":5,
              "analysis":{"daylight_directional_qualified_steps":120,
                          "results":{"raw_toward_sun_mean_cos":{"mean":.12},
                                     "clock_adjusted_excess_cos":{"mean":.007},
                                     "compass_independence_excess_cos":{"mean":.02}}}
            }]
        }
        mock.return_value={"status":"descriptive_source_estimated",
                           "supported_individuals":5,
                           "daylight_directional_qualified_steps":120,
                           "results":{"raw_toward_sun_mean_cos":{"mean":.12},
                                      "clock_adjusted_excess_cos":{"mean":.007},
                                      "compass_independence_excess_cos":{"mean":.02}}}
        track={"Species A":{"animal":{"hour":("t",0,0)}}}
        counts={"Species A":{"original_taxon_rows":1}}
        self.assertEqual(_original_source_replay(track,counts,prior)
                         ["original_GPS_first_source_analyzable_taxa_replayed"],1)
        mock.return_value["results"]["raw_toward_sun_mean_cos"]["mean"]=-.01
        with self.assertRaisesRegex(ValueError,"did not reproduce"):
            _original_source_replay(track,counts,prior)


if __name__=="__main__":
    unittest.main()
