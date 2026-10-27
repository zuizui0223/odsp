from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_bop_common_input_transport_v1 import (
    CONTRACT,load_frozen_contract,run_world,
)


def test_contract_frozen_roles_cannot_relabel_old_RF_as_compatible():
    c=load_frozen_contract()
    assert c["frozen_date"]=="2026-10-26"
    assert c["role"]=="prospective_known_truth_method_validation_only_not_real_BOP_or_Dryad_results"
    assert c["predecessors"]["closed_BOP_terminal"]=="empirical_state_prediction_mixed"
    assert c["predecessors"]["Dryad_external_source_gate"]=="NOT_ADMITTED"
    assert c["predecessors"]["Dryad_original_RF_gate"]=="ORIGINAL_RF_PREDICTOR_INCOMPATIBLE"
    assert c["synthetic_generator"]["worlds"]==24
    assert c["synthetic_generator"]["seed"]==20261028
    assert c["synthetic_generator"]["group_counts_per_stratum"]=={
        "BOP_training":20,"DRYAD_calibration":39,"DRYAD_validation":30
    }
    assert c["acceptance"]["expected_validation_groups_each_condition"]==2880


def test_one_frozen_world_is_computed_from_two_synthetic_source_schemas():
    c=load_frozen_contract()
    w=run_world(c,0)
    assert w["training_individuals"]==80
    assert w["calibration_individuals"]==156
    assert w["validation_individuals"]==120
    assert 0<=w["covered_same"]<=120
    assert 0<=w["covered_validation_shift"]<=120
    assert w["source_shift_from_BOP_training_to_Dryad_target"] is True
    assert w["training_model_refitted_after_target_outcome"] is False
    assert w["target_identity_crosswalk_real_world_verified"] is False
    assert w["original_bop_terminal_changed"] is False
    for field in ("frozen_forecast_plan_sha256","calibration_sha256",
                  "model_sha256","reference_sha256"):
        assert len(w[field])==64


@pytest.mark.parametrize("location,match",[
    (("seed",0),"contract changed"),
    (("worlds",32),"contract changed"),
    (("miscoverage",0.5),"contract changed"),
    (("BOP_context_amplitude",0.0),"contract changed"),
])
def test_after_outcome_scientific_selection_contract_cannot_change(tmp_path:Path,location,match):
    c=load_frozen_contract()
    key,value=location
    c["synthetic_generator"][key]=value
    path=tmp_path/"post_outcome_tune.json"
    path.write_text(json.dumps(c),encoding="utf-8")
    with pytest.raises(ValueError,match=match):
        load_frozen_contract(path)


def test_outcome_blind_source_projection_contract_is_not_prospective_real_bop():
    c=load_frozen_contract()
    assert c["source_schema"]["no_fitted_temperature_imputation"] is True
    assert c["source_schema"]["exclude_latitude_as_direct_predictor"] is True
    assert c["source_schema"]["prior_external_identity_nonoverlap_verification_required_for_empirical_admission"] is True
    assert c["interpretation"]["actual_cross_study_independence_not_verified"] is True
    assert c["interpretation"]["actual_Dryad_source_remains_unadmitted"] is True
    assert c["interpretation"]["original_BOP_RF_not_rerun"] is True
    assert "DATA_1a.csv" not in str(CONTRACT)
