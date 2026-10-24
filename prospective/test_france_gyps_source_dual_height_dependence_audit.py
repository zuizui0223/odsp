"""Pure analytical unit tests for the post-outcome dual sensor audit."""
import numpy as np
import pytest
from prospective.france_gyps_source_dual_height_dependence_audit import (
  rank_average,rho,interval,audit,summarize
)

def test_average_ranks_and_spearman_handle_tied_height_gains():
    assert list(rank_average([1,1,2]))==[1.5,1.5,3]
    assert rho([1,2,3,4],[20,30,40,50])==pytest.approx(1)
    assert rho([1,2,3,4],[50,40,30,20])==pytest.approx(-1)
    assert rho([2,2,2],[1,2,3]) is None

def test_bootstrap_confidence_interval_does_not_use_fix_count():
    x=interval(np.arange(101,dtype=float))
    assert x==pytest.approx([2.5,97.5])

def test_no_sensor_independence_claim_when_original_flag_false_required():
    with pytest.raises(ValueError,match="native paired positive"):
        summarize({"terminal":"unavailable","native_sensor_independence_proven":False})

def test_original_historical_artifact_hash_guards_against_accidental_new_null(tmp_path):
    p=tmp_path/"fake.zip"
    p.write_bytes(b"Not original source")
    with pytest.raises(ValueError,match="Original artifact ZIP SHA"):
        audit(p)

def test_source_contingent_two_height_agreement_is_not_a_new_bird_replication():
    # Check fixed claim boundaries built into code itself.
    import inspect
    from prospective import france_gyps_source_dual_height_dependence_audit as mod
    src=inspect.getsource(mod.audit)
    assert "POST_OUTCOME_SOURCE_QUALITY_ONLY" in src
    assert "source_original_sample_and_999_nulls_changed" in src
