"""Guard frozen four-source Wstar family and nonconfirmation contract."""
from prospective.run_gyps_shared_species_vs_bird_wstar import (
    PRIOR_RESULTS, family_holm
)


def test_new_analysis_retains_original_four_source_categories():
    assert PRIOR_RESULTS == {
       "122120597/Gyps fulvus":"supported_50km_thermal_height_shape",
       "352166254/Gyps africanus":"unavailable",
       "44080734/Gyps fulvus":"supported_50km_thermal_height_shape",
       "972560688/Gyps coprotheres":"not_supported_50km_thermal_height_shape"
    }


def test_holm_uses_original_family_members_including_unavailable():
    rows={
       "a":{"terminal":"exploratory_tested","calibration":{"p_upper":0.001}},
       "b":{"terminal":"unavailable","calibration":{"p_upper":0.02}},
       "c":{"terminal":"exploratory_tested","calibration":{"p_upper":0.025}},
       "d":{"terminal":"exploratory_tested","calibration":{"p_upper":0.08}}
    }
    family_holm(rows)
    assert rows["a"]["exploratory_holm_p_upper"]==0.004
    assert rows["b"]["holm_family_input_p"]==1
    assert rows["b"]["exploratory_holm_p_upper"]==1
    assert abs(rows["c"]["exploratory_holm_p_upper"]-0.075)<1e-12
    assert abs(rows["d"]["exploratory_holm_p_upper"]-0.16)<1e-12


def test_no_favoring_original_two_supported_studies_at_stage_one():
    assert len(PRIOR_RESULTS)==4
    assert len({i.rsplit("/",1)[-1] for i in PRIOR_RESULTS})==3
