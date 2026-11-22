import hashlib
import unittest
from unittest.mock import patch
from odsp.gomes_tower_transfer_v6 import TowerCell,score_tower_transfer
from scripts import gomes_tower_transfer_v6 as adapter


def fixtures(*, opposite=False):
    records=[]
    for tower in ("green","red"):
        for day in map(str,range(10,19)):
            for hour in (20,21):
                for label in ("A","B"):
                    above=9 if label=="A" else 1
                    if opposite and tower=="red":
                        above=10-above
                    records.append(TowerCell(day,hour,label,"above",above,tower))
                    records.append(TowerCell(day,hour,label,"below",10-above,tower))
    return records


class GomesTowerTests(unittest.TestCase):
    def test_stable_structuring_transfers_to_both_towers(self):
        r=score_tower_transfer(fixtures())
        self.assertEqual(r["leave_one_tower_out"]["positive_tower_folds"],2)
        self.assertEqual(r["leave_both_tower_and_night_out"]["n_tower_day_folds"],18)
        self.assertEqual(r["leave_both_tower_and_night_out"]["positive_tower_day_folds"],18)
        self.assertGreater(r["leave_one_tower_out"]["equal_tower_mean_delta_nats_per_count"],.15)
        self.assertGreater(r["leave_both_tower_and_night_out"]["equal_tower_then_day_delta_nats_per_count"],.15)

    def test_reversed_tower_structure_does_not_masquerade_as_transfer(self):
        r=score_tower_transfer(fixtures(opposite=True))
        self.assertEqual(r["leave_one_tower_out"]["positive_tower_folds"],0)
        self.assertLess(r["leave_one_tower_out"]["equal_tower_mean_delta_nats_per_count"],-.2)
        self.assertEqual(r["leave_both_tower_and_night_out"]["positive_tower_day_folds"],0)

    def test_original_zero_and_negative_count_contract(self):
        rows=fixtures()
        r=score_tower_transfer(rows)
        self.assertEqual(r["original_count_weighted_n"],720)
        with self.assertRaisesRegex(ValueError,"Number"):
            score_tower_transfer([*rows,TowerCell("10",20,"B","above",-1,"green")])

    def test_only_author_fields_opened(self):
        header=adapter.KNOWN_HEADER
        r={h:"SEALED" for h in header}
        r.update({"DAY":"10","HOUR":"20","Bat":"AA","POS":"above","Number":"0","COLOR":"green"})
        raw=(",".join(header)+"\n"+",".join(r.get(h,"") for h in header)+"\n").encode()
        with (patch.object(adapter,"EXPECTED_MD5",hashlib.md5(raw).hexdigest()),
              patch.object(adapter,"SOURCE_SHA256",hashlib.sha256(raw).hexdigest())):
            with self.assertRaisesRegex(ValueError,"structure/total mismatch"):
                adapter.parse_source_towers(raw)

    def test_no_artificial_new_tower(self):
        rows=[r._replace(tower="bad") if r.tower=="red" else r for r in fixtures()]
        with self.assertRaisesRegex(ValueError,"two source-authenticated towers"):
            score_tower_transfer(rows)

if __name__=="__main__":
    unittest.main()
