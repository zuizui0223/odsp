"""Synthetic fixtures only: ensure paper source-audit cannot imply a new animal result."""
import io
import json
import unittest
import zipfile
from pathlib import Path

from scripts.audit_kays_2020_seasonal_zip_schema_v0 import (
    _safe_member,
    official_schema_preflight,
    schema_only_receipt,
)

ROOT = Path(__file__).resolve().parents[1]


class TestSolarSeasonalHysteresisSourceGate(unittest.TestCase):
    def test_first_header_only_no_biological_values_ever_emitted(self):
        memory = io.BytesIO()
        with zipfile.ZipFile(memory, "w", zipfile.ZIP_DEFLATED) as zipped:
            zipped.writestr(
                "data/observation.csv",
                "StationID,EventStart,Species,Latitude,Longitude\n"
                "secret_real_source_species_value,2022-06-01 10:15:00,"
                "DoNotReportTheAnimal,XX.XXXX,YY.YYYY\n",
            )
            zipped.writestr("data/deployments.csv", "StationID,DeploymentStart,DeploymentEnd\na,first,last\n")
        receipt = schema_only_receipt(memory.getvalue())
        encoded = json.dumps(receipt)
        self.assertNotIn("DoNotReportTheAnimal", encoded)
        self.assertNotIn("secret_real_source_species_value", encoded)
        self.assertNotIn("XX.XXXX", encoded)
        self.assertFalse(receipt["verified_physical_camera_uptime"])
        self.assertFalse(receipt["verified_same_station_both_photoperiod_branches"])
        self.assertEqual(receipt["source_scientific_status"], "NO_BIOLOGICAL_OUTCOME_COMPUTED")
        self.assertEqual(len(receipt["source_zip_member_headers"]), 2)
        self.assertTrue(receipt["source_zip_member_headers"][0]["date_or_timestamp_header_candidate"])
        self.assertTrue(receipt["source_zip_member_headers"][1]["deployment_start_header_candidate"])

    def test_zip_path_traversal_rejected(self):
        self.assertFalse(_safe_member("../test.csv"))
        self.assertFalse(_safe_member("/root.csv"))
        self.assertFalse(_safe_member("a/../../root.csv"))
        with self.assertRaises(ValueError):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w") as zipped:
                zipped.writestr("../bad.csv", "Species,EventStart\nsecret,now\n")
            schema_only_receipt(stream.getvalue())

    def test_unregistered_url_holds_without_network(self):
        receipt = official_schema_preflight("https://untrusted.example.org/data.csv")
        self.assertEqual(receipt["status"], "HOLD_UNREGISTERED_DOWNLOAD_URL")

    def test_catalog_does_not_mistake_41_studies_for_41_seasonal_replications(self):
        source = json.loads((ROOT / "research/solar_seasonal_hysteresis_source_feasibility_v0.json").read_text())
        entries = source["sources"]
        self.assertEqual(len(entries), 10)
        ids = [entry["id"] for entry in entries]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(entry["gate"] for entry in entries))
        self.assertTrue(all(not entry["primary_equal_daylength_eligible_now"] for entry in entries))
        kays = next(entry for entry in entries if entry["id"] == "kays2020_seasonal")
        self.assertEqual(kays["published_study_areas_all_analyses"], 41)
        self.assertEqual(kays["published_study_areas_with_yearlong_seasonality"], 5)
        self.assertEqual(len(kays["seasonality_area_names"]), 5)
        self.assertFalse(kays["original_event_zip_member_rows_verified"])
        self.assertFalse(kays["source_independent_hourly_camera_operation_verified"])
        self.assertEqual(
            next(e for e in entries if e["id"] == "snapshot_japan_2023")["gate"],
            "NOT_RISING_DAYLENGTH_COVERAGE",
        )


if __name__ == "__main__":
    unittest.main()
