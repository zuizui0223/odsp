"""Known-truth temporal grouping and coverage, independent of source GPS effects."""
import unittest
from datetime import datetime,date,timedelta
from scripts.etosha_yearly_ecology_20261019 import (
    choose_solar_cycles,shared_date_coverage,calendar_coverage
)
class Tests(unittest.TestCase):
    def test_southern_solar_year_filter_dates(self):
        anchor=datetime(2009,9,15,12)
        rows=[(anchor,-19,16),(datetime(2010,3,15,12),-19,16),
              (datetime(2010,9,15,12),-19,16),(datetime(2011,4,15,12),-19,16),
              (datetime(2011,9,15,12),-19,16)]
        x=choose_solar_cycles({"a":rows},{2009})
        self.assertEqual(len(x["a"]),2)
        y=choose_solar_cycles({"a":rows},{2010})
        self.assertEqual(len(y["a"]),2)
        z=choose_solar_cycles({"a":rows},{2009,2010})
        self.assertEqual(len(z["a"]),4)
    def test_pair_overlap_is_calendar_not_animal_count(self):
        a,b,c,d=[date(2010,1,1)+timedelta(days=i) for i in (0,1,50,51)]
        x={"animal1":[[(a,c),(b,d)]],"animal2":[[(a,c)]]}
        y={"other":[[(a,c),(a,d)]]}
        res=shared_date_coverage(x,y)
        self.assertEqual(res["identical_unique_date_pairs_supported_in_both_sources"],1)
        self.assertEqual(res["individual_matched_pairs_elephant"],3)
        self.assertEqual(res["individual_matched_pairs_jackal"],2)
        self.assertEqual(res["common_unique_rising_dates"],1)
        self.assertEqual(res["common_unique_falling_dates"],1)
    def test_empty_year_is_reported_without_inventing_calendar_days(self):
        n=shared_date_coverage({}, {})
        self.assertEqual(n["identical_unique_date_pairs_supported_in_both_sources"],0)
        self.assertEqual(calendar_coverage({})["count_total_individual_matched_pairs"],0)
if __name__=="__main__":unittest.main()
