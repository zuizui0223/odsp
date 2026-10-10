"""Exact source-free tolerance to unmeasured target near/far passage fractions."""
from pathlib import Path
import json
import math
import numpy as np
import pytest

pytest.importorskip("scipy",reason="Optional calibrated q inference benchmark")
from odsp.uljin_distance_mix_tipping_radius_v0 import (
    DELTAS,NS,NEAR,FAR,OBSERVATIONS,oracle_B_formula,source_q_bounds,
    q_envelope,result_at_delta,certified_delta_supremum,
    run_frozen_distance_radius,
)
from odsp.uljin_detector_bias_robust_or_v0 import (
    FourCells,exact_lower_bound_count_OR
)
from odsp.uljin_q_transport_distance_mix_v0 import q_effective,detector_crossproduct

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_DISTANCE_MIX_TIPPING_RADIUS_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_IID_REFERENCE_Q_TRANSPORT_V1_FIRST_RESULT_LEDGER.json").read_text())


def test_closed_form_oracle_detector_q_and_parent_counterexample():
    oracle=source_q_bounds("oracle",None)
    for d in DELTAS:
        lower,upper=q_envelope(d,oracle)
        assert lower==pytest.approx([.6-.6*d]*4)
        assert upper==pytest.approx([.6+.6*d]*4)
        assert upper[2]*upper[1]/(lower[0]*lower[3])==pytest.approx(
            oracle_B_formula(d),rel=1e-12)
    true_q=q_effective(NEAR,FAR,(.2,.8,.8,.2))
    assert true_q==pytest.approx([.42,.78,.78,.42])
    assert detector_crossproduct(true_q)==pytest.approx(oracle_B_formula(.3))
    assert oracle_B_formula(.0)==1
    assert oracle_B_formula(.3)>3.44


def test_robust_exact_fisher_one_sided_tipping_point_agrees_with_analytic_formula():
    t=FourCells((200,200,280,120),(4.,4.,4.,4.))
    lower=exact_lower_bound_count_OR(t,alpha=.025)
    oracle=source_q_bounds("oracle",None)
    dcrit=certified_delta_supremum(t,lower,oracle)
    direct=(math.sqrt(lower)-1)/(math.sqrt(lower)+1)
    assert dcrit==pytest.approx(direct,abs=1e-9)
    assert .1<dcrit<.2
    assert result_at_delta(t,lower,.05,oracle)[
        "certifies_positive_with_both_calibration_and_count_alpha"]
    assert not result_at_delta(t,lower,.2,oracle)[
        "certifies_positive_with_both_calibration_and_count_alpha"]


def test_CP_detector_uncertainty_never_looks_artificially_tighter_than_true_q():
    for n in NS:
        q=source_q_bounds("exact_CP",n)
        assert all(v.shape==(4,) for v in q)
        assert np.all(q[0]<=np.asarray(NEAR)) and np.all(q[1]>=np.asarray(NEAR))
        assert np.all(q[2]<=np.asarray(FAR)) and np.all(q[3]>=np.asarray(FAR))
        for delta in DELTAS:
            lo,hi=q_envelope(delta,q)
            o_lo,o_hi=q_envelope(delta,source_q_bounds("oracle",None))
            assert np.all(lo<=o_lo+1e-12)
            assert np.all(hi>=o_hi-1e-12)
    with pytest.raises(ValueError):
        source_q_bounds("oracle",50)
    with pytest.raises(ValueError):
        source_q_bounds("exact_CP",17)
    with pytest.raises(ValueError):
        q_envelope(-.1,source_q_bounds("oracle",None))


def test_whole_frozen_5x5x6_radius_matrix_and_no_field_claims():
    r=run_frozen_distance_radius(PLAN,PARENT)
    assert r["status"]=="SOURCE_FREE_DISTANCE_MIX_PARTIAL_IDENTIFICATION_RADIUS"
    assert r["total_predeclared_delta_x_calibration_x_table_scores"]==150
    assert len(r["all_5_original_observation_tables"])==5
    assert r["requires_externally_valid_deterministic_delta_bound"]
    assert r["statistically_estimated_delta_would_require_extra_error_budget"]
    assert r["no_real_wildlife_or_camera_calibration_records_read"]
    assert r["no_actual_distance_distribution_bound_known"]
    assert r["distance_mix_30pct_radius_parent_confounded_detector_OR"]==pytest.approx(
        (0.78/.42)**2)
    for table in r["all_5_original_observation_tables"]:
        variants=table["source_q_uncertainty_sensitivity"]
        assert len(variants)==5
        for v in variants:
            d=v["all_predeclared_radius_results"]
            assert [x["target_near_mix_half_width_delta"] for x in d]==list(DELTAS)
            lowers=[x["one_sided_97p5pct_lower_latent_encounter_OR"] for x in d]
            assert lowers==sorted(lowers,reverse=True)
            p=[x["robust_exact_one_sided_p_under_latent_OR_le_1"] for x in d]
            assert p==sorted(p)
    negative=next(x for x in r["all_5_original_observation_tables"]
                  if x["hypothetical_observed_table"]=="unequal_effort_algebra_only")
    assert negative["device_hour_effort_OR"]==2.
    assert negative["raw_observed_count_OR"]==2.
    assert negative["oracle_target_mix_tipping_delta_analytic_or_null"] is None
    json.dumps(r,allow_nan=False)


def test_pr252_first_ledger_immutable_and_freeze_gate():
    mutated=json.loads(json.dumps(PLAN))
    mutated["delta_grid"]=[0,.05,.1,.20,.3]
    with pytest.raises(ValueError,match="frozen"):
        run_frozen_distance_radius(mutated,PARENT)
    mutated=json.loads(json.dumps(PARENT))
    mutated["first_full_ci_run"]=12345
    with pytest.raises(ValueError,match="frozen"):
        run_frozen_distance_radius(PLAN,mutated)
