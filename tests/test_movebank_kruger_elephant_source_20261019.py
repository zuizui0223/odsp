"""Frozen source/hemisphere verification independent of Kruger animal GPS outcomes."""
import unittest,json,csv
from pathlib import Path
from datetime import date,datetime
from tempfile import TemporaryDirectory
from scripts.movebank_kruger_elephant_source_20261019 import CONTRACT,read_column_names_only
from scripts.movebank_southern_solar_mammal_20261019 import southern_solar_cycle
from scripts.movebank_elephant_hourly_20261019 import choose_one_per_utc_hour

class Tests(unittest.TestCase):
    def test_original_source_identifiers(self):
        p=json.loads(CONTRACT.read_text())
        self.assertEqual(p["version"],"african-elephant-independent-kruger-source-v0")
        self.assertEqual(len(p["source"]["original_md5"]),32)
        self.assertEqual(p["source"]["taxon"],"Loxodonta africana")
        self.assertEqual(p["source"]["original_bytes"],43776326)
    def test_southern_summer_not_northern(self):
        self.assertEqual(southern_solar_cycle(date(2007,10,21)),(2007,"rising"))
        self.assertEqual(southern_solar_cycle(date(2008,2,21)),(2007,"falling"))
    def test_only_header_read(self):
        with TemporaryDirectory() as t:
            file=Path(t)/"data.csv"
            file.write_text("timestamp,location-lat,individual-local-identifier\n2007-01-01,-24,x\n")
            self.assertEqual(read_column_names_only(file),["timestamp","location-lat","individual-local-identifier"])
    def test_clock_selection_timestamp_only(self):
        t=datetime(2007,10,21,12)
        a=[(t.replace(minute=m),-24,31) for m in (45,2,31)]
        self.assertEqual(choose_one_per_utc_hour(a)[0][0].minute,2)
if __name__=="__main__":unittest.main()
