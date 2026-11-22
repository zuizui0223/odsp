"""Known-truth checks for observation-aware species×height identifiability.

No field response is read. The constructed Poisson aggregate surveys are unlinked.
"""
import math

import numpy as np
import pytest

from odsp.vertical_species_identification import (
    conditional_species_height_information,
    observed_poisson_means,
    two_world_witness,
)

def test_same_geographic_and_observed_worlds_different_ecological_information():
    result=two_world_witness()
    a=result["true_world_A_I_species_height_given_site"]["information_nats"]
    b=result["true_world_B_I_species_height_given_site"]["information_nats"]
    y=result["naive_detected_method1_I_species_height_given_site"]["information_nats"]
    expected=math.log(2) + .9*math.log(.9) + .1*math.log(.1)
    assert a == pytest.approx(expected,abs=1e-12)
    assert a/math.log(2) == pytest.approx(0.5310044064,abs=1e-9)
    assert b == pytest.approx(0.0,abs=1e-12)
    assert y == pytest.approx(a,abs=1e-12)
    assert result["biological_horizontal_intensity_same"]
    assert result["unlinked_observed_method_poisson_likelihood_same"]
    assert result["observed_method_means_both_worlds_mxsz"] == [
        [[[9.,1.],[1.,9.]]], [[[4.5,.5],[.5,4.5]]]
    ]

def test_original_projection_overlap_can_be_fully_misleading():
    r=two_world_witness()
    assert r["horizontal_schoener_overlap_both_worlds"] == pytest.approx(1)
    assert r["full_schoener_overlap_world_A"] == pytest.approx(.2)
    assert r["full_schoener_overlap_world_B"] == pytest.approx(1)
    assert r["projected_overlap_inflation_world_A"] == pytest.approx(.8)
    assert r["projected_overlap_inflation_world_B"] == pytest.approx(0)

def test_calibrated_q_recovers_original_latent_world():
    r=two_world_witness()
    obs=np.asarray(r["observed_method_means_both_worlds_mxsz"])
    for letter in "AB":
        latent=np.asarray(r[f"latent_intensity_world_{letter}_xsz"])
        detection=np.asarray(r[f"detection_world_{letter}_mxsz"])
        np.testing.assert_allclose(obs / detection, np.broadcast_to(latent,obs.shape))

def test_declared_site_weights_alter_target_and_not_missingness():
    a=np.array([[[90.,10.],[10.,90.]],
                [[50.,50.],[50.,50.]]])
    equal=conditional_species_height_information(a,site_weights=np.array([1.,1.]))
    weighted=conditional_species_height_information(a,site_weights=np.array([1.,3.]))
    assert weighted["information_nats"] == pytest.approx(equal["information_nats"]/2)
    assert equal["site_weights"] == pytest.approx([.5,.5])
    assert weighted["site_weights"] == pytest.approx([.25,.75])

def test_empty_site_cannot_receive_positive_weight():
    a=np.array([[[2.,1.],[1.,2.]],[[0.,0.],[0.,0.]]])
    with pytest.raises(ValueError,match="without support"):
        conditional_species_height_information(a,site_weights=np.array([1.,1.]))
    score=conditional_species_height_information(a,site_weights=np.array([1.,0.]))
    assert score["per_site_information_nats"][1] is None

def test_dop_like_probs_cannot_exceed_one_and_shape_fails_closed():
    x=np.ones((1,2,2))
    bad=np.ones((2,1,2,2))
    bad[0,0,0,0]=1.5
    with pytest.raises(ValueError,match="probabilities"):
        observed_poisson_means(x,bad)
    with pytest.raises(ValueError,match="expected"):
        observed_poisson_means(x,np.ones((1,2,2)))
