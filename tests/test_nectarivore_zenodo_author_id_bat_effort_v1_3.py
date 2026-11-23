import unittest
from scripts.nectarivore_zenodo_author_id_bat_effort_v1_3 import (
    camera_plant_key,nectar_plant_key,positive_effort,audit
)

def fixture(num=7,bat_invalid=False):
    cam=[];nectar=[]
    for plant in range(1,num+1):
        for z in ("Low","Middle","High"):
            cam.append({"ML_ID":f"ML{plant:02d}","Stratum":z,"Taxa":"Bat",
                        "Hours":"NA" if bat_invalid else "48","Inflorescences":"2"})
            cam.append({"ML_ID":f"ML{plant:02d}","Stratum":z,"Taxa":"Bird",
                        "Hours":"NA","Inflorescences":"2"})
            nectar.append({"ML_ID":str(plant),"Stratum":z,"Year":"2018","Height":"12"})
    return {"CameraTraps.xlsx":cam,
            "Nectar measurements_Strata.xlsx":nectar,
            "Mist-netting_bats.xlsx":[]}

class CanonicalIDTests(unittest.TestCase):
    def test_original_source_grammar(self):
        self.assertEqual(camera_plant_key("ML03"),"3")
        self.assertEqual(camera_plant_key("ML3"),"3")
        self.assertEqual(nectar_plant_key("3"),"3")
        self.assertEqual(nectar_plant_key("20"),"20")
        with self.assertRaisesRegex(ValueError,"grammar"):
            camera_plant_key("C03")

    def test_source_nonpositive_numeric_effort(self):
        self.assertTrue(positive_effort("1.25"))
        self.assertFalse(positive_effort("NA"))
        self.assertFalse(positive_effort("0"))
        self.assertFalse(positive_effort("nan"))

    def test_known_truth_join_and_documented_bird_method_separation(self):
        r=audit(fixture(),{})
        self.assertEqual(r["status"],"canonical_plant_ID_and_Bat_effort_source_admitted")
        self.assertEqual(r["Bat_camera_plants_with_at_least_two_paired_resource_layers"],7)
        self.assertEqual(r["original_plant_IDs_shared_after_author_id_normalization"],7)
        self.assertFalse(r["original_visit_count_nectar_quantity_sugar_pH_bat_capture_association_opened"])

    def test_no_claim_when_bat_camera_effort_missing(self):
        r=audit(fixture(bat_invalid=True),{})
        self.assertEqual(r["status"],"source_plant_Bat_effort_or_duplicate_key_hold")
        self.assertEqual(r["Bat_camera_plants_with_at_least_two_paired_resource_layers"],0)

    def test_same_source_mislabelled_duplicate_ID_hard_stop(self):
        f=fixture()
        f["CameraTraps.xlsx"].append({"ML_ID":"ML1","Stratum":"Low","Taxa":"Bat","Hours":"5","Inflorescences":"2"})
        with self.assertRaisesRegex(ValueError,"collision"):
            audit(f,{})

if __name__=="__main__":
    unittest.main()
