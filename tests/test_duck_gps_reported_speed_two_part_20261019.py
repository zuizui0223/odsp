import math
import statistics
import unittest
from scripts.duck_gps_reported_speed_two_part_20261019 import date_equal_mixture, seasonal_contrast

class TestReportedSpeedTwoPart(unittest.TestCase):
    def test_zero_median_does_not_require_zero_positive_reporting(self):
        block=[0,0,0,math.log(4)]
        self.assertEqual(statistics.median(block),0)
        d=date_equal_mixture([block])
        self.assertAlmostEqual(d['p'],.25)
        self.assertAlmostEqual(d['C'],math.log(4))
        self.assertAlmostEqual(d['M'],.25*math.log(4))
    def test_dates_not_fix_counts_receive_equal_weight(self):
        d=date_equal_mixture([[0,2],[0]*99+[4]])
        self.assertAlmostEqual(d['p'],.255)
        self.assertAlmostEqual(d['M'],.52)
        self.assertAlmostEqual(d['C'],.52/.255)
    def test_conditional_value_undefined_for_all_zero_samples(self):
        d=date_equal_mixture([[0,0],[0]])
        self.assertEqual(d['p'],0)
        self.assertEqual(d['M'],0)
        self.assertIsNone(d['C'])
    def test_occurrence_only_and_exact_identity(self):
        base=date_equal_mixture([[0,0,0,2]])
        raised=date_equal_mixture([[0,2,2,2]])
        r=seasonal_contrast({'FN':raised,'FD':base,'RN':base,'RD':base})
        self.assertAlmostEqual(r['delta_p'],.5)
        self.assertAlmostEqual(r['delta_M'],1)
        self.assertAlmostEqual(r['occurrence_term'],1)
        self.assertAlmostEqual(r['positive_magnitude_term'],0)
        self.assertLess(r['identity_error'],1e-12)
    def test_magnitude_only_and_no_pseudocount(self):
        base=date_equal_mixture([[0,2]])
        raised=date_equal_mixture([[0,4]])
        r=seasonal_contrast({'FN':raised,'FD':base,'RN':base,'RD':base})
        self.assertAlmostEqual(r['delta_p'],0)
        self.assertAlmostEqual(r['delta_M'],1)
        self.assertAlmostEqual(r['occurrence_term'],0)
        self.assertAlmostEqual(r['positive_magnitude_term'],1)
        zero=date_equal_mixture([[0,0]])
        r=seasonal_contrast({'FN':zero,'FD':base,'RN':base,'RD':base})
        self.assertIsNone(r['delta_C'])
        self.assertIsNone(r['occurrence_term'])
        self.assertAlmostEqual(r['delta_p'],-.5)
    def test_empty_negative_or_nonfinite_samples_are_not_silent_zeros(self):
        for blocks in ([],[[]],[[float('nan')]], [[-1.0]], [[float('inf')]]):
            with self.assertRaises(ValueError):date_equal_mixture(blocks)

if __name__=='__main__':unittest.main()
