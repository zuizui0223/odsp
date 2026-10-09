"""Valid binomial reference q still nontransportable to target distance mixture."""
import json
from pathlib import Path
import numpy as np
import pytest
pytest.importorskip("scipy",reason="optional source-free exact q reference calibration")
from odsp.uljin_iid_reference_q_transport_v1 import (
    NEAR,FAR,WREF,NS,SEED,REPS,WORLDS,
    iid_reference_trial,iid_reference_transport_full_panel,
)
from odsp.uljin_q_transport_distance_mix_v0 import q_effective,detector_crossproduct

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_IID_REFERENCE_Q_TRANSPORT_V1_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_Q_TRANSPORT_DISTANCE_MIX_V0_FIRST_RESULT_LEDGER.json").read_text())

def test_proper_source_reference_is_iid_bernoulli_point6_but_target_not():
    assert q_effective(NEAR,FAR,WREF)==pytest.approx([.6]*4)
    assert detector_crossproduct(q_effective(NEAR,FAR,WREF))==pytest.approx(1)
    q=q_effective(NEAR,FAR,WORLDS[1][2])
    assert q==pytest.approx([.42,.78,.78,.42])
    assert detector_crossproduct(q)==pytest.approx((.78/.42)**2)
    assert abs(q[0]-.6)>.1


def test_dedicated_IID_reference_stream_independent_and_parent_events_reused():
    a=iid_reference_trial(1,1,13)
    b=iid_reference_trial(1,1,13)
    assert a==b
    assert a["same_parent_animal_count_table"]==b["same_parent_animal_count_table"]
    assert a["truth"]=="null_mixing_confounded"
    assert a["true_target_detector_gamma"]==pytest.approx((.78/.42)**2)
    assert a["same_parent_animal_count_table"] is not None
    assert 0<=a["proper_iid_reference_q_gamma_upper"]
    assert type(a["parent_target_standardized_certifies"]) is bool


def test_pre_frozen_all_twelve_synthetic_cases_fast_and_source_embargo():
    out=iid_reference_transport_full_panel(PLAN,PARENT,_test_replicates=3)
    assert out["status"]=="SOURCE_FREE_VALID_IID_Q_PREFLIGHT"
    assert len(out["case_results"])==12
    assert out["total_worlds"]==36
    assert out["fully_correct_iid_source_reference_q_binomial_model"]
    assert out["source_reference_q_CP_simultaneous_coverage_guaranteed"]==.975
    assert not out["no_real_Uljin_animal_or_operator_data_read"] is False
    assert not out["parent_all_first_frozen_source_free_outcomes_replayed"]
    assert out==iid_reference_transport_full_panel(PLAN,PARENT,
                                                   _test_replicates=3)
    json.dumps(out,allow_nan=False)


def test_parent_freeze_and_iid_sampling_seeds_fail_closed():
    changed=json.loads(json.dumps(PLAN))
    changed["replications"]["original_seed"]=0
    with pytest.raises(ValueError,match="contract"):
        iid_reference_transport_full_panel(changed,PARENT,_test_replicates=1)
    changed=json.loads(json.dumps(PARENT))
    changed["first_scored_ci_run"]=1
    with pytest.raises(ValueError,match="contract"):
        iid_reference_transport_full_panel(PLAN,changed,_test_replicates=1)
    with pytest.raises(ValueError):
        iid_reference_transport_full_panel(PLAN,PARENT,_test_replicates=0)
    with pytest.raises(ValueError):
        iid_reference_trial(0,0,REPS)
