"""Finite q-reference joint coverage + externally attested daily drift sensitivity."""
import json
from pathlib import Path
import numpy as np
import pytest

pytest.importorskip("scipy",reason="optional independent CP detector reference calibration")
from odsp.uljin_within_branch_daily_q_drift_v0 import (
    AMPLITUDES,EPS,EXPECTED_PAIRS,
    true_daily_q,external_qday_bounds,sitewise_outer_daily_score,
    first_frozen_daily_drift_panel,
)
from odsp.uljin_station_season_camera_q_v0 import (
    physical_site_q,calibrate_site_q
)
from odsp.uljin_common_clock_mechanistic_comparison_v0 import original_days

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_WITHIN_BRANCH_DAILY_Q_DRIFT_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_STATION_SEASON_CAMERA_Q_V0_FIRST_RESULT_LEDGER.json").read_text())
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def test_daily_q_varies_WITHIN_branch_yet_reference_mean_is_correct():
    dates,branch=original_days(CAL)
    labels,qbar=physical_site_q(1)
    assert len(dates)==82 and np.array_equal(branch,np.tile([0,1],41))
    stable=true_daily_q(branch,qbar,labels,0.)
    varying=true_daily_q(branch,qbar,labels,.35)
    assert stable.shape==varying.shape==(32,82,6)
    assert np.allclose(stable,qbar[:,branch,:])
    assert np.max(np.abs(varying-stable))>.04
    assert np.all((varying>0)&(varying<1))
    for b in (0,1):
        assert np.allclose(varying[:,branch==b,:].mean(axis=1),
                           qbar[:,b,:],atol=1e-12)
    relative=np.abs(varying/stable-1)
    assert float(relative.max())<=.35+1e-12


def test_true_daily_detector_q_has_valid_mean_cp_coverage_only_if_drift_bound_attested():
    _,branch=original_days(CAL)
    labels,qbar=physical_site_q(1)
    actual=true_daily_q(branch,qbar,labels,.35)[16:]
    for budget in range(2):
        source=calibrate_site_q(1,budget,1,qbar)
        assert source["q_source_groups"]==192
        assert source["total_true_passage_reference_opportunities"] in (38400,153600)
        for eps in EPS:
            lower,upper=external_qday_bounds(source,branch,eps)
            assert lower.shape==upper.shape==(16,82,6)
            assert np.all(lower<=upper)
            if eps>=.35 and source["station_by_branch_target_CP_joint_coverage_ORACLE_ONLY"]:
                assert np.all(lower<=actual+1e-12)
                assert np.all(upper>=actual-1e-12)
    with pytest.raises(ValueError):
        external_qday_bounds(calibrate_site_q(1,0,1,qbar),branch,.21)


def test_no_peeking_at_oracle_true_q_confidence_coverage_and_unattested_epsilon_hold():
    _,branch=original_days(CAL)
    labels,qbar=physical_site_q(1)
    actual=true_daily_q(branch,qbar,labels,.35)[16:]
    a=np.full((82,96),1/96.)
    b=a.copy()
    a[:,5]*=4
    a/=a.sum(axis=1,keepdims=True)
    counts=np.zeros((16,82,96),dtype=int)
    counts[:,:,5]=20
    ref=calibrate_site_q(1,1,1,qbar)
    missing=sitewise_outer_daily_score(counts,a,b,actual,ref,branch,.1,.35)
    assert missing["scope"]=="HOLD_EXTERNAL_DAILY_DRIFT_CAP_NOT_ATTESTED"
    assert missing["new_site_majority_certified"] is None
    permitted=sitewise_outer_daily_score(counts,a,b,actual,ref,branch,.35,.35)
    assert permitted["scope"]=="EXTERNAL_DAILY_DRIFT_BOUND_ASSUMED_VALID_SOURCE_FREE"
    assert permitted["oracle_coverage_not_used_to_admit_or_reject"]
    changed={**ref,
        "source_CP_joint_coverage_ORACLE_ONLY":False,
        "station_by_branch_target_CP_joint_coverage_ORACLE_ONLY":False}
    # Both data-dependent inferential labels must be identical regardless
    # of whether the simulator knows the calibration true q was covered.
    no_oracle=sitewise_outer_daily_score(counts,a,b,actual,changed,branch,.35,.35)
    assert no_oracle["new_site_majority_certified"]==permitted["new_site_majority_certified"]
    assert no_oracle["independent_physical_sites_robust_positive"]==permitted[
        "independent_physical_sites_robust_positive"]
    assert no_oracle["exact_site_sign_p"]==permitted["exact_site_sign_p"]


def test_full_frozen_384_case_96civil_site_drift_and_PR260_first_result_replay():
    result=first_frozen_daily_drift_panel(PLAN,PARENT,CAL)
    assert result["status"]=="SOURCE_FREE_DAILY_DETECTOR_Q_DRIFT_OUTER_SITE_MAJORITY"
    assert result["total_frozen_case_x_eps"]==EXPECTED_PAIRS==384
    assert len(result["all_first_96_model_comparisons_by_four_eps"])==96
    assert len(result["all_source_reference_qmean_audits"])==4
    assert result["pr260_original_station_branch_eps0_positive_count_replayed"]==13
    assert result["total_per_attested_design_false_majority_alpha_bound"]==.05
    assert result["original_astronomy_pairs"]==41
    assert result["original_96_civil_clock_quarterhour_bins"]==96
    assert result["independent_heldout_physical_sites"]==16
    assert result["oracle_q_coverage_only_a_result_audit_not_a_gate"]
    assert result["no_real_original_NIE_EcoBank_animal_events_camera_uptime_q_references"]
    for row in result["all_first_96_model_comparisons_by_four_eps"]:
        assert set(row["all_four_precommitted_eps_results"])=={"0.0","0.1","0.2","0.35"}
        amp=row["daily_q_generator_amplitude"]
        prior=17
        for eps in EPS:
            r=row["all_four_precommitted_eps_results"][str(eps)]
            assert r["oracle_coverage_not_used_to_admit_or_reject"]
            if eps<amp:
                assert r["scope"]=="HOLD_EXTERNAL_DAILY_DRIFT_CAP_NOT_ATTESTED"
                assert r["new_site_majority_certified"] is None
            else:
                assert r["scope"]=="EXTERNAL_DAILY_DRIFT_BOUND_ASSUMED_VALID_SOURCE_FREE"
                assert r["independent_physical_sites_robust_positive"]<=prior
                prior=r["independent_physical_sites_robust_positive"]
                assert r["independent_physical_sites_robust_positive"] in range(17)
                if r["new_site_majority_certified"]:
                    assert prior>=14
    json.dumps(result,allow_nan=False)


def test_preoutcome_freeze_and_parent_unchanged_guard():
    changed=json.loads(json.dumps(PLAN))
    changed["external_relative_daily_envelopes"]["epsilon_grid"]=[0,.1,.2,.4]
    with pytest.raises(ValueError,match="frozen"):
        first_frozen_daily_drift_panel(changed,PARENT,CAL)
    changed=json.loads(json.dumps(PARENT))
    changed["first_focused_ci_run"]=0
    with pytest.raises(ValueError,match="frozen"):
        first_frozen_daily_drift_panel(PLAN,changed,CAL)
