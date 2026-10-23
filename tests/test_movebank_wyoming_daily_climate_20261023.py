"""Source-independent daily ERA5/animal seasonal ecological estimator controls."""
import json,math,unittest
from datetime import date,timedelta
from scripts.movebank_wyoming_daily_climate_20261023 import (
    CONTRACT,climate_at_gps_day,group_effect,adjusted_daily_effects
)
from scripts.movebank_utah_calendar_condition_20261022 import partial_slope
class Tests(unittest.TestCase):
    def test_separately_registered_daily_not_monthly(self):
        c=json.loads(CONTRACT.read_text())
        self.assertEqual(c["version"],"wyoming-daily-original-gps-era5-daylight-v1")
        self.assertIn("monthly",c["epistemic_status"].lower())
        self.assertEqual(len(c["original_effect_replay"]),2)
    def test_antecedent_30_days_not_future(self):
        d=date(2019,3,15)
        weather={d-timedelta(days=i):(15.,25.,4.,1.) for i in range(30)}
        weather[d+timedelta(days=1)]=(99.,99.,500.,0.)
        result=climate_at_gps_day(weather,d)
        self.assertEqual(result[:2],(15.,25.))
        self.assertAlmostEqual(result[2],.9)
    def test_missing_one_of_30_days_is_hold(self):
        d=date(2019,3,15)
        weather={d-timedelta(days=i):(15.,25.,4.,1.) for i in range(29)}
        self.assertIsNone(climate_at_gps_day(weather,d))
    def test_known_individual_year_slope(self):
        rows=[]
        for i in range(40):
            light=10+.09*i
            Tmax=25+.1*i+(i%4-1)*3.1
            water=-.4+(.15*(i%6-3))
            q=2*light+1*Tmax+2*water
            rows.append((Tmax,water,light,q,15.))
        self.assertAlmostEqual(partial_slope(rows,2,[0,1],minimum_n=15,residual_sd=.1),2,places=7)
    def test_one_individual_one_inference_unit(self):
        x=group_effect([("a",2019,.1),("a",2020,.5),("b",2019,-.1)])
        self.assertEqual(x["admitted_animals"],2)
        self.assertIsNone(x["mean"])
        self.assertEqual(x["status"],"INSUFFICIENT_IDENTIFIABLE_SOURCE_ANIMALS")
    def test_missing_weather_does_not_impute_behavior(self):
        d=date(2019,3,1)
        days=[(d+timedelta(days=i),10+.05*i,.1,(42,-110),(2019,3)) for i in range(20)]
        out=adjusted_daily_effects([("a",2019,days)],{})
        self.assertEqual(out["source_dates_without_30day_complete_ERA5"],20)
        self.assertEqual(out["water_given_daylight_and_tmax"]["status"],"INSUFFICIENT_IDENTIFIABLE_SOURCE_ANIMALS")
if __name__=="__main__":unittest.main()
