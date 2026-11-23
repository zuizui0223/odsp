import unittest
from scripts.nectarivore_zenodo_source_v1_1_pairs import admitted_source_structure


def source(num_plants=6,missing_hours=False):
    camera=[]
    nectar=[]
    net=[]
    for i in range(num_plants):
        ident="Plant"+str(i)
        for z in ("understory","midstory","canopy"):
            for animal in ("bats","birds"):
                camera.append({"ML_ID":ident,"Taxa":animal,"Stratum":z,
                               "Hours":"" if (missing_hours and i==0) else "8",
                               "Inflorescences":"2"})
            nectar.append({"ML_ID":ident,"Stratum":z,"Year":"2023","Height":"10"})
        net.append({"ML_ID":ident,"Type":"plant","Species":"BatSpecies",
                    "Net":"A","Height":"12","Feeding_guild":"nectarivore"})
    return {
        "CameraTraps.xlsx":camera,
        "Mist-netting_bats.xlsx":net,
        "Nectar measurements_Strata.xlsx":nectar,
    }


class PairedSourceUnitTests(unittest.TestCase):
    def test_exact_plant_and_stratum_pairing_and_positive_effort(self):
        r=admitted_source_structure(source(),{"test":"synthetic"})
        self.assertEqual(r["status"],"source_plant_level_pairing_and_effort_admitted")
        self.assertEqual(r["paired_plant_IDs_with_ge2_strata"],6)
        self.assertEqual(r["paired_plant_IDs_with_ge3_strata"],6)
        self.assertEqual(r["paired_visit_nectar_exact_ID_stratum_units"],18)
        self.assertEqual(r["camera_taxon_labels"],["bats","birds"])
        self.assertFalse(r["response_Abundance_or_Capture_rate_or_nectar_values_opened"])

    def test_not_enough_plants_is_source_hold(self):
        r=admitted_source_structure(source(3),{})
        self.assertEqual(r["status"],"source_plant_level_pairing_or_effort_hold")
        self.assertEqual(r["paired_plant_IDs_with_ge2_strata"],3)

    def test_missing_camera_effort_is_source_hold(self):
        r=admitted_source_structure(source(missing_hours=True),{})
        self.assertEqual(r["status"],"source_plant_level_pairing_or_effort_hold")
        self.assertEqual(r["missing_camera_Hours_exposure"],6)

    def test_unmatched_height_labels_do_not_get_implicitly_joined(self):
        tables=source()
        for r in tables["Nectar measurements_Strata.xlsx"]:
            if r["Stratum"]=="canopy":r["Stratum"]="upper canopy"
        result=admitted_source_structure(tables,{})
        self.assertEqual(result["paired_plant_IDs_with_ge3_strata"],0)
        self.assertEqual(result["paired_visit_nectar_exact_ID_stratum_units"],12)

if __name__=="__main__":
    unittest.main()
