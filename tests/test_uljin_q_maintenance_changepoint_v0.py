"""Known independent camera service break, exact q source mean and 16-site tests."""
from pathlib import Path
import json
import numpy as np
import pytest
pytest.importorskip("scipy",reason="optional exact reference q CP calibration")
from odsp.uljin_q_maintenance_changepoint_v0 import (
    WORLDS,METHODS,BUDGETS,source_date_groups,
    step_day_q,source_reference,first_frozen_maintenance_panel
)
from odsp.uljin_station_season_camera_q_v0 import physical_site_q
from odsp.uljin_common_clock_mechanistic_comparison_v0 import original_days

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=json.loads((ROOT/"ULJIN_Q_MAINTENANCE_CHANGEPOINT_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_Q_TEMPORAL_POOLING_LIPSCHITZ_V0_FIRST_RESULT_LEDGER.json").read_text())
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def test_external_service_break_and_all_date_reference_partitions():
    days,branch=original_days(CAL)
    assert len(days)==82
    _,base=physical_site_q(1)
    stable=step_day_q(branch,base,0)
    stepped=step_day_q(branch,base,1)
    assert stable.shape==stepped.shape==(32,82,6)
    assert np.allclose(stable,base[:,branch,:])
    assert np.allclose(stepped[:,38,:],base[:,0,:])
    assert np.allclose(stepped[:,40,:],.4+.2*base[:,0,:])
    assert np.all((stepped>0)&(stepped<1))
    for method in METHODS:
        groups=source_date_groups(method)
        assert [j for group in groups for j in group]==list(range(41))
        assert sum(len(group) for group in groups)==41
        assert len(groups)=={METHODS[0]:41,METHODS[1]:6,METHODS[2]:7}[method]
    assert any(any(j<20 for j in group) and any(j>=20 for j in group)
               for group in source_date_groups(METHODS[1]))
    assert not any(any(j<20 for j in group) and any(j>=20 for j in group)
                   for group in source_date_groups(METHODS[2]))


def test_correct_source_iid_group_mean_q_vs_nontransportable_daily_q():
    _,branch=original_days(CAL)
    _,base=physical_site_q(1)
    qstep=step_day_q(branch,base,1)
    for bi,(n_day,total) in enumerate(BUDGETS):
        assert total==16*2*6*41*n_day
        daily,unaware,split=(source_reference(qstep,1,bi,k)
                            for k in range(3))
        for result in (daily,unaware,split):
            assert result["n_independent_gold_passages_total"]==total
            assert result["source_iid_Binomial_for_GROUP_MEAN"]
            assert result["daily_lower"].shape==(16,82,6)
            assert result["daily_upper"].shape==(16,82,6)
        assert not unaware["source_to_individual_date_transport_attested"]
        assert daily["source_to_individual_date_transport_attested"]
        assert split["source_to_individual_date_transport_attested"]
        for result in (daily,split):
            if result["q_group_means_CP_joint_coverage_ORACLE_ONLY"]:
                assert result["individual_day_q_joint_coverage_ORACLE_ONLY"]
                assert np.all(result["daily_lower"]<=qstep[16:]+1e-12)
                assert np.all(result["daily_upper"]>=qstep[16:]-1e-12)
        assert unaware["n_q_groups"]==16*2*6*6
        assert split["n_q_groups"]==16*2*6*7


def test_full_original_96_paired_288_camera_source_method_cases():
    d=first_frozen_maintenance_panel(CONTRACT,PARENT,CAL)
    assert d["status"]=="SOURCE_FREE_KNOWN_MAINTENANCE_CHANGEPOINT_Q"
    assert len(d["all_96_paired_clock_model_comparisons"])==96
    assert len(d["all_12_reference_source_calibration_receipts"])==12
    assert d["total_predeclared_method_results"]==288
    assert d["same_original_mirrored_astronomy_pairs"]==41
    assert d["original_civil_15min_response_bins"]==96
    assert d["step_world_unaware_source_HOLD_pairs"]==48
    assert d["per_original_design_combined_type_I_bound"]==.05
    assert d["group_source_iid_binomial_valid_even_with_changepoint"]
    assert d["no_synthetic_oracle_coverage_gating"]
    for case in d["all_96_paired_clock_model_comparisons"]:
        arms=case["three_equal_cost_calibration_methods"]
        assert set(arms)==set(METHODS)
        for arm in arms.values():
            assert arm["oracle_coverage_never_an_admission_gate"]
            if arm["site_majority_certified"] is True:
                assert arm["robust_positive_physical_site_count"]>=14
            if arm["status"]=="HOLD_REFERENCE_GROUP_MEAN_NOT_VALID_FOR_STEP_DATE":
                assert arm["site_majority_certified"] is None
    assert d["no_authentic_EcoBank_wildlife_camera_source_or_maintenance_data"]
    json.dumps(d,allow_nan=False)


def test_frozen_contract_and_prior_first_result_fail_closed():
    changed=json.loads(json.dumps(CONTRACT))
    changed["q_truth_worlds"][1]["step_index"]=18
    with pytest.raises(ValueError,match="frozen"):
        first_frozen_maintenance_panel(changed,PARENT,CAL)
    prior=json.loads(json.dumps(PARENT))
    prior["first_completed_scored_ci_run"]=1
    with pytest.raises(ValueError,match="frozen"):
        first_frozen_maintenance_panel(CONTRACT,prior,CAL)
