import unittest
from scripts.audit_duck_gps_identifiability_20261019 import maximum_matching, diagnose, zero_summary

class IdentifiabilityTests(unittest.TestCase):
    def test_greedy_can_lose_capacity_without_changing_calipers(self):
        # Choosing (a,x) first leaves b unmatched; optimum pairs a-y and b-x.
        graph={'a':['x','y'],'b':['x']}
        self.assertEqual(len(maximum_matching(graph)),2)

    def test_empty_graph(self):
        self.assertEqual(maximum_matching({}),{})
        self.assertEqual(maximum_matching({'a':[]}),{})

    def test_loss_reason_order(self):
        self.assertEqual(diagnose(4,10,4,4,4),'day_night_sampling')
        self.assertEqual(diagnose(8,8,3,3,3),'photoperiod_overlap')
        self.assertEqual(diagnose(8,8,8,4,4),'fix_count_balance')
        self.assertEqual(diagnose(8,8,8,6,4),'greedy_pairing')
        self.assertEqual(diagnose(8,8,8,6,5),'included_v0')

    def test_zero_is_not_missing_or_inactivity(self):
        out=zero_summary([[0,0,7],[0,0,0],[1,2,3]])
        self.assertEqual(out['zone_medians_zero'],2)
        self.assertEqual(out['zone_medians_total'],3)
        self.assertEqual(out['sensor_samples_zero'],5)
        self.assertEqual(out['sensor_samples_total'],9)

    def test_max_matching_bruteforce(self):
        import itertools
        for flags in itertools.product((0,1),repeat=9):
            g={i:[j for j in range(3) if flags[3*i+j]] for i in range(3)}
            best=0
            for perm in itertools.product((-1,0,1,2),repeat=3):
                chosen=[j for j in perm if j>=0]
                if len(set(chosen))!=len(chosen): continue
                if all(j<0 or j in g[i] for i,j in enumerate(perm)):
                    best=max(best,len(chosen))
            self.assertEqual(len(maximum_matching(g)),best)

if __name__=='__main__': unittest.main()
