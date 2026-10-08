"""Source-free tests: multi-site exact 2-bin Fisher conditioning and Simpson guard."""
import json
from pathlib import Path
import numpy as np
import pytest

from odsp.uljin_stratified_exact_conditional_power_v0 import (
    FixedSiteMargins, central_site_hypergeom, stratified_null_convolution,
    common_OR_tilt,exact_upper_tail_threshold,rejection_prob,
    sites_for_design,pooled_margins,witness_composition,
    run_stratified_exact_panel,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_STRATIFIED_EXACT_CONDITIONAL_POWER_V0_CONTRACT.json").read_text())


def test_n2_balanced_one_site_and_two_site_exact_null_by_enumeration():
    m=FixedSiteMargins(4,2,2)
    offset,p=central_site_hypergeom(m)
    assert offset==0
    assert p==pytest.approx([1/6,4/6,1/6],abs=1e-12)
    start,dist=stratified_null_convolution([m,m])
    assert start==0
    assert dist==pytest.approx([1/36,8/36,18/36,8/36,1/36],abs=1e-12)
    assert np.isclose(dist.sum(),1.)


def test_stratified_null_site_specific_support_and_common_OR_ordering():
    sites=sites_for_design("composition_confounded_alternating",2)
    assert len(sites)==2
    lo,p=stratified_null_convolution(sites)
    assert lo==sites[0].bounds[0]+sites[1].bounds[0]
    assert np.isclose(p.sum(),1.)
    null=common_OR_tilt(lo,p,1.)
    assert np.array_equal(p,null)
    bigger=common_OR_tilt(lo,p,3.)
    assert np.isclose(bigger.sum(),1.)
    assert (lo+np.arange(len(p)))@bigger > (lo+np.arange(len(p)))@p
    c,size=exact_upper_tail_threshold(lo,p)
    assert 0<=size<=.05+1e-12
    assert rejection_prob(lo,bigger,c)>=size


def test_fixed_simpson_witness_within_site_OR_one_but_pooled_rejects():
    witness=witness_composition()
    assert witness["within_site_observed_OR"]==[1.,1.]
    assert witness["naively_pooled_observed_OR"]>5.
    assert witness["stratified_null_conditional_expectation"]==pytest.approx(56.)
    assert witness["observed_total_falling_early"]==56
    assert witness["stratified_exact_one_sided_p"]>.05
    assert witness["naive_pooled_one_sided_fisher_p"]<.05
    assert witness["fixed_total_event_count"]==160


def test_full_exact_precommitted_case_matrix_and_all_null_sizes():
    result=run_stratified_exact_panel(PLAN)
    assert result["case_count"]==12
    assert result["truth_effect_rows"]==48
    assert result["site_stratified_conditional_null_size_valid_all_cases"]
    assert result["all_probabilities_analytic_no_simulation"]
    assert result["max_naive_pooled_null_rejection_in_compositional_stress"]>.05
    assert not result["not_site_sampling_superpopulation_or_full_six_bin_power"] is False
    for case in result["case_results"]:
        assert 0<=case["stratified_exact_null_rejection_probability"]<=.05+1e-12
        vals=[r["stratified_exact_conditional_rejection_probability"]
              for r in case["by_common_true_OR"]]
        assert vals==sorted(vals)
        assert len(vals)==4
        assert vals[0]==pytest.approx(
            case["stratified_exact_null_rejection_probability"],abs=1e-12)
        assert all(0<=r["pooled_naive_conditional_rejection_probability"]<=1
                   for r in case["by_common_true_OR"])
    assert result["no_real_source_animal_or_camera_operation_data_accessed"]
    json.dumps(result,allow_nan=False)


def test_invalid_input_and_precommitted_contract_mutations_fail():
    with pytest.raises(ValueError):
        FixedSiteMargins(4,5,2)
    with pytest.raises(ValueError):
        stratified_null_convolution([])
    with pytest.raises(ValueError):
        common_OR_tilt(0,np.array([.5,.5]),0.)
    with pytest.raises(ValueError):
        sites_for_design("new_after_result",2)
    altered=json.loads(json.dumps(PLAN))
    altered["stratum_templates"][2]["sites"][0]["D"]=55
    with pytest.raises(ValueError,match="contract"):
        run_stratified_exact_panel(altered)
