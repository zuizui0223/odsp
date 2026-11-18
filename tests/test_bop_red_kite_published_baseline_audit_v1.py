"""All checks use published aggregate numbers; never use source GPS or labels."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest
from scripts.bop_red_kite_published_baseline_audit_v1 import SOURCE,calculate

def _source():
    return json.loads(SOURCE.read_text(encoding="utf-8"))

def test_published_counts_arithmetic_and_claim_boundary():
    out=calculate(_source())
    v={x["state"]:x for x in out["benchmarks"]}
    assert out["status"]=="PUBLISHED_AGGREGATE_DIAGNOSTIC_ONLY"
    assert out["biological_individuals_published"]==63
    assert out["individual_seasons_published"]==99
    assert out["replication_units_verified_from_source"] is False
    assert out["new_prediction_evaluated"] is False
    assert out["rank_lower_bound_calibrated"] is False
    assert v["home_range"]["posthoc_majority_class_accuracy_pct"]==round(100*98/99,5)
    assert v["nest_attempt"]["posthoc_majority_class_accuracy_pct"]==round(100*89/99,5)
    assert v["nest_success"]["posthoc_majority_class_accuracy_pct"]==round(100*55/89,5)
    assert v["home_range"]["illustrative_accuracy_gap_percentage_points"] < 0
    assert v["nest_attempt"]["illustrative_accuracy_gap_percentage_points"] < 0
    assert v["nest_success"]["illustrative_accuracy_gap_percentage_points"] > 0
    assert all(not x["valid_independent_prediction_comparison"] for x in v.values())
    assert v["nest_success"]["success_denominator_not_reconciled"] is True
    assert out["original_bop_terminal"]=="empirical_state_prediction_mixed"

@pytest.mark.parametrize("path,value",[
    (("reported_german","eligible_birds"),99),
    (("reported_german","nest_attempt_yes_seasons"),10),
    (("published_accuracy_pct","nest_attempt"),98.0),
    (("interpretation","new_data_access"),"RAW_GPS"),
    (("interpretation","original_bop_legacy_terminal"),"POSITIVE"),
    (("status",),"NEW_EXTERNAL_RESULT"),
])
def test_rewritten_counts_and_claims_fail_closed(path,value):
    obj=deepcopy(_source())
    ptr=obj
    for k in path[:-1]:
        ptr=ptr[k]
    ptr[path[-1]]=value
    with pytest.raises(ValueError):
        calculate(obj)

def test_public_record_is_only_aggregate():
    obj=_source()
    assert obj["interpretation"]["biological_replication_unit"].startswith("bird_id")
    assert obj["interpretation"]["new_data_access"]=="NONE"
    assert "previously published" in obj["future_analysis_prerequisites"][-1]
