"""Pre-outcome systematic twelve GPS sources: source-only selection tests."""
import json
import unittest
from unittest.mock import patch
from scripts.movebank_native_ecology_20261019 import HERE
from scripts.global_solar_azimuth_new_registry_sample_v1 import (
    CONTRACT,CATALOG,choose_all_strata,one_metadata_package,rank_key
)


class NewIndependentSourceSelectionTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads(CONTRACT.read_text())
        self.packages=json.loads(CATALOG.read_text())["packages"]

    def test_all_previous_sources_excluded_and_four_strata_frozen(self):
        selected,counts=choose_all_strata(self.packages,self.spec)
        self.assertEqual(len(selected),12)
        self.assertEqual(sum(counts.values()),186)
        self.assertEqual(set(counts),{"single_large","single_small","multiple_small","multiple_large"})
        self.assertEqual(len({p["package_uuid"] for _,_,p in selected}),12)
        self.assertFalse(set(self.spec["previous_sources"]) &
                         {p["package_uuid"] for _,_,p in selected})
        for name in counts:
            self.assertEqual(sum(g==name for g,_,_ in selected),3)
        for group,rank,p in selected:
            candidates=[x for x in self.packages if x["package_uuid"]!=None
                        and x["package_uuid"] not in self.spec["previous_sources"]
                        and any(v in ("GPS","GNSS") for v in (x.get("sensor_names") or []))
                        and (x.get("reported_animal_count") or 0)>=5
                        and (x.get("reported_location_count") or 0)>=10000
                        and (x.get("scientific_names") or [])]
            local=[x for x in candidates if
                   ("multiple" if len(set(x["scientific_names"]))>1 else "single")
                   +("_large" if x["reported_animal_count"]>=30 else "_small")==group]
            expected=sorted(local,key=rank_key)[rank-1]
            self.assertEqual(expected["package_uuid"],p["package_uuid"])

    def test_completeness_failure_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            choose_all_strata(self.packages[:-1],self.spec)

    @patch("scripts.global_solar_azimuth_new_registry_sample_v1.original_files")
    def test_no_primary_source_data_substitution(self,get):
        meta=self.packages[0]
        get.return_value=[
            {"name":"a.csv","bitstream_uuid":"first","bytes":500,"checksum":{"value":"a","checkSumAlgorithm":"MD5"}},
            {"name":"b.csv.zip","bitstream_uuid":"second","bytes":600,"checksum":{"value":"b","checkSumAlgorithm":"MD5"}}
        ]
        row=one_metadata_package("single_large",1,meta)
        self.assertEqual(row["status"],"SOURCE_HOLD")
        self.assertEqual(row["candidate_source_data_containers"],2)
        self.assertIsNone(row["original_file"])
        self.assertEqual(row["animal_event_rows_opened"],0)


if __name__=="__main__":
    unittest.main()
