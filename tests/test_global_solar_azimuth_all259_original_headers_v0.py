"""All 259 original Movebank candidate source header screens are source-only."""
import unittest
from unittest.mock import patch
from scripts.global_solar_azimuth_all259_original_headers_v0 import (
    parse_header_preview,screen_one,supported_original_files,REQUIRED
)


class OriginalFirstHeaderTests(unittest.TestCase):
    def test_canonical_headers_and_no_event_values_used(self):
        raw=b'timestamp,location-lat,location-long,individual-local-identifier,individual-taxon-canonical-name\n2020-01-01,41,17,PRIVATE_ID,species\n'
        x=parse_header_preview(raw)
        self.assertTrue(x["valid_required_columns"])
        self.assertTrue(x["native_taxon_column_present"])
        self.assertNotIn("PRIVATE_ID",str(x))
        self.assertNotIn("2020-01",str(x))

    def test_header_gates_missing_timestamp_and_duplicate_normalization(self):
        bad=b'obs-time,location-lat,location-long,individual-local-identifier\n'
        self.assertFalse(parse_header_preview(bad)["valid_required_columns"])
        dup=b'timestamp,location-lat,location-long,individual-local-identifier, TIMEStamp \n'
        self.assertFalse(parse_header_preview(dup)["valid_required_columns"])

    def test_binary_and_unclosed_header_not_parsed_as_original_gps(self):
        self.assertFalse(parse_header_preview(b"PK\x03\x04data")["valid_required_columns"])
        self.assertFalse(parse_header_preview(b'timestamp,location-lat')["valid_required_columns"])

    @patch("scripts.global_solar_azimuth_all259_original_headers_v0.source_first_header")
    @patch("scripts.global_solar_azimuth_all259_original_headers_v0.original_files")
    def test_one_real_filename_only_then_first_header(self,files,fetch):
        p={"package_uuid":"x","scientific_names":["Species one"],"sensor_names":["GPS"]}
        files.return_value=[{"name":"source.csv","bytes":1000,"bitstream_uuid":"b1",
                             "checksum":{"value":"good","checkSumAlgorithm":"MD5"}}]
        fetch.return_value=(b'timestamp,location-lat,location-long,individual-local-identifier\nDATA\n',206)
        r=screen_one(p)
        self.assertEqual(r["status"],"CANONICAL_ORIGINAL_CSV_HEADER")
        self.assertEqual(r["source_GPS_records_qualified"],0)
        self.assertFalse("DATA" in str(r))
        fetch.assert_called_once_with("b1")

    @patch("scripts.global_solar_azimuth_all259_original_headers_v0.source_first_header")
    @patch("scripts.global_solar_azimuth_all259_original_headers_v0.original_files")
    def test_ambiguous_zip_and_schema_hold_never_fallback_to_alternative(self,files,fetch):
        p={"package_uuid":"x","scientific_names":["Species one"],"sensor_names":["GPS"]}
        files.return_value=[
            {"name":"original_data_1.csv","bytes":1000,"bitstream_uuid":"b1"},
            {"name":"original_data_2.csv","bytes":1000,"bitstream_uuid":"b2"}
        ]
        r=screen_one(p)
        self.assertEqual(r["status"],"AMBIGUOUS_OR_MISSING_SINGLE_ORIGINAL_FILE")
        fetch.assert_not_called()
        files.return_value=[
            {"name":"archived.csv.zip","bytes":1000,"bitstream_uuid":"b1",
             "checksum":{"value":"verified_provider_metadata","checkSumAlgorithm":"MD5"}}
        ]
        r=screen_one(p)
        self.assertEqual(r["status"],"COMPRESSED_ORIGINAL_REQUIRES_VERIFIED_DOWNLOAD")
        fetch.assert_not_called()


if __name__=="__main__":
    unittest.main()
