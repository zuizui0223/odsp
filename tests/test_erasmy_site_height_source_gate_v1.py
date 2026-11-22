import unittest

from scripts.erasmy_site_height_source_gate_v1 import (
    embedded_list,inspect_original_header,list_file_metadata,
    select_version,download_href,
)


class ErasmySourceAdmissionTests(unittest.TestCase):
    def test_published_version_metadata_selects_last(self):
        src={"_embedded":{"stash:versions":[
            {"id":18,"versionNumber":1},{"id":19,"versionNumber":2}
        ]}}
        self.assertEqual(select_version(src),19)

    def test_dryad_published_hal_versions_without_id(self):
        src={"_embedded":{"stash:versions":[
          {"versionNumber":1,"_links":{"self":{"href":"/api/v2/versions/26724"}}},
          {"versionNumber":2,"_links":{"self":{"href":"/api/v2/versions/26725"}}}
        ]}}
        self.assertEqual(select_version(src),26725)

    def test_only_expected_original_files_allowed(self):
        files=[
            {"path":"dir/species_act.csv","size":33690,
             "_links":{"stash:download":{"href":"/api/v2/files/400/download"}}},
            {"path":"guildact.csv","size":68970},
            {"path":"README_verticalstrat_models.txt","size":817},
        ]
        result=list_file_metadata({"_embedded":{"stash:files":files}})
        self.assertEqual(set(result),set((
            "species_act.csv","guildact.csv","README_verticalstrat_models.txt")))
        self.assertEqual(download_href(result["species_act.csv"]),
                         "https://datadryad.org/api/v2/files/400/download")

    def test_no_spoofed_file_or_download_host(self):
        with self.assertRaisesRegex(ValueError,"roster"):
            list_file_metadata({"files":[{"path":"fake.csv"}]})
        with self.assertRaisesRegex(ValueError,"outside"):
            download_href({"_links":{"download":{"href":"https://evil.example/file.csv"}}})

    def test_synthetic_numeric_response_is_never_parsed(self):
        src=b"plot,date,height,bat,activity\np1,2021-06-01,ground,bat1,SEALED\n"
        result=inspect_original_header(src)
        self.assertEqual(result["source_design_rows"],1)
        self.assertFalse(result["bat_activity_numeric_values_inspected"])
        self.assertEqual(result["header_fields"],
                         ["plot","date","height","bat","activity"])

    def test_ragged_file_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"ragged"):
            inspect_original_header(
                b"plot,date,height,bat,activity\np1,2021-06-01,ground\n")

    def test_version_without_unique_id_stops(self):
        with self.assertRaisesRegex(ValueError,"no usable"):
            select_version({"versions":[{"versionNumber":1}]})

if __name__=="__main__":
    unittest.main()
