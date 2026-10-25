"""Known-truth climate-control fixtures. No wildlife detection outcomes are read."""
import datetime as dt
import unittest
from scripts.run_serengeti_era5_environment_v0 import (
    START,END,SERIES,calendar_pairs,quantile,run,verify_source
)

def synthetic_source():
    first=dt.date.fromisoformat(START)
    end=dt.date.fromisoformat(END)
    dates=[]
    while first<=end:
        dates.append(first.isoformat())
        first+=dt.timedelta(days=1)
    return {
        "latitude":-2.5,
        "longitude":34.75,
        "elevation":1555.0,
        "timezone":"Africa/Dar_es_Salaam",
        "utc_offset_seconds":10800,
        "daily":{
            "time":dates,
            "temperature_2m_mean":[20.0]*len(dates),
            "temperature_2m_max":[27.0]*len(dates),
            "precipitation_sum":[1.0]*len(dates),
            "shortwave_radiation_sum":[18.0]*len(dates)
        }
    }

class TestERA5MatchedDaylengthEnvironment(unittest.TestCase):
    def test_pair_calendar_522_no_retune(self):
        ps=calendar_pairs()
        self.assertEqual(len(ps),522)
        self.assertEqual(ps[0],(2010,"2010-12-14","2010-12-28"))
        self.assertEqual(ps[-1],(2012,"2012-06-24","2013-06-19"))

    def test_uniform_temperature_rain_has_exact_zero_branch_contrast(self):
        receipt=run(synthetic_source())
        self.assertEqual(receipt["status"],"EXTERNAL_ERA5_REGIONAL_CLIMATE_CONTEXT_ONLY")
        self.assertEqual(receipt["source_available_day_count"],1277)
        self.assertEqual(receipt["paired_calendar_design"]["environmental_date_pairs_total"],522)
        for row in receipt["results"]["yearwise_and_all"]:
            for stats in row["delta_falling_minus_rising"].values():
                self.assertEqual(stats["mean"],0.0)
                self.assertEqual(stats["median"],0.0)
                self.assertEqual(stats["positive_fraction"],0.0)
        self.assertFalse(receipt["serengeti_original_animal_record_linked"])

    def test_nonfinite_or_missing_fails_closed(self):
        source=synthetic_source()
        source["daily"]["precipitation_sum"][200]=None
        with self.assertRaisesRegex(ValueError,"HOLD_ERA5_NULL_NONFINITE"):
            verify_source(source)

    def test_wrong_timezone_and_date_sequence_fails_closed(self):
        s=synthetic_source()
        s["utc_offset_seconds"]=0
        with self.assertRaisesRegex(ValueError,"HOLD_SOURCE_TIMEZONE"):
            verify_source(s)
        s=synthetic_source()
        s["daily"]["time"][7]=s["daily"]["time"][6]
        with self.assertRaisesRegex(ValueError,"HOLD_ERA5_NONCONSECUTIVE"):
            verify_source(s)

    def test_quantile_interpolation(self):
        self.assertEqual(quantile([2,4,6,8,10],.5),6)
        self.assertEqual(quantile([0,10],.1),1)

if __name__=="__main__":
    unittest.main()
