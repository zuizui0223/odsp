"""Source integrity and known-truth tests for the original frozen 21-site panel."""
from datetime import date
import math
import unittest
from scripts.analyze_fixed_21site_global_equinoctial_era5_20261019 import (
    DATES,validate,daylength,compute,desc
)

def synthetic_obj(day="2019-03-19",soil=0.30):
    return {"latitude":15.0,"longitude":0.0,"timezone":"Africa/Bamako",
            "daily_units":{"temperature_2m_mean":"°C","temperature_2m_max":"°C",
                           "soil_moisture_0_to_7cm_mean":"m³/m³"},
            "daily":{"time":[day],"temperature_2m_mean":[26.0],
                     "temperature_2m_max":[33.0],"soil_moisture_0_to_7cm_mean":[soil]}}

class FrozenClimateTest(unittest.TestCase):
    def test_original_dates_same_as_frozen_source_panel(self):
        self.assertEqual(DATES["south"][0],("2018-09-26","2019-03-19"))
        self.assertEqual(DATES["north"][2],("2020-03-19","2020-09-25"))
        self.assertLess(abs(daylength(date(2018,3,19),45)-daylength(date(2018,9,26),45)),1)
        self.assertLess(abs(daylength(date(2019,9,22),-30)-daylength(date(2020,3,22),-30)),1)

    def test_source_good_units_values_and_physical_bounds(self):
        self.assertEqual(validate(synthetic_obj(),15,0,"2019-03-19"),[26.0,33.0,.30])
        with self.assertRaisesRegex(ValueError,"HOLD_PHYSICALLY_INVALID_SOIL_MOISTURE"):
            validate(synthetic_obj(soil=-.001),15,0,"2019-03-19")
        with self.assertRaisesRegex(ValueError,"HOLD_PHYSICALLY_INVALID_SOIL_MOISTURE"):
            validate(synthetic_obj(soil=1.001),15,0,"2019-03-19")

    def test_null_bad_unit_timestamp_and_site_rejected(self):
        u=synthetic_obj();u["daily"]["soil_moisture_0_to_7cm_mean"]=[None]
        with self.assertRaisesRegex(ValueError,"HOLD_MISSING_OR_NONFINITE"):
            validate(u,15,0,"2019-03-19")
        with self.assertRaisesRegex(ValueError,"HOLD_DATE_OR_TIMEZONE"):
            validate(synthetic_obj(),15,0,"2019-03-20")
        with self.assertRaisesRegex(ValueError,"HOLD_UNEXPECTED_GRID"):
            validate(synthetic_obj(),-30,0,"2019-03-19")
        u=synthetic_obj();u["daily_units"]["soil_moisture_0_to_7cm_mean"]="mm"
        with self.assertRaisesRegex(ValueError,"HOLD_SOURCE_UNITS"):
            validate(u,15,0,"2019-03-19")

    def test_signed_differences_not_automatically_same_direction(self):
        x=desc([-5,0,4,8])
        self.assertEqual((x["negative"],x["zero"],x["positive"]),(1,1,2))
        self.assertEqual(x["mean"],1.75)

    def test_unchanged_source_63_pairs_all_missingness_retained(self):
        rows,summary=compute()
        self.assertEqual(len(rows),63)
        self.assertEqual(len({(r["cell_id"],r["cycle"]) for r in rows}),63)
        self.assertEqual(len({r["cell_id"] for r in rows}),21)
        self.assertLess(summary["max_daylength_mismatch_minutes"],1)
        self.assertEqual(summary["verified_pairs"]+len(summary["invalid_pairs"]),63)
        self.assertTrue(summary["no_area_weighting_or_animal_behavior_inference"])

    def test_bad_original_era5_soil_stays_source_hold_not_zero(self):
        rows,summary=compute()
        invalid=[r for r in rows if r["status"]!="VERIFIED_REANALYSIS_PAIR"]
        self.assertEqual(len(invalid),1)
        self.assertEqual((invalid[0]["cell_id"],invalid[0]["cycle"]),("+30_+060",2019))
        self.assertEqual(invalid[0]["status"],"HOLD_PHYSICALLY_INVALID_SOIL_MOISTURE")
        self.assertIsNone(invalid[0]["delta_soil_m3m3"])
        self.assertIsNone(invalid[0]["delta_tmean_C"])

if __name__=="__main__":
    unittest.main()
