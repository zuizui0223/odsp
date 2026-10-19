"""Known-truth and immutable-original source checks for 15/30-day climate windows."""
import copy
from datetime import date,timedelta
import math
import unittest

from scripts.analyze_fixed_21site_era5_15_30day_history_v0 import (
    WINDOWS, validated_window, make_row, compute, desc
)

def fake_source(with_rain=True):
    start=date(2020,4,1)
    days=[(start+timedelta(days=k)).isoformat() for k in range(30)]
    data={
        "time":days,
        "temperature_2m_mean":[10.0]*30,
        "temperature_2m_max":[20.0]*30,
        "soil_moisture_0_to_7cm_mean":[0.2]*30,
        "precipitation_sum":[1.0]*30
    }
    return {"daily":data}

class ERA5TemporalHistory(unittest.TestCase):
    def test_equal_trailing_15_and_30_day_values(self):
        p=fake_source()
        self.assertEqual(WINDOWS,(15,30))
        self.assertAlmostEqual(validated_window(p,15)["mean_t2m_C"],10)
        self.assertAlmostEqual(validated_window(p,15)["total_precip_mm"],15)
        self.assertAlmostEqual(validated_window(p,30)["total_precip_mm"],30)

    def test_nonlast_weather_changes_30day_without_changing_15day(self):
        p=fake_source()
        p["daily"]["temperature_2m_mean"][2]=16.0
        self.assertAlmostEqual(validated_window(p,15)["mean_t2m_C"],10.0)
        self.assertAlmostEqual(validated_window(p,30)["mean_t2m_C"],10.2)

    def test_physical_invalid_hold_not_replaced_or_clipped(self):
        p=fake_source()
        p["daily"]["soil_moisture_0_to_7cm_mean"][29]=-.001
        for w in WINDOWS:
            with self.assertRaisesRegex(ValueError,"HOLD_PHYSICALLY_INVALID_SOIL"):
                validated_window(p,w)
        p=fake_source()
        p["daily"]["soil_moisture_0_to_7cm_mean"][0]=-0.001
        self.assertAlmostEqual(validated_window(p,15)["mean_soil_m3m3"],.2)
        with self.assertRaisesRegex(ValueError,"HOLD_PHYSICALLY_INVALID_SOIL"):
            validated_window(p,30)

    def test_source_precip_missing_and_temperature_sanity(self):
        p=fake_source();p["daily"]["precipitation_sum"][29]=-1
        with self.assertRaisesRegex(ValueError,"HOLD_NEGATIVE_DAILY_PRECIP"):
            validated_window(p,30)
        p=fake_source();p["daily"]["temperature_2m_max"][29]=9.9
        with self.assertRaisesRegex(ValueError,"HOLD_TMAX_BELOW_TMEAN"):
            validated_window(p,30)
        p=fake_source();p["daily"]["temperature_2m_mean"][29]=float("nan")
        with self.assertRaisesRegex(ValueError,"HOLD_NONFINITE"):
            validated_window(p,15)

    def test_opposite_sign_classification_and_exact_precip_units(self):
        rising=fake_source();falling=fake_source()
        falling["daily"]["temperature_2m_mean"]=[13.0]*30
        falling["daily"]["temperature_2m_max"]=[23.0]*30
        falling["daily"]["soil_moisture_0_to_7cm_mean"]=[.15]*30
        falling["daily"]["precipitation_sum"]=[2.0]*30
        site={"cell_id":"S","latitude":15.0,"longitude":0,"continent":"Africa","map_label":"test"}
        old={"status":"VERIFIED_REANALYSIS_PAIR","delta_tmean_C":1.0,"delta_soil_m3m3":-.01,"opposite_tmean_soil_sign":True}
        row=make_row(site,2020,"north",30,rising,falling,old)
        self.assertEqual(row["status"],"VERIFIED_ERA5_HISTORICAL_WINDOW")
        self.assertAlmostEqual(row["delta_tmean_C"],3.0)
        self.assertAlmostEqual(row["delta_soil_m3m3"],-.05)
        self.assertEqual(row["delta_precip_window_mm"],30.0)
        self.assertEqual(row["temperature_and_soil_category"],"warmer_drier")
        self.assertTrue(row["temperature_and_soil_opposite"])
        self.assertTrue(row["precipitation_soil_opposite"])

    def test_all_prior_63_rows_reproduced_and_new_126_complete(self):
        rows,rec=compute()
        self.assertEqual(len(rows),126)
        self.assertEqual(len({(r["cell_id"],r["cycle"],r["trailing_window_days"]) for r in rows}),126)
        self.assertEqual(rec["n_original_sites"],21)
        self.assertEqual(rec["original_site_cycles"],63)
        self.assertEqual(rec["original_one_day_admitted"],62)
        self.assertEqual(rec["original_one_day_temperature_soil_opposite"],29)
        self.assertTrue(rec["limits"]["not_equal_daily_photoperiod_throughout_trailing_windows"])

    def test_new_invalid_window_flagged_and_history_source_not_modified(self):
        rows,rec=compute()
        for w in WINDOWS:
            x=rec["windows"][str(w)]
            self.assertEqual(x["source_admitted_site_cycles"]+len(x["unavailable_pairs"]),63)
            self.assertTrue(all(a["reason"].startswith("HOLD_") for a in x["unavailable_pairs"]))
        # Both 15 and 30-day original Iran 2019 are invalid, no zeros fabricated.
        iran=[r for r in rows if r["cell_id"]=="+30_+060" and r["cycle"]==2019]
        self.assertEqual(len(iran),2)
        self.assertTrue(all(r["status"].startswith("HOLD_PHYSICALLY_INVALID_SOIL") for r in iran))
        self.assertTrue(all(r["delta_tmean_C"] is None and r["delta_soil_m3m3"] is None for r in iran))

if __name__=="__main__":unittest.main()
