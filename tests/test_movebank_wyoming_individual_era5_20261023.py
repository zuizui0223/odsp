"""Synthetic regression, climate calendar and source gating tests only."""
import json,math,unittest
from datetime import date,timedelta
from scripts.movebank_wyoming_individual_era5_20261023 import (
    CONTRACT,monthly_observations,source_animal_slopes,exposure_frame
)
from scripts.movebank_utah_calendar_condition_20261022 import partial_slope
class Tests(unittest.TestCase):
    def test_source_registered_before_new_environment(self):
        s=json.loads(CONTRACT.read_text())
        self.assertEqual(s["version"],"wyoming-independent-individual-environment-daylight-v0")
        self.assertEqual(len(s["prior_effects_to_replay"]),2)
        self.assertEqual({v["taxon"] for v in s["prior_effects_to_replay"]},{"Odocoileus hemionus","Ovis canadensis"})
    def test_month_contribution_requires_four_observed_days(self):
        d=date(2019,5,1)
        days=[(d+timedelta(days=i),13+i*.01,-.1,(42,-111),(2019,5)) for i in range(3)]
        weather={(42,-111,2019,5):{"temperature_mean":20.,"precip_minus_et0":-30.}}
        out,missing=monthly_observations(days,weather)
        self.assertEqual(len(out),0);self.assertEqual(missing,0)
        days.append((d+timedelta(days=3),13.05,-.2,(42,-111),(2019,5)))
        out,missing=monthly_observations(days,weather)
        self.assertEqual(len(out),1)
        self.assertAlmostEqual(out[0][0],20.)
        self.assertAlmostEqual(out[0][1],-.3)
    def test_no_ERA5_never_filled(self):
        d=date(2019,5,1)
        days=[(d+timedelta(days=i),13,-.1,(42,-111),(2019,5)) for i in range(5)]
        out,missing=monthly_observations(days,{})
        self.assertEqual(len(out),0);self.assertEqual(missing,5)
    def test_source_exposure_frame_only_recorded_months(self):
        d=date(2019,4,1)
        admitted=[("animal",2019,[(d,13,-.1,(42,-111),(2019,4))])]
        frame=exposure_frame(admitted)
        self.assertEqual(frame,{(42,-111):{(2019,4)}})
    def test_sunlight_partial_from_known_truth_climate(self):
        rows=[]
        for i in range(9):
            sunlight=10+0.3*i
            temperature=15+0.3*i+(i%3)*1.6
            water=(i%4-2)*.4+i*.03
            q=2*sunlight+3*temperature
            rows.append((temperature,water,sunlight,q,2019,i+1))
        self.assertAlmostEqual(partial_slope(rows,2,[0,1],minimum_n=8,residual_sd=.2),2.,places=8)
    def test_missing_environment_no_effect(self):
        d=date(2019,1,1)
        days=[(d+timedelta(days=i),10+.005*i,-.1,(42,-111),(2019,1)) for i in range(20)]
        result=source_animal_slopes([("animal",2019,days)],{})
        self.assertEqual(result["source_days_without_era5_month"],20)
        self.assertEqual(result["environment_adjusted_associations"]["daylight_given_temperature_and_water"]["status"],"INSUFFICIENT_IDENTIFIABLE_ANIMALS")
if __name__=="__main__":unittest.main()
