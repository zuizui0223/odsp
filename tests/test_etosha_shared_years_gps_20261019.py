import unittest
from datetime import datetime
from scripts.movebank_native_ecology_20261019 import solar_period
from scripts.movebank_southern_solar_mammal_20261019 import southern_solar_cycle
from scripts.etosha_shared_years_gps_20261019 import shared_year_loader
class Tests(unittest.TestCase):
    def test_inclusion_by_local_solar_cycle(self):
        for t,expected in [
           (datetime(2009,9,15,12),True),
           (datetime(2010,4,12,12),True),
           (datetime(2010,9,15,12),True),
           (datetime(2011,4,12,12),True),
           (datetime(2011,9,15,12),False),
           (datetime(2008,9,15,12),False)]:
            local,_=solar_period(t,-19,16)
            y,_=southern_solar_cycle(local)
            self.assertEqual(y in (2009,2010),expected)
    def test_southern_solstice_excluded(self):
        self.assertEqual(southern_solar_cycle(__import__("datetime").date(2009,12,21)),(None,None))
if __name__=="__main__":unittest.main()
