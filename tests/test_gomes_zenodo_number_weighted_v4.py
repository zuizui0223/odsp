import hashlib,math
import unittest
from unittest.mock import patch
from odsp.weighted_detected_vertical_transfer import (
    CountCell,score_weighted_counts,condition_information_from_counts
)
from scripts import gomes_zenodo_number_weighted_v4 as adapter

class CountWeightedTests(unittest.TestCase):
    def synthetic(self,split=True):
        cells=[]
        for day in map(str,range(10,19)):
            for hour in (19,20):
                for sp in ("A","B"):
                    above=90 if sp=="A" else (10 if split else 90)
                    cells.append(CountCell(day,hour,sp,"above",above))
                    cells.append(CountCell(day,hour,sp,"below",100-above))
        return cells
    def test_known_species_height_count_information_recovers_and_transfers(self):
        c=self.synthetic()
        r=score_weighted_counts(c)
        expected=math.log(2)+.9*math.log(.9)+.1*math.log(.1)
        self.assertAlmostEqual(condition_information_from_counts(c),expected,places=11)
        self.assertEqual(r["retained_acoustic_labels_author_rule"],2)
        self.assertEqual(r["nine_day_transfer_category"],"all_days_positive")
        self.assertGreater(r["B1_minus_B0_equal_day_gain_nats_per_recorded_count"],.3)
        self.assertGreater(r["day_gain_bootstrap_95pct_descriptive"][0],.3)
    def test_no_label_stratification_baseline_is_sufficient(self):
        r=score_weighted_counts(self.synthetic(split=False))
        self.assertAlmostEqual(r["in_sample_recorded_count_weighted_I_label_stratum_given_hour_nats"],0,places=10)
        self.assertAlmostEqual(r["B1_minus_B0_equal_day_gain_nats_per_recorded_count"],0,places=10)
    def test_author_original_rare_label_rule_preserved(self):
        c=self.synthetic()+[CountCell("10",20,"rare","above",5)]
        r=score_weighted_counts(c)
        self.assertEqual(r["author_rule_excluded_labels_total_le5"],1)
        self.assertEqual(r["source_total_number_counts_including_rare_labels"],3605)
        self.assertEqual(r["total_scored_recorded_counts_retained"],3600)
    def test_non_integer_author_number_does_not_get_rounded(self):
        head=adapter.KNOWN_HEADER
        v={k:"0" for k in head}
        v.update({"DAY":"10","HOUR":"20","Bat":"AA","POS":"above","Number":"1.4"})
        raw=(",".join(head)+"\n"+",".join(v[k] for k in head)+"\n").encode()
        with (patch.object(adapter,"EXPECTED_MD5",hashlib.md5(raw).hexdigest()),
              patch.object(adapter,"SOURCE_SHA256",hashlib.sha256(raw).hexdigest())):
            with self.assertRaisesRegex(ValueError,"nonnegative integer"):
                adapter.parse_original(raw)
    def test_original_source_adapter_reads_only_count_column(self):
        head=adapter.KNOWN_HEADER
        v={k:"SEALED" for k in head}
        v.update({"DAY":"10","HOUR":"20","Bat":"AA","POS":"above","Number":"0"})
        raw=(",".join(head)+"\n"+",".join(v[k] for k in head)+"\n").encode()
        with (patch.object(adapter,"EXPECTED_MD5",hashlib.md5(raw).hexdigest()),
              patch.object(adapter,"SOURCE_SHA256",hashlib.sha256(raw).hexdigest()),
              patch.object(adapter,"EXPECTED_SOURCE_ROWS",1)):
            # Needs nine day/21 class original support, so guards reject; not the sealed fields.
            with self.assertRaisesRegex(ValueError,"mismatch to pre-open"):
                adapter.parse_original(raw)

if __name__=="__main__":
    unittest.main()
