"""Exact source-free detector-bias sensitivity and effort OR mathematical tests."""
import json
import math
from pathlib import Path
import numpy as np
import pytest
from odsp.uljin_detector_bias_robust_or_v0 import (
    FourCells,BS,TABLES,CALIBRATIONS,central_logweights,
    conditional_nchypergeom,upper_tail,exact_lower_bound_count_OR,
    detector_gamma_interval,evaluate_frozen_detector_sensitivity,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_DETECTOR_BIAS_ROBUST_OR_V0_CONTRACT.json").read_text())


def test_small_exact_hypergeometric_by_independent_binomial_enumeration():
    t=FourCells((1,1,1,1),(4.,4.,4.,4.))
    lo,p=conditional_nchypergeom(t,1.)
    assert lo==0 and p==pytest.approx(np.array([1.,4.,1.])/6.)
    lo,p2=conditional_nchypergeom(t,2.)
    assert p2==pytest.approx(np.array([1.,8.,4.])/13.)
    assert upper_tail(t,1.)==pytest.approx(5./6.)
    assert t.effort_OR==1
    assert t.observed_count_OR==1


def test_exact_lower_limit_is_tail_inversion_and_effort_exposure_matters():
    for name,counts,hours in TABLES:
        t=FourCells(counts,hours)
        lower=exact_lower_bound_count_OR(t)
        assert lower>=0 and math.isfinite(lower)
        assert upper_tail(t,lower)==pytest.approx(.05,abs=1e-10)
    unequal=FourCells((40,40,80,40),(4.,4.,8.,4.))
    assert unequal.observed_count_OR==2.
    assert unequal.effort_OR==2.
    assert unequal.observed_effort_adjusted_OR==1.
    assert exact_lower_bound_count_OR(unequal)/unequal.effort_OR<1.


def test_joint_detector_q_interval_product_bound_and_unbounded_without_calibration():
    lo,hi=detector_gamma_interval((.9,)*4,(1.,)*4)
    assert lo==pytest.approx(.81)
    assert hi==pytest.approx(1/.81)
    # Independently calibrated q must have joint simultaneous coverage.
    lo2,hi2=detector_gamma_interval(
        (.8,.8,.85,.75),(.95,.95,.98,.9))
    assert lo2==pytest.approx((.85*.8)/(.95*.9))
    assert hi2==pytest.approx((.98*.95)/(.8*.75))
    # Construct a valid q in (0,1] producing any finite positive seasonal
    # detector crossproduct, so without external evidence latent OR is
    # arbitrarily close to 0 even if observed OR is large.
    for gamma in (.1,.5,1.,2.,10.,100.):
        q=(1.,1.,gamma,1.) if gamma<=1 else (1.,1.,1.,1./gamma)
        actual=q[2]*q[1]/(q[0]*q[3])
        assert actual==pytest.approx(gamma)
        assert all(0<e<=1 for e in q)
    with pytest.raises(ValueError):
        detector_gamma_interval((0.,.9,.9,.9),(1.,1.,1.,1.))
    with pytest.raises(ValueError):
        detector_gamma_interval((.95,.9,.9,.9),(.9,1.,1.,1.))


def test_all_5x5_robust_sensitivity_with_monotone_p_and_lower_bound():
    result=evaluate_frozen_detector_sensitivity(PLAN)
    assert result["status"]=="SOURCE_FREE_EXACT_DETECTION_BIAS_SENSITIVITY_NOT_ECOLOGICAL_INFERENCE"
    assert len(result["all_five_precommitted_tables"])==5
    assert result["uncalibrated_detection_crossproduct_unbounded"]
    assert result["all_calibration_B_values"]==list(BS)
    for x in result["all_five_precommitted_tables"]:
        rows=x["detector_cap_sensitivity_grid"]
        assert len(rows)==5
        assert len(x["two_hypothetical_joint_calibration_cases"])==2
        assert [a["robust_one_sided_exact_p_for_latent_OR_le_1"] for a in rows]==sorted(
            a["robust_one_sided_exact_p_for_latent_OR_le_1"] for a in rows)
        lowers=[a["one_sided_95pct_lower_latent_encounter_OR"] for a in rows]
        assert lowers==sorted(lowers,reverse=True)
        assert all(0<=row["robust_one_sided_exact_p_for_latent_OR_le_1"]<=1 for row in rows)
        assert x["uncalibrated_detector_sensitivity_real_ecological_conclusion"]=="HOLD"
    effort=next(x for x in result["all_five_precommitted_tables"]
                if x["synthetic_table_id"]=="unequal_effort_only")
    assert effort["raw_observed_count_OR"]==2
    assert effort["effort_adjusted_observed_rate_OR"]==1
    strong=next(x for x in result["all_five_precommitted_tables"]
                if x["synthetic_table_id"]=="strong_shift")
    assert strong["effort_adjusted_observed_rate_OR"]==pytest.approx(280/120)
    assert strong["detector_cap_sensitivity_grid"][0][
        "one_sided_95pct_lower_latent_encounter_OR"]>1
    assert not result["true_ungulate_behavior_or_photo_trigger_efficiency_estimated"]
    assert not result["source_original_ecobank_event_rows_opened"]
    json.dumps(result,allow_nan=False)


def test_negative_control_and_source_independent_contract_fail_closed():
    altered=json.loads(json.dumps(PLAN))
    altered["detector_crossproduct_max_B"][1]=1.4
    with pytest.raises(ValueError,match="contract"):
        evaluate_frozen_detector_sensitivity(altered)
    altered=json.loads(json.dumps(PLAN))
    altered["source_state"]["ecobank_v1p1_archive_verified"]=True
    with pytest.raises(ValueError,match="contract"):
        evaluate_frozen_detector_sensitivity(altered)
    with pytest.raises(ValueError):
        FourCells((1,-1,1,1),(4.,4.,4.,4.))
    with pytest.raises(ValueError):
        FourCells((1,1,1,1),(4.,0.,4.,4.))
    with pytest.raises(ValueError):
        conditional_nchypergeom(FourCells((1,1,1,1),(4.,)*4),-1.)
