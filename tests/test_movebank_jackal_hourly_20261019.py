"""Sensitivity registration tests, no animal response read."""
import json,unittest
from scripts.movebank_elephant_hourly_20261019 import choose_one_per_utc_hour
from scripts.movebank_jackal_hourly_20261019 import CONTRACT
from datetime import datetime,timedelta
class Tests(unittest.TestCase):
    def test_hourly_same_as_elephant(self):
        t=datetime(2018,5,1,7)
        d=[(t+timedelta(minutes=n),-19,15) for n in (1,29,52)]
        self.assertEqual(len(choose_one_per_utc_hour(d)),1)
        self.assertEqual(choose_one_per_utc_hour(d)[0][0],t+timedelta(minutes=1))
    def test_freeze(self):
        x=json.loads(CONTRACT.read_text())
        self.assertEqual(x["version"],"etosha-jackal-hourly-blind-sampling-v1")
        self.assertIn("post-outcome",x["status"].lower())
if __name__=="__main__":unittest.main()
