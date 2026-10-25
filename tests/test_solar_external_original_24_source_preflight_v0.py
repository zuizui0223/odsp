"""External original-source sampling freeze: public source metadata only."""
import unittest
from unittest.mock import patch
from scripts.preflight_solar_external_original_24_sources_v0 import (
    frozen_source_metadata_roster,preflight_one
)


class ExternalOriginalMetadataSourceTests(unittest.TestCase):

    def test_exact_unseen_nonhuman_24_and_public_study_ID_disjoint(self):
        roster=frozen_source_metadata_roster()
        self.assertEqual(len(roster),24)
        self.assertEqual(len({x["original_source_package_uuid"] for x in roster}),24)
        self.assertEqual(len({x["original_taxon"] for x in roster}),24)
        self.assertEqual(len({y for x in roster for y in x["original_repository_study_ids"]}),24)
        self.assertNotIn("Homo sapiens",{x["original_taxon"] for x in roster})
        self.assertEqual([x["frozen_metadata_rank"] for x in roster],list(range(1,25)))

    @patch("scripts.preflight_solar_external_original_24_sources_v0.original_files")
    def test_exact_original_file_size_checksum_and_no_event_access(self,fetch):
        source=frozen_source_metadata_roster()[0]
        fetch.return_value=[{
            "name":"provider_original.csv",
            "bitstream_uuid":"immutable-uuid",
            "bytes":source["expected_original_primary_csv_bytes"],
            "checksum":{"checkSumAlgorithm":"MD5","value":"abcdef"}
        }]
        result=preflight_one(source)
        self.assertEqual(result["original_source_status"],"ORIGINAL_FILE_METADATA_QUALIFIED")
        self.assertEqual(result["original_gps_event_rows_read"],0)
        self.assertEqual(result["original_file"]["bitstream_uuid"],"immutable-uuid")
        fetch.return_value[0]["bytes"]+=1
        result=preflight_one(source)
        self.assertEqual(result["original_source_status"],"SOURCE_METADATA_HOLD")
        self.assertIsNone(result["original_file"])


if __name__=="__main__":
    unittest.main()
