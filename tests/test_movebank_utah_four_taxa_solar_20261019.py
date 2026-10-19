"""Known-truth data architecture tests WITHOUT any Utah movement outcomes."""
import unittest, tempfile
from pathlib import Path
from datetime import datetime,timedelta
from zipfile import ZipFile
from scripts.movebank_utah_four_taxa_solar_20261019 import (
    CONTRACT,choose_from_timestamp,extract_time_only_original_source,analyze_from_group
)
import json
class Tests(unittest.TestCase):
    def test_freeze_source_specification(self):
        p=json.loads(CONTRACT.read_text())
        self.assertEqual(len(p["source"]["catalog_taxa"]),4)
        self.assertEqual(len(set(p["source"]["catalog_taxa"])),4)
        self.assertEqual(len(p["source"]["original_md5"]),32)
    def test_timestamp_only_selection_independent_of_position(self):
        t=datetime(2020,5,1,12)
        x=(t+timedelta(minutes=21),40,-111)
        y=(t+timedelta(minutes=2),60,-20)
        self.assertEqual(choose_from_timestamp(x,y)[0],y[0])
        self.assertEqual(choose_from_timestamp(x,(y[0],-40,80))[0],y[0])
    def test_taxon_identity_no_cross_taxon_leakage(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"utah.zip"
            csv="timestamp,location-lat,location-long,individual-local-identifier,individual-taxon-canonical-name\n"
            csv+="2020-04-04 12:01:00,40,-110,sharedID,Cervus elaphus\n"
            csv+="2020-04-04 12:02:00,40,-110,sharedID,Odocoileus hemionus\n"
            csv+="2020-04-04 12:50:00,40,-110,sharedID,Cervus elaphus\n"
            with ZipFile(f,"w") as z:z.writestr("study.csv",csv)
            g,c,other=extract_time_only_original_source(f,["Cervus elaphus","Odocoileus hemionus"])
            self.assertEqual(other,0)
            self.assertEqual(len(g["Cervus elaphus"]["sharedID"]),1)
            self.assertEqual(len(g["Odocoileus hemionus"]["sharedID"]),1)
            self.assertEqual(c["Cervus elaphus"]["rows"],2)
            self.assertEqual(next(iter(g["Cervus elaphus"]["sharedID"].values()))[0].minute,1)
    def test_unknown_taxon_not_silently_assigned(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"utah.zip"
            csv="timestamp,location-lat,location-long,individual-local-identifier,individual-taxon-canonical-name\n"
            csv+="2020-04-04 12:01:00,40,-110,a,Unknown mammal\n"
            with ZipFile(f,"w") as z:z.writestr("study.csv",csv)
            g,c,other=extract_time_only_original_source(f,["Cervus elaphus"])
            self.assertEqual(other,1);self.assertEqual(c["Cervus elaphus"]["rows"],0)
    def test_insufficient_source_keeps_undefined(self):
        x=analyze_from_group({},{"rows":0,"valid_rows":0,"invalid_rows":0})
        self.assertEqual(x["effect_status"],"insufficient_independent_animals")
        self.assertIsNone(x["effect"])
if __name__=="__main__":unittest.main()
