"""Known-truth tests independent from original four-taxonomy GPS effect values."""
import unittest,math,json
from scripts.movebank_utah_shared_spatial_20261019 import (
    percentile,cluster_interval,summarize_pair,CONTRACT
)
class Tests(unittest.TestCase):
    def test_source_contract_has_all_six(self):
        obj=json.loads(CONTRACT.read_text())
        self.assertEqual(len(obj["source_effect_replay"]),6)
        self.assertEqual(len(obj["source_overlap_count_replay"]),6)
    def test_constant_geographic_clusters(self):
        self.assertEqual(cluster_interval([.2]*10),[.2,.2])
    def test_no_false_independent_block_uncertainty(self):
        self.assertIsNone(cluster_interval([.1,.2,.3,.4]))
    def test_exact_day_night_q_algebra(self):
        # a=night 0.3 day 0.1, b=night 0.05 day 0.15
        a={"A":{(40,-111,2020,4):(.2,.3,.1)}}
        b={"B":{(40,-111,2020,4):(-.1,.05,.15)}}
        result=summarize_pair("A","B",{**a,**b})
        self.assertAlmostEqual(result["equal_cellmonth_night_minus_day_log1p_difference_a_minus_b"],.3)
        self.assertAlmostEqual(result["equal_cellmonth_night_log1p_difference_a_minus_b"]-
            result["equal_cellmonth_day_log1p_difference_a_minus_b"],.3)
        self.assertEqual(result["distinct_geographic_1degree_spatial_blocks"],1)
        self.assertIsNone(result["spatial_block_cluster_bootstrap_95_interval"])
    def test_equal_block_weight_not_repeated_month_weight(self):
        # Two months from cell 1, one from cell 2 -> equal-cellmonth=2/3, blocks=.5.
        one={(40,-111,2020,4):(1,1,0),(40,-111,2020,5):(1,1,0),(41,-111,2020,5):(0,0,0)}
        two={x:(0,0,0) for x in one}
        r=summarize_pair("A","B",{"A":one,"B":two})
        self.assertAlmostEqual(r["equal_cellmonth_night_minus_day_log1p_difference_a_minus_b"],2/3)
        self.assertAlmostEqual(r["equal_spatial_block_night_minus_day_log1p_difference_a_minus_b"],.5)
        self.assertEqual(r["distinct_geographic_1degree_spatial_blocks"],2)
    def test_zero_support_no_imputation(self):
        r=summarize_pair("A","B",{"A":{},"B":{}})
        self.assertEqual(r["status"],"unsupported")
if __name__=="__main__":unittest.main()
