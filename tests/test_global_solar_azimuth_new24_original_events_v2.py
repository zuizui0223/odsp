"""Verify exact new 24 source pre-result MD5 source manifest and six-shard routing."""
import json
import unittest
from scripts.movebank_native_ecology_20261019 import HERE
from scripts.global_solar_azimuth_new24_original_events_v2 import (
    CONTRACT,SOURCE_MANIFEST,fixed_new_sources
)


class FixedNewTwentyFourOriginal(unittest.TestCase):
    def test_manifest_consistent_no_previous_source_replacement(self):
        m=json.loads(SOURCE_MANIFEST.read_text())
        c=json.loads(CONTRACT.read_text())
        files=fixed_new_sources()
        self.assertEqual(len(files),24)
        self.assertEqual([x["package_uuid"] for x in c["source_groups"]],
                         [x["package_uuid"] for x in files])
        self.assertEqual(sum(x["status"]=="ORIGINAL_FILE_METADATA_ADMISSIBLE" for x in files),24)
        self.assertEqual(m["original_GPS_event_rows_opened"],0)
        self.assertEqual(len({x["package_uuid"] for x in files}),24)
        self.assertEqual(sum(x["sample_stratum"]=="single_taxon_hash_sample" for x in files),14)
        self.assertEqual(sum(x["sample_stratum"]=="all_remaining_multitaxon_census" for x in files),10)

    def test_six_shards_exactly_four_each(self):
        files=fixed_new_sources()
        encountered=set()
        for shard in range(6):
            this=[x["package_uuid"] for i,x in enumerate(files) if i%6==shard]
            self.assertEqual(len(this),4)
            self.assertFalse(set(this)&encountered)
            encountered.update(this)
        self.assertEqual(len(encountered),24)

    def test_provider_study_metadata_and_checksum_attested_before_effects(self):
        for x in fixed_new_sources():
            self.assertTrue(x["original_species_labels"])
            self.assertTrue(x["original_dois"])
            self.assertTrue(x["source_study_ids"] or x["package_uuid"])
            self.assertIn(x["original_file"]["checksum"]["checkSumAlgorithm"].upper(),
                          ("MD5","SHA256","SHA-256"))
            self.assertTrue(x["original_file"]["checksum"]["value"])


if __name__ == "__main__":
    unittest.main()
