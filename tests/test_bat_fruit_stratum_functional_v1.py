import hashlib
import math
import unittest
from unittest.mock import patch

from odsp import bat_fruit_stratum_functional_v1 as lane


class BatFruitFunctionalTests(unittest.TestCase):
    def test_source_tab_header_and_no_negative_counts(self):
        raw=("\tBatA\tBatB\nFruitA\t1\t0\nFruitB\t0\t2\n").encode()
        c,meta=lane.parse_author_matrix(raw)
        self.assertEqual(meta["total"],3)
        self.assertEqual(meta["bat_count"],2)
        self.assertEqual(meta["nonzero_bat_plant_cells"],2)
        self.assertEqual(c[("BatB","FruitB")],2)
        bad=raw.replace(b"FruitB\t0\t2",b"FruitB\t0\t-2")
        with self.assertRaisesRegex(ValueError,"nonnegative"):
            lane.parse_author_matrix(bad)
    def test_original_git_blob_hash_is_real_git_object_sha1(self):
        raw=b"hello world\n"
        expect=hashlib.sha1(b"blob 12\0hello world\n").hexdigest()
        self.assertEqual(lane.source_git_sha1(raw),expect)

    def test_three_source_matrices_reconcile_pooled_omitted_column(self):
        a=lane.parse_author_matrix(b"\tBatA\tBatB\nFruitA\t1\t1\nFruitB\t0\t0\n")
        b=lane.parse_author_matrix(b"\tBatA\tBatB\nFruitA\t0\t0\nFruitB\t1\t0\n")
        c=lane.parse_author_matrix(b"\tBatA\tBatB\nFruitA\t1\t0\nFruitB\t0\t0\n")
        pooled=lane.parse_author_matrix(b"\tBatA\tBatB\nFruitA\t2\t1\nFruitB\t1\t0\n")
        fake={
          "canopy":{"counts":a[0],"details":a[1],"source_git_blob_sha1":"a","source_file_sha256":"a","original_file_bytes":1},
          "subcanopy":{"counts":b[0],"details":b[1],"source_git_blob_sha1":"b","source_file_sha256":"b","original_file_bytes":1},
          "understory":{"counts":c[0],"details":c[1],"source_git_blob_sha1":"c","source_file_sha256":"c","original_file_bytes":1},
          "pooled":{"counts":pooled[0],"details":pooled[1],"source_git_blob_sha1":"d","source_file_sha256":"d","original_file_bytes":1},
        }
        with (patch.object(lane,"EXPECTED_LAYER_TOTALS",{"canopy":2,"subcanopy":1,"understory":1}),
              patch.object(lane,"EXPECTED_TOTAL",4),
              patch.object(lane,"EXPECTED_BAT_LABELS",2),
              patch.object(lane,"EXPECTED_PLANT_LABELS",2),
              patch.object(lane,"EXPECTED_POOLED_POSITIVE_PAIRS",3),
              patch.dict(lane.SOURCE_FILES,{"canopy":("c","a"),"subcanopy":("s","b"),"understory":("u","c"),"pooled":("p","d")}),
              patch.object(lane,"source_metrics")):
            # Code has deliberately fixed source cohort specific bat-header
            # expectations, so toy narrower headers must not be accepted.
            with self.assertRaisesRegex(ValueError,"unexpected"):
                lane.audit_author_tensor(fake)

    def test_exact_conditional_information_for_functional_partition(self):
        observed={
            ("BatA","Plant1","canopy"):10,
            ("BatA","Plant2","understory"):10,
            ("BatB","Plant1","canopy"):10,
            ("BatB","Plant1","understory"):10,
        }
        mi=lane.conditional_information(observed,1,2,0)
        target=(20/40)*math.log(2)+(10/40)*math.log(2)+(10/40)*0
        # Explicit check against independently computed per-bat entropies.
        independently=lane.conditional_entropy(observed,1,(0,))-lane.conditional_entropy(observed,1,(0,2))
        self.assertAlmostEqual(mi,independently,places=12)
        self.assertGreater(mi,0)
        self.assertAlmostEqual(lane.source_metrics(observed)["observed_interaction_I_plant_stratum_given_bat_nats"],mi)

    def test_zero_threeway_information_when_resource_state_is_conditionally_constant(self):
        observed={}
        for b in ("BatA","BatB"):
            for p in ("Plant1","Plant2"):
                for z in ("canopy","understory"):
                    observed[(b,p,z)]=10
        self.assertAlmostEqual(lane.conditional_information(observed,1,2,0),0,places=12)
        self.assertAlmostEqual(lane.conditional_information(observed,0,2,1),0,places=12)

    def test_null_shuffling_within_group_preserves_margins_and_is_reproducible(self):
        source={}
        for b in ("BatA","BatB"):
            for p in ("Fruit1","Fruit2"):
                for z in ("canopy","understory"):
                    source[(b,p,z)]=10
        with patch.object(lane,"N_PERMUTATIONS",59):
            a=lane._shuffle_nulls(source,0,1,2,20261123)
            b=lane._shuffle_nulls(source,0,1,2,20261123)
            c=lane._shuffle_nulls(source,1,0,2,20261124)
        self.assertEqual(a,b)
        self.assertEqual(len(a),59)
        self.assertTrue(all(math.isfinite(v) and v>=0 for v in c))
        self.assertGreater(sum(a)/len(a),0)
        nr=lane.null_report(0,a,20261123)
        self.assertEqual(nr["upper_tail_conditional_exchangeability_p"],1.0)

if __name__=="__main__":
    unittest.main()
