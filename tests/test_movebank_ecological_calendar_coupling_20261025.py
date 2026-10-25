"""Ecological calendar coupling: known-truth algebra, invalid rank and source locks."""
import json,unittest
from scripts.movebank_ecological_calendar_coupling_20261025 import (
    CONTRACT,year_decomposition,simple_slope,summarize
)
class Tests(unittest.TestCase):
    def test_source_contract_covers_all_six_public_taxa(self):
        r=json.loads(CONTRACT.read_text())
        self.assertEqual(r["version"],"odsp-two-study-solar-ecological-calendar-coupling-v0")
        self.assertEqual(len(r["sources"]["utah"]["taxa"]),4)
        self.assertEqual(len(r["sources"]["wyoming"]["taxa"]),2)
    def test_known_three_component_identity(self):
        rows=[]
        for i in range(30):
            daylight=10.0+.14*i
            temp=10+.85*i+(i%4-1.5)*1.7
            water=-2+.33*i+(i%5-2)*.37
            q=.008*daylight + .003*temp-.07*water
            rows.append((temp,water,daylight,q))
        r=year_decomposition(rows)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r["conditional_L_association"],.008,places=10)
        self.assertAlmostEqual(r["conditional_Tmax_coefficient_per_C"],.003,places=10)
        self.assertAlmostEqual(r["conditional_PminusET0_coefficient_per100mm"],-.07,places=10)
        self.assertAlmostEqual(r["raw_L_association_on_exact_joint_sample"],
             r["conditional_L_association"]+r["seasonal_Tmax_calendar_component"]+
             r["seasonal_PminusET0_calendar_component"],places=10)
    def test_complete_collinearity_is_UNAVAILABLE(self):
        rows=[(2*i,3*i,10+.3*i,.5*i) for i in range(30)]
        self.assertIsNone(year_decomposition(rows))
    def test_fewer_than_fifteen_original_animal_days_unavailable(self):
        rows=[(2*i,3*i,10+.3*i,.5*i) for i in range(14)]
        self.assertIsNone(year_decomposition(rows))
    def test_calendar_groups_require_animals_not_pseudoreplicated_days(self):
        x,c=summarize({},{"original_source_animal_years":100})
        self.assertEqual(x["estimable_source_individuals"],0)
        self.assertIsNone(x["source_equal_individual_associations"]["conditional_L_association"]["equal_animal_mean"])
if __name__=="__main__":unittest.main()
