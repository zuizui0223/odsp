"""Source-free known-truth tests for the preregistered Bat × liana nectar predictor.

Synthetic counts are explicitly not Thiel et al. real outcomes.
"""
from math import exp
import unittest
from unittest.mock import patch

from odsp import nectarivore_bat_resource_transfer_v2 as m
from scripts import nectarivore_bat_plant_resource_transfer_v2 as a


def synthetic_plants(beta=1.5,constant_resource=False):
    plants=[]
    heights=("Low","Middle","High")
    for index in range(9):
        # Counterbalanced source-independent cross-plant nectar strata.
        resources=(4.,4.,4.) if constant_resource else tuple(
            (0.,2.,15.)[(i+index)%3] for i in range(3))
        exposure=tuple((6.,8.,10.)[(i+2*index)%3] for i in range(3))
        intensity=[exposure[i]*(1+r)**beta for i,r in enumerate(resources)]
        k=150/sum(intensity)
        visits=[max(1,int(round(k*t))) for t in intensity]
        layers=tuple(m.Layer(h,exposure[i],resources[i],visits[i])
                     for i,h in enumerate(heights))
        plants.append(m.Plant(f"source_{index}",layers))
    return plants


class NectarBatPlantV2Tests(unittest.TestCase):
    def test_no_nectar_gradient_gives_no_added_information(self):
        plants=synthetic_plants(beta=1.5,constant_resource=True)
        with patch.object(m,"N_BOOT",120):
            result=m.evaluate(plants)
        self.assertAlmostEqual(
            result["mean_B1_minus_B0_nats_per_recorded_visit"],0,places=10)
        self.assertEqual(result["n_heldout_original_plants"],9)

    def test_strong_crossplant_resource_gradient_transfers(self):
        plants=synthetic_plants(beta=1.5)
        with patch.object(m,"N_BOOT",120):
            result=m.evaluate(plants)
        self.assertGreater(result["mean_B1_minus_B0_nats_per_recorded_visit"],.05)
        self.assertGreaterEqual(result["positive_heldout_plant_folds"],7)
        self.assertEqual(result["paired_height_cell_count"],27)
        self.assertEqual(result["fold_sign_category"],"all-positive")

    def test_training_never_contains_a_heldout_plant(self):
        plants=synthetic_plants(beta=1.5)
        training=[p for p in plants if p.identity!="source_0"]
        ref=m.fit(training,True)
        alt=[m.Plant(p.identity,tuple(
             m.Layer(z.name,z.exposure,z.resource,z.visits+100)
             for z in p.layers)) if p.identity=="source_0" else p
             for p in plants]
        replay=m.fit([p for p in alt if p.identity!="source_0"],True)
        self.assertEqual(ref,replay)

    def test_whole_source_stops_if_one_plant_has_zero_visits(self):
        plants=synthetic_plants()
        empty=m.Plant("no_visits",tuple(
            m.Layer(z.name,z.exposure,z.resource,0) for z in plants[0].layers))
        with self.assertRaisesRegex(ValueError,"SOURCE_RESPONSE_STOP"):
            m.evaluate(plants[:8]+[empty])

    def test_bad_resource_effort_and_duplicate_layer_fail_closed(self):
        src=synthetic_plants()
        bad_plant=m.Plant("source_0",tuple([
            m.Layer("Low",-1.,3.,10),
            *src[0].layers[1:]]))
        with self.assertRaisesRegex(ValueError,"invalid paired positive effort"):
            m.validate([bad_plant]+src[1:])
        duplicate=m.Plant("source_0",(src[0].layers[0],
                                      src[0].layers[0],src[0].layers[2]))
        with self.assertRaisesRegex(ValueError,"duplicate"):
            m.validate([duplicate]+src[1:])

    def test_source_only_nine_plants_have_25_layers_tenth_singleton_excluded(self):
        # Purely synthetic source of same frozen *structural* size as the
        # original: 180 Camera rows, 40 Nectar rows, 10 source nectars.
        # Nine plants have >=2 bat-deployed layers (7×3+2×2=25), while
        # plant 10 has only 1 camera-deployed layer and is not analyzable.
        heights=("Low","Middle","High")
        cam=[]
        nectar=[]
        for i in range(1,11):
            zcam=heights if i<=7 else heights[:2] if i<=9 else heights[:1]
            for z in zcam:
                cam.append({"ML_ID":f"ML{i:02}","Taxa":"Bat",
                    "Stratum":z,"Hours":"24","Inflorescences":"2",
                    "Abundance":"3"})
            for z in (heights if i<=7 or i==10 else heights[:2]):
                nectar.append({"ML_ID":str(i),"Stratum":z,
                               "Year":"2018","Nect_quant_mean":"1.5"})
        self.assertEqual(len(nectar),28)
        self.assertEqual(len(cam),26)
        for i in range(11,30):
            cam.append({"ML_ID":f"ML{i:02}","Taxa":"Bat",
                "Stratum":"Low","Hours":"24","Inflorescences":"2",
                "Abundance":"0"})
        for i in range(135):
            cam.append({"ML_ID":"ML01","Taxa":"Bird",
                        "Stratum":"Middle","Hours":"24",
                        "Inflorescences":"2","Abundance":"0"})
        for i in range(12):
            nectar.append({"ML_ID":"1","Stratum":"Low","Year":"2019",
                           "Nect_quant_mean":"1.5"})
        self.assertEqual(len(cam),180)
        self.assertEqual(len(nectar),40)
        profiles=a.get_qualified_original_plant_profiles(cam,nectar)
        self.assertEqual(len(profiles),9)
        self.assertEqual(sum(len(p.layers) for p in profiles),25)
        self.assertEqual({len(p.layers) for p in profiles},{2,3})
        self.assertNotIn("10",{p.identity for p in profiles})

    def test_original_adapter_validates_counts_without_rounding(self):
        self.assertEqual(a.parse_integer("0"),0)
        self.assertEqual(a.parse_integer("12.0"),12)
        with self.assertRaisesRegex(ValueError,"SOURCE_RESPONSE_STOP"):
            a.parse_integer("2.4")
        with self.assertRaisesRegex(ValueError,"SOURCE_RESPONSE_STOP"):
            a.parse_integer("NA")
        with self.assertRaisesRegex(ValueError,"SOURCE_RESPONSE_STOP"):
            a.parse_resource("nan")
        self.assertEqual(a.parse_resource("0"),0.0)

if __name__=="__main__":
    unittest.main()
