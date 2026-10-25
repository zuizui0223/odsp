"""Source-ID rather than GPS-fix weighting for original GPS meteorology ecology."""
from copy import deepcopy
import math
import unittest
from scripts.analyze_solar_azimuth_24_source_weather_study_blocks_v0 import (
    _study_mean,_average_tie_ranks,spearman,study_mean_summary,
    source_block_spearman,analyze_combined,study_bootstrap_mean
)
from scripts.run_solar_azimuth_24_source_population_weather_v0 import check_24_original_source_contract


def observation(sun=.2,temp=15,slope=.04):
    response={
        "sunward_cos":{"mean":sun},
        "windflow_cos":{"mean":-.1},
        "wind_sun_cos":{"mean":.1},
        "wind_speed_100m_ms":{"mean":5.0},
        "shortwave_Wm2":{"mean":400.0},
        "temperature_2m_C":{"mean":temp}
    }
    slopes={k:{"mean":slope} for k in
            ("wind_sun_cos","windspeed_ms","shortwave_Wm2","temperature_C")}
    return {
        "weather_environmental_effect_status":"SOURCE_GROUP_OBSERVED_ENVIRONMENT_DESCRIPTION",
        "environmental_group_means":response,
        "within_animal_clock_month_weather_associations":slopes,
    }


def study(uuid,studyid,taxa):
    return {
        "source_package_uuid":uuid,"source_study_ids":[studyid],
        "original_source_status":"ORIGINAL_GPS_REPLAYED_WEATHER_SCREENED",
        "source_original_replay_success":True,
        "source_climate_request_count":1,
        "source_taxa":taxa
    }


def taxon(name,contexts):
    return {"taxon":name,"source_gridyear_weather_contexts":contexts}


class WeatherMacroStudyBlocks(unittest.TestCase):

    def test_one_equal_taxon_then_equal_original_study_weight(self):
        one=study("source1","sid1",[
            taxon("A",[observation(sun=.1,slope=.1),
                       observation(sun=.3,slope=.3)]),
            taxon("B",[observation(sun=.8,slope=.8)])
        ])
        r=_study_mean(one)
        self.assertAlmostEqual(r["source_study_equal_taxon_context_means"]["sunward_cos"],.5)
        self.assertAlmostEqual(r["source_study_equal_taxon_context_means"]["slope_windspeed_ms"],.5)
        self.assertEqual(r["source_modal_gridyears_observed"],3)

    def test_source_missing_weather_is_not_ecological_zero(self):
        s=study("S","sid",[taxon("A",[{
            "weather_environmental_effect_status":"SOURCE_WEATHER_HOLD"}])])
        r=_study_mean(s)
        self.assertIsNone(r["source_study_equal_taxon_context_means"]["sunward_cos"])
        self.assertIsNone(r["source_study_equal_taxon_context_means"]["slope_shortwave_Wm2"])

    def test_average_tie_spearman_and_source_bootstrap(self):
        self.assertEqual(_average_tie_ranks([1,1,3]),[1.5,1.5,3])
        self.assertAlmostEqual(spearman([1,2,3,4],[10,20,30,40]),1)
        self.assertAlmostEqual(spearman([1,2,3,4],[40,30,20,10]),-1)
        self.assertIsNone(study_bootstrap_mean([1,2,3,4,5]))
        self.assertEqual(study_bootstrap_mean([.1]*6),[.1,.1])

    def test_context_correlation_descriptive_source_block_only(self):
        sources=[]
        for i in range(10):
            x=_study_mean(study("src"+str(i),"ID"+str(i),[
                taxon("A",[observation(sun=i/50,temp=5+i)])
            ]))
            sources.append(x)
        result=source_block_spearman(sources,"temperature_2m_C")
        self.assertEqual(result["n_original_source_archives_with_both_weather_and_solar"],10)
        self.assertAlmostEqual(result["Spearman_source_level_rho"],1)

    def test_full_24_source_roster_and_hold_retained(self):
        _,manifest,_=check_24_original_source_contract()
        sources=[]
        for i,p in enumerate(manifest):
            outcome=[observation(sun=i/100,temp=i+1,slope=.01*(i%3-1))] if i<12 else [{
                "weather_environmental_effect_status":"SOURCE_WEATHER_HOLD"}]
            sources.append(study(p["package_uuid"],p["source_study_ids"][0],
                                 [taxon(p["original_species_labels"][0],outcome)]))
        r=analyze_combined({"version":"original-gps-solar-population-weather-v0",
                            "source_groups":sources})
        self.assertEqual(r["complete_fixed_source_archive_denominator"],24)
        self.assertEqual(r["source_archives_with_at_least_one_environmental_group"],12)
        self.assertEqual(r["study_equal_univariate_within_tagged_animal_climate_slopes"]
                         ["shortwave_Wm2"]["study_ID_source_archives_with_identifiable_effect"],12)
        self.assertEqual(len(r["all_24_source_level_descriptions"]),24)
        self.assertEqual(r["study_equal_meteorological_context_correlations"]
                         ["temperature_2m_C"]["n_original_source_archives_with_both_weather_and_solar"],12)


if __name__=="__main__":
    unittest.main()
