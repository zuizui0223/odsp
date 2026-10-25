"""Known-truth tests for the new *directional* (not diel speed) ecological response."""
import math
import unittest
from datetime import date, datetime, timedelta, timezone

from scripts.solar_azimuth_macro_v0 import (
    Step, analyze_taxon, bearing_degrees, circular_span_degrees,
    cosine_alignment, directional_step, distance_km, summarize_animal, sun_position
)
from scripts.run_global_solar_azimuth_macro_v0 import frame_rows, frame_summary


class SolarAzimuthMacroKnownTruth(unittest.TestCase):

    def test_solar_noon_and_equatorial_equinox(self):
        noon = sun_position(datetime(2026, 6, 21, 12, tzinfo=timezone.utc), 40, 0)
        self.assertGreater(noon.elevation, 70)
        self.assertLess(noon.elevation, 75)
        self.assertLess(abs(noon.azimuth - 180), 5)
        night = sun_position(datetime(2026, 6, 21, 0), 40, 0)
        self.assertLess(night.elevation, 0)
        equinox = sun_position(datetime(2026, 3, 20, 12), 0, 0)
        self.assertGreater(equinox.elevation, 85)

    def test_direction_bearing_and_dateline(self):
        self.assertAlmostEqual(bearing_degrees(0, 0, 0, 1), 90, places=5)
        self.assertAlmostEqual(bearing_degrees(0, 0, 1, 0), 0, places=5)
        self.assertAlmostEqual(bearing_degrees(0, 0, 0, -1), 270, places=5)
        self.assertAlmostEqual(distance_km(0, 179.99, 0, -179.99), 2.2239, places=2)
        self.assertAlmostEqual(bearing_degrees(0, 179.99, 0, -179.99), 90, places=3)
        with self.assertRaises(ValueError):
            bearing_degrees(1, 1, 1, 1)

    def test_sunrise_and_stationary_steps_excluded(self):
        dawn = datetime(2026, 6, 21, 2)
        self.assertIsNone(directional_step((dawn, 40, 0),
                                            (dawn + timedelta(hours=1), 40, .03)))
        day = datetime(2026, 6, 21, 10)
        self.assertIsNone(directional_step((day, 40, 0),
                                            (day + timedelta(hours=1), 40, 0)))
        result = directional_step((day, 40, 0),
                                  (day + timedelta(hours=1), 40, .03))
        self.assertIsNotNone(result)
        self.assertTrue(0 <= result.sun_azimuth < 360)
        self.assertGreater(result.sun_elevation, 10)
        self.assertAlmostEqual(result.bearing, 90, delta=0.02)

    def test_circular_wrap_span(self):
        self.assertAlmostEqual(circular_span_degrees([358, 2, 359]), 4)
        self.assertAlmostEqual(circular_span_degrees([90, 180, 270]), 180)

    def test_fixed_geographic_heading_is_not_solar_covariance(self):
        d = date(2026, 6, 1)
        s = [Step(heading, sun, d + timedelta(days=i), 10, 35)
             for i, (heading, sun) in enumerate(
                 ([(90, 30), (90, 60), (90, 90), (90, 120)] * 8))]
        observed, baseline = cosine_alignment(s)
        self.assertAlmostEqual(observed - baseline, 0, places=12)
        result = summarize_animal(s)
        self.assertTrue(result["supported"])
        self.assertAlmostEqual(result["compass_independence_excess_cos"], 0, places=12)
        self.assertTrue(result["clock_adjusted_identifiable"])
        self.assertAlmostEqual(result["clock_adjusted_excess_cos"], 0, places=12)

    def test_following_solar_bearing_gives_positive_covariance(self):
        d = date(2026, 6, 1)
        s = [Step(sun, sun, d + timedelta(days=i), 10, 30)
             for i, sun in enumerate(([60, 90, 120, 150] * 8))]
        result = summarize_animal(s)
        self.assertTrue(result["clock_adjusted_identifiable"])
        self.assertAlmostEqual(result["raw_toward_sun_mean_cos"], 1.0)
        self.assertGreater(result["compass_independence_excess_cos"], .1)
        self.assertGreater(result["clock_adjusted_excess_cos"], .1)

    def test_solar_azimuth_no_contrast_is_unidentifiable(self):
        d = date(2026, 6, 1)
        s = [Step((90 + i) % 360, 120, d + timedelta(days=i), 10, 30)
             for i in range(32)]
        result = summarize_animal(s)
        self.assertTrue(result["supported"])
        self.assertFalse(result["clock_adjusted_identifiable"])
        self.assertIsNone(result["clock_adjusted_excess_cos"])

    def test_animal_cluster_instead_of_gps_fix_weighting(self):
        base = datetime(2026, 6, 1, 10)
        fixes = []
        for i in range(32):
            t = base + timedelta(days=i)
            fixes.extend([(t, 40, 0), (t + timedelta(hours=1), 40, .03)])
        animals = {"a" + str(i): list(fixes) for i in range(6)}
        result = analyze_taxon(animals)
        self.assertEqual(result["source_animals"], 6)
        self.assertEqual(result["supported_individuals"], 6)
        self.assertEqual(result["status"], "descriptive_source_estimated")
        self.assertEqual(result["results"]["raw_toward_sun_mean_cos"]["n_individuals"], 6)

    def test_full_frame_metadata_classification_without_source_peeking(self):
        packages = [
            {"package_uuid": "a", "sensor_names": ["GPS", "Argos Doppler Shift"],
             "scientific_names": ["A"], "reported_location_count": 20000,
             "reported_animal_count": 7},
            {"package_uuid": "b", "sensor_names": ["Argos Doppler Shift"],
             "scientific_names": ["B"], "reported_location_count": 12000,
             "reported_animal_count": 6},
            {"package_uuid": "c", "sensor_names": ["Solar Geolocator"],
             "scientific_names": ["C"], "reported_location_count": 5000,
             "reported_animal_count": 3},
        ]
        r = frame_rows(packages)
        s = frame_summary(r)
        self.assertEqual(s["GPS_or_GNSS_packages"], 1)
        self.assertEqual(s["Argos_only_packages"], 1)
        self.assertEqual(s["broader_tracking_sensor_candidates"], 2)
        self.assertEqual(s["GPS_GNSS_metadata_priority_10000locations_5animals"], 1)
        self.assertEqual(s["original_tracks_qualified_by_this_census"], 0)


if __name__ == "__main__":
    unittest.main()
