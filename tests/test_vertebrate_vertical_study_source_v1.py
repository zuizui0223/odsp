"""Known-truth source-only diagnostic tests; no original biodiversity values opened."""
import csv
import hashlib
import io
import unittest
from unittest.mock import patch
from scripts import vertebrate_vertical_study_source_v1 as s


def make_fixture(studies=5,metric="richness",bad=False):
    columns=list(s.STRUCT_COLUMNS)+list(s.SEALED_RESPONSE_COLUMNS)
    out=io.StringIO(newline="")
    w=csv.DictWriter(out,fieldnames=columns)
    w.writeheader()
    for taxon in ("Bats","Birds","Small mammals"):
        for n in range(studies):
            for h,z in ((0,"ground"),(.5,"mid"),(1,"canopy")):
                row={c:"NA" for c in columns}
                row.update({
                    "link":f"{taxon}_Study{n}_site1",
                    "study_id":f"{taxon}_Study{n}",
                    "study_id.x":f"{taxon}_Study{n}",
                    "taxa":taxon,"biodiversity_metric":metric,
                    "strata_category":z,
                    "mean_strata_height_p":str(h),
                    "min_strata_height":str(h),
                    "max_strata_height":str(h),
                    "country":"Brazil","continent":"Americas",
                    "temporal_effort_at_each_height":"100",
                    "spatial_effort_unit":"station-days",
                    "season":"dry",
                    "elevation":"200",
                    "canopy_height":"25",
                })
                # Sealed original biological outcome is not numerical,
                # demonstrating source audit does NOT parse it.
                row["corrected_biodiversity_metric_value"]="DO_NOT_READ"
                if bad and n==0 and z=="mid":
                    row["mean_strata_height_p"]="NA"
                w.writerow(row)
    return out.getvalue().encode()


class StudyGateTests(unittest.TestCase):
    def test_original_git_blob_sha1(self):
        raw=b"example\n"
        self.assertEqual(s.git_blob_hash(raw),
            hashlib.sha1(b"blob 8\0example\n").hexdigest())

    def test_fifteen_studies_and_sealed_response_admitted(self):
        raw=make_fixture()
        with patch.object(s,"SOURCE_GIT_BLOB",s.git_blob_hash(raw)):
            receipt=s.source_structure(raw)
        self.assertEqual(receipt["status"],
                         "source_structure_admitted_numerical_biodiversity_sealed")
        self.assertEqual(receipt["source_unique_studies"],15)
        self.assertEqual(receipt["site_metric_units_ge3_heights"],15)
        self.assertFalse(receipt["original_biodiversity_numeric_values_inspected"])

    def test_missing_geometry_enters_hold_not_biological_null(self):
        raw=make_fixture(bad=True)
        with patch.object(s,"SOURCE_GIT_BLOB",s.git_blob_hash(raw)):
            receipt=s.source_structure(raw)
        self.assertEqual(receipt["status"],"source_architecture_gate_hold")
        self.assertEqual(receipt["invalid_height_geometry_rows"],1)

    def test_insufficient_independent_studies_hold(self):
        raw=make_fixture(studies=3)
        with patch.object(s,"SOURCE_GIT_BLOB",s.git_blob_hash(raw)):
            receipt=s.source_structure(raw)
        self.assertEqual(receipt["status"],"source_architecture_gate_hold")
        self.assertEqual(receipt["all_cohort_qualified_distinct_studies"],0)

    def test_source_hash_mismatch_fail_closed(self):
        raw=make_fixture()
        with self.assertRaisesRegex(RuntimeError,"blob"):
            s.source_structure(raw)

if __name__=="__main__":
    unittest.main()
