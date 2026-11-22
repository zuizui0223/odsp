import math
import unittest
from unittest.mock import patch

from odsp import vertebrate_vertical_study_transfer_v2 as m


def make_site(study,site,taxon="Bats",metric="abundance",beta=2.0):
    heights=(0.,0.5,1.)
    vals=[math.exp(beta*h) for h in heights]
    return [m.SourceRow(study,site,taxon,metric,h,v) for h,v in zip(heights,vals)]


class VertebrateV2StudyTests(unittest.TestCase):
    def test_ties_and_no_context_slope(self):
        src=[]
        for i in range(15):
            src+=make_site(f"s{i}",f"site{i}",beta=0)
        p,a=m.assemble_profiles(src)
        self.assertEqual(a["geometry_qualified_profile_count"],15)
        self.assertEqual(m.fit_beta(p),0)
        self.assertAlmostEqual(m.logscore(p[0],0),-math.log(3))

    def test_duplicate_numeric_heights_are_means_not_extra_record_mass(self):
        src=make_site("s","x")
        src.append(m.SourceRow("s","x","Bats","abundance",0.5,11.0))
        p,a=m.assemble_profiles(src)
        self.assertEqual(a["site_metric_units_with_duplicate_heights"],1)
        self.assertEqual(a["extra_height_rows_collapsed_by_arithmetic_mean"],1)
        expected=(math.exp(0.5*2)+11)/2
        weights=[1,expected,math.exp(2)]
        self.assertAlmostEqual(p[0].q[1],expected/sum(weights),places=12)
        self.assertEqual(len(p[0].heights),3)

    def test_source_zero_preserved_and_bad_y_stops_all(self):
        rows=[
            m.SourceRow("s","x","Bats","abundance",0,0),
            m.SourceRow("s","x","Bats","abundance",1,5),
        ]
        p,_=m.assemble_profiles(rows)
        self.assertEqual(p[0].q,(0.,1.))
        with self.assertRaisesRegex(ValueError,"SOURCE_RESPONSE_STOP"):
            m.assemble_profiles(rows+[m.SourceRow("s","x","Bats","abundance",.5,-1)])

    def test_study_equal_weight_not_row_equal_weight(self):
        src=make_site("s1","site1",beta=4)
        src+=make_site("s2","site2",beta=-4)
        p,_=m.assemble_profiles(src)
        score=m.site_macro_by_study(p,beta=1)
        dup_site=make_site("s1","site3",beta=4)
        p2,_=m.assemble_profiles(src+dup_site)
        self.assertAlmostEqual(score,m.site_macro_by_study(p2,beta=1),places=12)

    def test_heldout_study_cannot_leak_into_any_training_beta(self):
        src=[]
        for taxon in ("Bats","Birds","Amphibians","Small mammals"):
            for i in range(16):
                src+=make_site(f"{taxon}{i}",f"{taxon}_site{i}",taxon=taxon,beta=2)
        p,_=m.assemble_profiles(src)
        original=m.fit_training_slopes(p,"Bats0","abundance")
        changed=[m.Profile(x.study,x.site,x.taxon,x.metric,x.heights,
                           tuple(reversed(x.q)),x.source_rows,x.repeated_height_rows)
                 if x.study=="Bats0" else x for x in p]
        replay=m.fit_training_slopes(changed,"Bats0","abundance")
        self.assertEqual(original,replay)

    def test_taxon_conditioning_transfers_when_stratum_slopes_stable(self):
        src=[]
        for taxon,beta in (("Bats",5.),("Birds",-5.),
                           ("Amphibians",-3.),("Small mammals",3.)):
            for i in range(16):
                src+=make_site(f"{taxon}{i}",f"{taxon}_site{i}",
                               taxon=taxon,beta=beta)
        p,_=m.assemble_profiles(src)
        with patch.object(m,"BOOTSTRAP_REPS",250):
            res=m.evaluate_transfer(p)
        self.assertEqual(res["scores_by_endpoint"]["abundance"]["status"],
                         "prospective_whole_original_study_holdout_evaluated")
        bat=res["scores_by_endpoint"]["abundance"]["by_original_taxon"]["Bats"]
        self.assertGreater(bat["equal_study_mean_gain_nats_per_normalized_profile"],.01)
        self.assertEqual(bat["positive_heldout_study_gains"],16)
        self.assertEqual(bat["source_study_fold_category"],"all-positive")
        self.assertEqual(res["scores_by_endpoint"]["richness"]["status"],
                         "endpoint_insufficient_original_studies")

    def test_common_vertical_policy_has_no_unnecessary_taxon_gain(self):
        src=[]
        for taxon in m.ORIGINAL_TAXA:
            for i in range(15):
                src+=make_site(f"{taxon}{i}",f"{taxon}_site{i}",
                               taxon=taxon,beta=2)
        p,_=m.assemble_profiles(src)
        with patch.object(m,"BOOTSTRAP_REPS",150):
            out=m.evaluate_transfer(p)
        a=out["scores_by_endpoint"]["abundance"]["all_taxa_original_study_summary"]
        self.assertAlmostEqual(a["equal_study_mean_gain_nats_per_normalized_profile"],0,places=10)

    def test_small_training_taxon_uses_exact_global_fallback(self):
        src=[]
        for taxon in m.ORIGINAL_TAXA:
            n=3 if taxon=="Amphibians" else 17
            for i in range(n):
                src+=make_site(f"{taxon}{i}",f"{taxon}{i}",taxon=taxon)
        p,_=m.assemble_profiles(src)
        ref,by=m.fit_training_slopes(p,"Amphibians0","abundance")
        self.assertEqual(by["Amphibians"],(ref,2,False))

if __name__=="__main__":
    unittest.main()
