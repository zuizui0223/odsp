"""Prior-to-source-response GPS 24-source metadata manifest integrity."""
import json
import unittest
from unittest.mock import patch
from scripts.movebank_native_ecology_20261019 import HERE
from scripts.global_solar_azimuth_24_source_only_v2 import (
    source_only_entry,CONTRACT,CATALOG
)


class New24SourceMetadataTests(unittest.TestCase):
    def test_all_24_exact_before_original_data(self):
        c=json.loads(CONTRACT.read_text())
        self.assertEqual(len(c["source_groups"]),24)
        self.assertEqual(len(set(x["package_uuid"] for x in c["source_groups"])),24)
        self.assertEqual(sum(x["source_type"]=="all_remaining_multitaxon_census" for x in c["source_groups"]),10)
        self.assertEqual(sum(x["source_type"]=="single_taxon_hash_sample" for x in c["source_groups"]),14)
        self.assertEqual(len(json.loads(CATALOG.read_text())["packages"]),437)

    @patch("scripts.global_solar_azimuth_24_source_only_v2.original_files")
    def test_checksum_file_and_size_are_fixed_from_metadata(self,fs):
        s={"package_uuid":"id", "source_type":"single_taxon_hash_sample",
           "within_group_rank":1, "expected_original_file_bytes":300}
        p={"scientific_names":["Bird"],"dois":["doi:test"],
           "repository_study_ids":["study"]}
        fs.return_value=[{"bitstream_uuid":"b1","name":"original.csv","bytes":300,
                          "checksum":{"value":"abcd","checkSumAlgorithm":"MD5"}}]
        x=source_only_entry(s,p)
        self.assertEqual(x["status"],"ORIGINAL_FILE_METADATA_ADMISSIBLE")
        self.assertEqual(x["original_file"]["bitstream_uuid"],"b1")
        self.assertEqual(x["observed_original_GPS_rows"],0)
        fs.return_value=[{"bitstream_uuid":"b1","name":"original.csv","bytes":301,
                          "checksum":{"value":"abcd","checkSumAlgorithm":"MD5"}}]
        y=source_only_entry(s,p)
        self.assertEqual(y["status"],"SOURCE_HOLD")
        self.assertIsNone(y["original_file"])


if __name__ == "__main__":
    unittest.main()
