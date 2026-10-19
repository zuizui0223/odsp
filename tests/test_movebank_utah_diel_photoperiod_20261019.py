import unittest,json
from scripts.movebank_utah_diel_photoperiod_20261019 import slope,boot,one_taxon,compare_sites,CONTRACT
class Tests(unittest.TestCase):
    def test_old_unsupported_endpoint_not_reclassified(self):
        a=json.loads(CONTRACT.read_text())
        self.assertEqual(a["version"],"utah-diel-photoperiod-description-v0")
        self.assertIn("not a rescue",a["reason"].lower())
    def test_known_daylight_gradient(self):
        x=[(10+i*.1,1+2*(10+i*.1)) for i in range(12)]
        self.assertAlmostEqual(slope(x),2)
    def test_daylight_slope_needs_temporal_span(self):
        self.assertIsNone(slope([(11+i*.01,i) for i in range(12)]))
    def test_bootstrap_requires_animals(self):
        self.assertIsNone(boot([1,2,3]))
        self.assertEqual(boot([0]*5),[0,0])
    def test_unsupported_taxon_remains(self):
        result,cells=one_taxon("test",{})
        self.assertIsNone(result["day_night_speed_contrast"])
        self.assertIsNone(result["daylength_association"])
        self.assertEqual(len(cells),0)
    def test_no_common_month_is_not_effect(self):
        q=compare_sites({"a":{(40,-110,2019,6):1},"b":{}})
        self.assertEqual(len(q),1)
        self.assertEqual(q[0]["status"],"unsupported")
if __name__=="__main__":unittest.main()
