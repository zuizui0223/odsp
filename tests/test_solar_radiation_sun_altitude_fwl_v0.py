"""Known truth: distinguish sun-altitude geometry from irradiation-weather response."""
from datetime import date,datetime
import math
import unittest
from scripts.solar_radiation_sun_geometry_fwl_v0 import (
    conditional_shortwave_slope_one_animal
)
from scripts.run_solar_altitude_conditioned_48_original_studies_v0 import (
    fixed_original_study_roster
)


def artificial_animal(true_sw=0.0,geometry=0.3,collinear=False):
    """All data are known-truth synthetic, NOT actual wildlife evidence."""
    rows=[]
    for month in (4,5,6):
        for day in range(1,7):
            for hour in (9,10,11,12):
                s=.5+.02*(hour-10)+.013*(day-3)+.012*(month-5)
                sunel=math.degrees(math.asin(s))
                residual=75*(((-1)**(hour+day))+0.4*(day%3-1))
                SW=360+1250*(s-.5)+22*(hour-10)
                if not collinear:
                    SW+=residual
                sunaz=150
                y=true_sw*(SW-360)+geometry*(s-.5)+.015*(hour-10)
                if not -.98<y<.98:
                    raise ValueError("Synthetic response cannot be transformed to cosine")
                heading=sunaz+math.degrees(math.acos(y))
                utc=datetime(2018,month,day,hour)
                rows.append((utc,date(2018,month,day),hour+.25,heading,
                             sunaz,sunel,SW))
    return rows


class SunAltTimeRadiationSeparation(unittest.TestCase):

    def test_all_original_48_study_ids_retained_with_20_identified(self):
        selected,held=fixed_original_study_roster()
        self.assertEqual(len(selected),20)
        self.assertEqual(len(held),28)
        self.assertEqual(len({x[0]["source_uuid"] for x in selected}),20)
        self.assertEqual(sum(x[0]["cohort"]=="earlier" for x in selected),10)
        self.assertEqual(sum(x[0]["cohort"]=="external" for x in selected),10)
        self.assertTrue(all(x[0]["native_eligible_taxa"] for x in selected))

    def test_geometry_alone_no_false_independent_shortwave_effect(self):
        v=conditional_shortwave_slope_one_animal(
            artificial_animal(true_sw=0,geometry=.7))
        self.assertEqual(v["status"],"GEOMETRY_ADJUSTED_SOURCE_ANIMAL_ESTIMABLE")
        self.assertGreater(abs(v["unadjusted_same_step_slope"]),.0001)
        self.assertAlmostEqual(v["solar_geometry_conditional_slope"],0,delta=1e-7)

    def test_true_source_radiation_effect_survives_altitude_and_clock(self):
        v=conditional_shortwave_slope_one_animal(
            artificial_animal(true_sw=.0007,geometry=.3))
        self.assertEqual(v["status"],"GEOMETRY_ADJUSTED_SOURCE_ANIMAL_ESTIMABLE")
        self.assertAlmostEqual(v["solar_geometry_conditional_slope"],.07,delta=1e-7)
        self.assertGreater(v["fraction_shortwave_variance_after_solar_geometry"],.10)
        self.assertGreater(v["residual_shortwave_SD_Wm2"],30)

    def test_no_shortwave_residual_is_unidentifiable_not_zero(self):
        v=conditional_shortwave_slope_one_animal(
            artificial_animal(true_sw=0,geometry=.7,collinear=True))
        self.assertIn(v["status"],("INSUFFICIENT_SUN_INDEPENDENT_SHORTWAVE",
                                  "SUN_GEOMETRY_MULTICOLLINEAR"))
        self.assertIsNone(v["solar_geometry_conditional_slope"])

    def test_one_time_block_cannot_become_source_solar_geometry_result(self):
        rows=[r for r in artificial_animal(true_sw=.0002) if r[0].month==4]
        v=conditional_shortwave_slope_one_animal(rows)
        self.assertIn(v["status"],("INSUFFICIENT_ORIGINAL_BLOCKS",
                                  "INSUFFICIENT_SUN_INDEPENDENT_SHORTWAVE"))
        self.assertIsNone(v["solar_geometry_conditional_slope"])


if __name__=="__main__":
    unittest.main()
