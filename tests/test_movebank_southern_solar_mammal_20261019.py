"""Fixed astronomical and source-safe controls independent of animal outcomes."""
from datetime import date,datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import json
import unittest
from scripts.movebank_southern_solar_mammal_20261019 import southern_solar_cycle,matched_pairs,safe_unzip_data_csv,analyze_south,CONTRACT
from scripts.movebank_native_ecology_20261019 import daylength
class Tests(unittest.TestCase):
    def test_south_solstice_branch(self):
        self.assertEqual(southern_solar_cycle(date(2019,9,22)),(2019,"rising"))
        self.assertEqual(southern_solar_cycle(date(2020,3,22)),(2019,"falling"))
        self.assertEqual(southern_solar_cycle(date(2019,12,21)),(None,None))
        self.assertEqual(southern_solar_cycle(date(2020,6,21)),(None,None))
    def test_daylength_southern(self):
        self.assertGreater(daylength(-30,date(2019,12,21)),daylength(-30,date(2019,6,21)))
        self.assertAlmostEqual(daylength(-30,date(2019,9,21)),daylength(-30,date(2020,3,20)),delta=.07)
    def test_match_no_date_reuse(self):
        a={}
        for d,branch in [(date(2019,9,21),"rising"),(date(2019,9,22),"rising"),(date(2020,3,20),"falling"),(date(2020,3,21),"falling")]:
            a[d]={"branch":branch,"lat":-30.0,"n_day":3,"n_night":3}
        pairs=matched_pairs(a)
        self.assertGreaterEqual(len(pairs),1)
        self.assertEqual(len(set(x[0] for x in pairs)),len(pairs))
        self.assertEqual(len(set(x[1] for x in pairs)),len(pairs))
    def test_reject_insufficient_observation(self):
        a={date(2019,9,22):{"branch":"rising","lat":-30.0,"n_day":3,"n_night":3},
           date(2020,3,22):{"branch":"falling","lat":-30.0,"n_day":18,"n_night":18}}
        self.assertEqual(matched_pairs(a),[])
    def test_zip_only_one_primary(self):
        with TemporaryDirectory() as t:
            inp=Path(t)/"o.zip";out=Path(t)/"d.csv"
            with ZipFile(inp,"w") as z:
                z.writestr("main.csv","one,two\n"+"1,2\n"*55)
                z.writestr("main-reference-data.csv","id\n"+"a\n"*4)
            self.assertGreater(safe_unzip_data_csv(inp,out),128)
            self.assertEqual(out.read_text().splitlines()[0],"one,two")
    def test_zip_multiple_candidate_failclosed(self):
        with TemporaryDirectory() as t:
            z=Path(t)/"bad.zip"
            with ZipFile(z,"w") as arc:
                arc.writestr("one.csv","a,b\n"+("1,2\n"*100))
                arc.writestr("two.csv","a,b\n"+("1,2\n"*100))
            with self.assertRaises(ValueError):safe_unzip_data_csv(z,Path(t)/"out.csv")
    def test_missing_schema_no_effect(self):
        with TemporaryDirectory() as t:
            p=Path(t)/"d.csv"
            p.write_text("timestamp,species\n2020-01-01 00:00:00,x\n")
            with self.assertRaises(ValueError):analyze_south(p)
    def test_source_pins(self):
        x=json.loads(CONTRACT.read_text())
        self.assertEqual(len(x["sources"]),3)
        self.assertEqual(len({s["package_uuid"] for s in x["sources"]}),3)
        self.assertTrue(all(len(s["provider_original_md5"])==32 for s in x["sources"]))
if __name__=="__main__":unittest.main()
