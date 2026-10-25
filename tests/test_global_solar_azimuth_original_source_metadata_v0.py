"""All-source GPS/GNSS original metadata preflight: fixed selection and fail-closed."""
import unittest
from unittest.mock import patch
from scripts.global_solar_azimuth_259_original_source_metadata_v0 import (
    row_for_package,summary
)


class OriginalSourceMetadataTests(unittest.TestCase):
    def setUp(self):
        self.p={
            "package_uuid":"a","repository_study_ids":["S1"],
            "scientific_names":["Species a"],"sensor_names":["GPS"],"dois":["doi:example"],
            "licenses":["CC0"],"reported_animal_count":6,"reported_location_count":20000
        }

    @patch("scripts.global_solar_azimuth_259_original_source_metadata_v0.original_files")
    def test_archive_metadata_without_any_event_access(self,get):
        get.return_value=[
            {"bitstream_uuid":"b1","name":"data.csv","bytes":100,
             "checksum":{"value":"checksum","checkSumAlgorithm":"MD5"}},
            {"bitstream_uuid":"b2","name":"reference-data.csv","bytes":50,
             "checksum":{"value":"checksum2","checkSumAlgorithm":"MD5"}}
        ]
        r=row_for_package(self.p)
        self.assertEqual(r["source_status"],"original_metadata_listed")
        self.assertEqual(r["repository_study_ids"],["S1"])
        self.assertEqual(r["animal_event_rows_screened"],0)
        self.assertEqual(len(r["candidate_original_track_containers"]),1)
        self.assertFalse(r["candidate_original_track_containers"][0]["original_bytes_or_schema_verified"])

    @patch("scripts.global_solar_azimuth_259_original_source_metadata_v0.original_files")
    def test_source_missing_preserved_as_hold(self,get):
        get.side_effect=RuntimeError("403")
        r=row_for_package(self.p)
        self.assertEqual(r["source_status"],"SOURCE_HOLD")
        self.assertTrue(r["catalog_meta_only_priority"])
        self.assertEqual(r["candidate_original_track_containers"],[])

    def test_census_rejects_not_all_259(self):
        with self.assertRaisesRegex(ValueError,"259"):
            summary([row_for_package_no_http(self.p)])


def row_for_package_no_http(p):
    with patch("scripts.global_solar_azimuth_259_original_source_metadata_v0.original_files",return_value=[]):
        return row_for_package(p)


if __name__=="__main__":
    unittest.main()
