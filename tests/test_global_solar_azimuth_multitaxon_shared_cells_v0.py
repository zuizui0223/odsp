"""Known-truth ecology and complete all-pair support tests for source-original GPS."""
from datetime import date,datetime,timedelta
import unittest
from scripts.solar_azimuth_macro_v0 import Step
from scripts.global_solar_azimuth_multitaxon_shared_cells_v0 import (
    source_preselection,cell_for_step,source_pair_comparisons,
    admit_source_taxon_cells
)


class SameSourceSharedSolarHabitatTest(unittest.TestCase):
    def test_exact_all_ten_existing_multispecies_original_source_roster(self):
        frame=source_preselection()
        self.assertEqual(len(frame),10)
        self.assertEqual(len({x["package_uuid"] for x in frame}),10)
        self.assertTrue(all(len(set(x["original_species_labels"]))>1 for x in frame))

    def test_dateline_cell_kept_private_and_wrapped(self):
        mid=Step(95,140,date(2026,7,7),10,45)
        cell=cell_for_step(mid,
                           (datetime(2026,7,7,9),15,179.9),
                           (datetime(2026,7,7,10),15.2,-179.9))
        self.assertEqual(cell[:2],(15,-180))
        self.assertEqual(cell[4],2)

    def test_all_source_species_pairs_including_unsupported(self):
        k1=(10,20,2026,6,2)
        k2=(10,21,2026,6,2)
        k3=(11,20,2026,7,2)
        def make(v):
            return {"animal_equal_mean":v,"n_animals":3,
                    "source_animal_ids":{"a","b","c"},
                    "source_days":{date(2026,6,1),date(2026,6,2),date(2026,6,3)},
                    "eligible_steps":16}
        a={k:make(.25) for k in (k1,k2,k3)}
        b={k:make(-.15) for k in (k1,k2,k3)}
        out=source_pair_comparisons({"a":a,"b":b,"c":{}},["a","b","c"])
        self.assertEqual(len(out),3)
        supported=[x for x in out if x["status"]=="SUPPORTED_SOURCE_DESCRIPTIVE"]
        self.assertEqual(len(supported),1)
        self.assertEqual(supported[0]["taxa"],["a","b"])
        self.assertAlmostEqual(supported[0]["a_minus_b_solar_relative_bearing_cosine"],.4)
        self.assertEqual(supported[0]["shared_unique_coarse_1degree_spatial_grids"],3)
        self.assertTrue(all("source_cells" not in x for x in out))

    def test_three_animals_three_days_hour_block_is_admitted(self):
        dates=[date(2026,6,1),date(2026,6,2),date(2026,6,3)]
        tracks={}
        for animal in range(3):
            fixes={}
            for d in dates:
                for hour in (8,9,10,11):
                    t=datetime(d.year,d.month,d.day,hour)
                    fixes[t]=(t,15,0.01*animal+0.03*(hour-8))
            tracks[str(animal)]=fixes
        cells=admit_source_taxon_cells(tracks)
        self.assertGreaterEqual(len(cells),1)
        self.assertGreaterEqual(max(x["n_animals"] for x in cells.values()),3)
        self.assertGreaterEqual(max(x["eligible_steps"] for x in cells.values()),15)


if __name__=="__main__":
    unittest.main()
