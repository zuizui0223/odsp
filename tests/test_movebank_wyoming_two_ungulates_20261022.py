"""Original source-identity and biological-estimand known-truth checks."""
import csv,json,math,unittest
from datetime import datetime,timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from scripts.movebank_wyoming_two_ungulates_20261022 import (
    CONTRACT,streaming_time_selected_csv,between_taxon_geography
)
class Tests(unittest.TestCase):
    def test_fixed_source_taxa_md5(self):
        r=json.loads(CONTRACT.read_text())
        self.assertEqual(r["version"],"wyoming-two-ungulate-independent-source-diel-ecology-v0")
        self.assertEqual(set(r["source"]["published_species"]),{"Ovis canadensis","Odocoileus hemionus"})
        self.assertEqual(len(r["source"]["original_md5"]),32)
    def test_separate_same_animal_id_in_two_species(self):
        with TemporaryDirectory() as td:
            p=Path(td)/"s.csv"
            p.write_text("timestamp,location-long,location-lat,individual-local-identifier,individual-taxon-canonical-name\n"+
                "2020-04-01 12:10:00,-110,40,same,Odocoileus hemionus\n"+
                "2020-04-01 12:15:00,-110,41,same,Ovis canadensis\n"+
                "2020-04-01 12:02:00,-110,42,same,Ovis canadensis\n")
            x,n,other=streaming_time_selected_csv(p,["Odocoileus hemionus","Ovis canadensis"])
            self.assertEqual(other,0)
            self.assertEqual(len(x["Odocoileus hemionus"]["same"]),1)
            self.assertEqual(len(x["Ovis canadensis"]["same"]),1)
            self.assertEqual(next(iter(x["Ovis canadensis"]["same"].values()))[0].minute,2)
    def test_unknown_source_taxa_not_rescued(self):
        with TemporaryDirectory() as td:
            p=Path(td)/"s.csv"
            p.write_text("timestamp,location-long,location-lat,individual-local-identifier,individual-taxon-canonical-name\n"+
                "2020-04-01 12:10:00,-110,40,animal,UNKNOWN\n")
            x,n,other=streaming_time_selected_csv(p,["Odocoileus hemionus","Ovis canadensis"])
            self.assertEqual(other,1)
            self.assertEqual(sum(len(k) for k in x.values()),0)
    def test_same_source_pair_has_positive_known_synthetic(self):
        x={"Odocoileus hemionus":{
              (40,-111,2020,4):.2,(40,-111,2020,5):.4,(41,-111,2020,5):.2},
           "Ovis canadensis":{
              (40,-111,2020,4):.1,(40,-111,2020,5):.2,(41,-111,2020,5):.1}}
        out=between_taxon_geography(x)
        self.assertEqual(out["source_original_shared_coarse_cell_months"],3)
        self.assertEqual(out["shared_distinct_coarse_geographic_1degree_blocks"],2)
        self.assertAlmostEqual(out["equal_geographic_block_mean_q_difference_a_minus_b"],(.15+.1)/2)
        self.assertIsNone(out["blockbootstrap_95_interval"])
    def test_no_shared_space_is_not_biological_negative(self):
        x={"Odocoileus hemionus":{(40,-111,2020,4):.2},
           "Ovis canadensis":{(41,-111,2020,4):.1}}
        out=between_taxon_geography(x)
        self.assertEqual(out["q_difference_sign_if_estimable"],"unavailable")
if __name__=="__main__":unittest.main()
