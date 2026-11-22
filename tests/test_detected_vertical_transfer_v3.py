import hashlib
import math
import unittest
from unittest.mock import patch
from odsp.detected_vertical_transfer import (
    Record,conditional_information_given_hour,minimum_detector_ratio_to_erase_partition,
    score_recorded_stratum_by_day
)
from scripts import gomes_zenodo_detected_height_v3 as adapter

class DetectedVerticalTests(unittest.TestCase):
    @staticmethod
    def source(proportions=(90,10)):
        rows=[]
        for day in range(10,19):
            for hour in (20,21):
                for bat,nabove in zip(("A","B"),proportions):
                    rows.extend(Record(str(day),hour,bat,"above") for _ in range(nabove))
                    rows.extend(Record(str(day),hour,bat,"below") for _ in range(100-nabove))
        return rows
    def test_known_truth_information_and_heldout_improvement(self):
        src=self.source()
        v=score_recorded_stratum_by_day(src)
        exact=math.log(2)+.9*math.log(.9)+.1*math.log(.1)
        self.assertAlmostEqual(conditional_information_given_hour(src),exact,places=11)
        self.assertEqual(v["n_day_folds"],9)
        self.assertEqual(v["transfer_category"],"all_days_positive")
        self.assertGreater(v["equal_day_delta_nats_per_record"],.3)
        self.assertGreater(v["delta_day_bootstrap_95pct_descriptive"][0],0)
    def test_no_species_organization_has_no_transfer_gain(self):
        src=self.source((50,50))
        v=score_recorded_stratum_by_day(src)
        self.assertAlmostEqual(v["equal_day_delta_nats_per_record"],0,places=10)
        self.assertAlmostEqual(v["in_sample_observed_record_I_bat_stratum_given_hour_nats"],0,places=10)
    def test_threshold_matches_two_world_observation_witness(self):
        counts={"A":{"above":9,"below":1},"B":{"above":1,"below":9}}
        self.assertAlmostEqual(minimum_detector_ratio_to_erase_partition(counts,alpha=0),9)
        self.assertGreater(minimum_detector_ratio_to_erase_partition(counts,alpha=.5),7)
    def test_stops_unseen_hour(self):
        src=[Record("a",20,"S","above"),Record("b",21,"S","below")]
        with self.assertRaisesRegex(ValueError,"hour"):
            score_recorded_stratum_by_day(src)
    def test_pinned_source_adapter_never_reads_number(self):
        header=adapter.KNOWN_HEADER
        values={h:"SEALED" for h in header}
        values.update({"DAY":"10","HOUR":"20","Bat":"AA","POS":"above"})
        row=",".join(values[h] for h in header)
        raw=(",".join(header)+"\n"+row+"\n").encode()
        with (patch.object(adapter,"EXPECTED_MD5",hashlib.md5(raw).hexdigest()),
              patch.object(adapter,"SOURCE_SHA256",hashlib.sha256(raw).hexdigest()),
              patch.object(adapter,"EXPECTED_ROWS",1),
              patch.object(adapter,"EXPECTED_DAYS",1),
              patch.object(adapter,"EXPECTED_BAT_LABELS",1),
              patch.object(adapter,"EXPECTED_HOURS",1)):
            records=adapter.records_from_original(raw)
        self.assertEqual(len(records),1)
        self.assertEqual(records[0].recorded_stratum,"above")

if __name__=="__main__":
    unittest.main()
