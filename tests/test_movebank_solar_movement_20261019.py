from datetime import datetime
import unittest
from scripts.movebank_solar_movement_20261019 import great_circle_km,valid_interval

class TestStep(unittest.TestCase):
    def test_zero_distance(self):
        self.assertEqual(great_circle_km(0,0,0,0),0)
    def test_one_degree_distance(self):
        self.assertAlmostEqual(great_circle_km(0,0,0,1),111.2,places=1)
    def test_valid_day_step(self):
        t1=datetime(2020,5,20,9);t2=datetime(2020,5,20,10)
        v=valid_interval(t1,45,0,t2,45,0.01)
        self.assertIsNotNone(v)
        self.assertEqual(v[1],"day")
        self.assertGreater(v[2],0)
    def test_dawn_crossing_excluded(self):
        t1=datetime(2020,5,20,4);t2=datetime(2020,5,20,5)
        self.assertIsNone(valid_interval(t1,45,0,t2,45,0))
    def test_gaps_and_unrealistic_speed_excluded(self):
        t1=datetime(2020,5,20,9)
        self.assertIsNone(valid_interval(t1,45,0,datetime(2020,5,20,9,15),45,0.01))
        self.assertIsNone(valid_interval(t1,45,0,datetime(2020,5,20,10),45,2))

if __name__=="__main__": unittest.main()
