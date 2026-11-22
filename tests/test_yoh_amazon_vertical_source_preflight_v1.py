import unittest
from scripts.yoh_amazon_vertical_source_preflight_v1 import source_only_scan

HEADER=b"Season,Location,Transect,Distance,Habitat,Species,No.\n"

def fixture(duplicate=False,missing=False):
    rows=[]
    for loc in ("Dimona","CaboFrio"):
      for tr in ("T1","T2"):
        for distance in ("-100","100","200"):
          for habitat in ("U","C"):
            for sp in ("AA","BB"):
              # Deliberately nonnumerical response: if read as numeric, should fail.
              rows.append([("Dry" if not missing else ""),loc,tr,distance,habitat,sp,"SEALED_OUTCOME"])
    if duplicate: rows.append(rows[0])
    body="\n".join(",".join(row) for row in rows)+"\n"
    return HEADER+body.encode()

class SourceGateTests(unittest.TestCase):
    def test_positive_synthetic_source_does_not_parse_response(self):
        v=source_only_scan(fixture())
        self.assertEqual(v["status"],"source_structure_pass")
        self.assertFalse(v["bat_pass_values_accessed"])
        self.assertEqual(v["site_season_distance_keys_with_both_strata"],12)
        self.assertEqual(v["distinct_species_or_sonotype_codes"],2)
    def test_duplicate_source_key_stops(self):
        v=source_only_scan(fixture(duplicate=True))
        self.assertEqual(v["duplicate_six_field_keys"],1)
        self.assertEqual(v["status"],"source_structure_stop")
    def test_missing_core_key_stops(self):
        v=source_only_scan(fixture(missing=True))
        self.assertEqual(v["status"],"source_structure_stop")
        self.assertEqual(v["missing_non_response_key_counts"]["season"],len(fixture().decode().splitlines())-1)
    def test_missing_response_header_stops(self):
        source=fixture().replace(b"No.",b"unknown_response")
        with self.assertRaisesRegex(RuntimeError,"required"):
            source_only_scan(source)

if __name__=="__main__":
    unittest.main()
