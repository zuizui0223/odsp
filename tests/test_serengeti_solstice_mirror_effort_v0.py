"""Synthetic astronomy / site-roster tests: no Serengeti wildlife rows involved."""
from datetime import date, timedelta
import unittest

from scripts.assess_serengeti_solstice_mirror_effort_v0 import (
    merge_intervals, mirror_pairs, parse_date, MIN_SOLSTICE_DISTANCE_DAYS
)


class TestSerengetiMirrorSourceOnly(unittest.TestCase):
    def test_calendar_mirrors_cross_year(self):
        a=date(2012, 12, 21)
        intervals=[(a-timedelta(days=70),a+timedelta(days=70))]
        pairs=mirror_pairs(intervals,2012)
        self.assertEqual(len(pairs),70-MIN_SOLSTICE_DISTANCE_DAYS+1)
        self.assertEqual((pairs[0][0],pairs[0][1]),(a-timedelta(days=7),a+timedelta(days=7)))
        self.assertEqual((pairs[-1][0],pairs[-1][1]),(a-timedelta(days=70),a+timedelta(days=70)))
        self.assertEqual(pairs[-1][1].year,2013)

    def test_one_branch_has_no_pairs(self):
        a=date(2013,12,21)
        self.assertEqual(mirror_pairs([(a-timedelta(days=170), a)],2013),[])

    def test_merged_overlap_does_not_inflate_site_support(self):
        merged=merge_intervals([
            (date(2012,11,1),date(2013,2,1)),
            (date(2012,11,10),date(2013,2,5)),
        ])
        self.assertEqual(len(merged),1)
        self.assertEqual(len(mirror_pairs(merged,2012)),40)

    def test_invalid_source_dates_not_silently_reversed(self):
        with self.assertRaises(ValueError):
            merge_intervals([(date(2021,5,10),date(2021,5,1))])
        with self.assertRaises(ValueError):
            parse_date("not a date")


if __name__=="__main__":
    unittest.main()
