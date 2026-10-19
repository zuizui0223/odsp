import unittest
from datetime import datetime,timedelta
from scripts.movebank_elephant_hourly_20261019 import choose_one_per_utc_hour
class Tests(unittest.TestCase):
    def test_blind_to_speed_and_position(self):
        t=datetime(2020,5,1,8)
        a=[(t+timedelta(minutes=m),lat,10) for m,lat in [(35,-20),(4,-19),(45,-17),(57,-18)]]
        s=choose_one_per_utc_hour(a)
        self.assertEqual(len(s),1)
        self.assertEqual(s[0][0],t+timedelta(minutes=4))
    def test_missing_hour_not_invented(self):
        t=datetime(2020,5,1,8)
        a=[(t+timedelta(minutes=5),-20,16),(t+timedelta(hours=2,minutes=3),-20,16)]
        s=choose_one_per_utc_hour(a)
        self.assertEqual(len(s),2)
        self.assertAlmostEqual((s[1][0]-s[0][0]).total_seconds()/3600,1.9666666667)
    def test_order_independence_for_different_times(self):
        t=datetime(2020,4,3,20)
        a=[(t+timedelta(minutes=m),-19,15) for m in (31,2,29,13,47)]
        self.assertEqual(choose_one_per_utc_hour(a),choose_one_per_utc_hour(list(reversed(a))))
    def test_original_gps_coordinates_irrelevant(self):
        t=datetime(2020,4,3,20)
        a=[(t+timedelta(minutes=2),-19,15),(t+timedelta(minutes=30),-20,16)]
        b=[(t+timedelta(minutes=2),-40,50),(t+timedelta(minutes=30),-20,16)]
        self.assertEqual(choose_one_per_utc_hour(a)[0][0],choose_one_per_utc_hour(b)[0][0])
if __name__=="__main__":unittest.main()
