"""New Southern source roster and timestamp-only fixes: deterministic pre-outcome tests."""
import unittest
from datetime import datetime,timedelta
from scripts.run_global_solar_azimuth_southern_v0 import (
    fixed_source_roster, closest_to_hour
)
from scripts.solar_azimuth_macro_v0 import directional_step


class SouthernGPSAzimuthKnownTruth(unittest.TestCase):
    def test_exact_four_registered_original_sources(self):
        sources=fixed_source_roster()
        self.assertEqual(len(sources),4)
        self.assertEqual(len(set(x["package_uuid"] for x in sources)),4)
        self.assertEqual(set(x["taxon"] for x in sources),
                         {"Loxodonta africana","Tapirus terrestris","Canis mesomelas"})
        self.assertEqual(sum(x["zipped"] for x in sources),1)

    def test_source_hour_selection_must_ignore_displacement(self):
        start=datetime(2026,1,22,9)
        tracks=[(start+timedelta(minutes=42),-20,25.1),
                (start+timedelta(minutes=12),-20,25.0),
                (start+timedelta(minutes=58),-20,25.2),
                (start+timedelta(hours=1,minutes=4),-20,25.3)]
        observed=closest_to_hour(tracks)
        self.assertEqual(len(observed),2)
        self.assertEqual(observed[0][0],start+timedelta(minutes=12))
        self.assertEqual(observed[1][0],start+timedelta(hours=1,minutes=4))

    def test_southern_sun_geometry_and_daylight_filter(self):
        t=datetime(2026,1,21,8)
        day=directional_step((t,-20,25), (t+timedelta(hours=1),-20,25.06))
        self.assertIsNotNone(day)
        self.assertGreater(day.sun_elevation,10)
        night=directional_step((t+timedelta(hours=12),-20,25),
                               (t+timedelta(hours=13),-20,25.06))
        self.assertIsNone(night)


if __name__ == "__main__":
    unittest.main()
