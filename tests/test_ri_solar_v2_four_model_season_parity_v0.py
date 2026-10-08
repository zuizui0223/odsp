"""Four-model predictive-score identity: synthetic data, no ecology download."""
from __future__ import annotations

import hashlib
import json
import math

import pytest

from odsp import ri_solar_v2_four_model_season_parity_v0 as audit


def _fixture():
    w=(.02745845931504319,-.007018735146054966,.05909664872739589,.1306145514843494)
    s=(-.0325742873706785,.033572910321444036,.03918205629522679,.04306169049894341)
    def metrics(parts):
        names=("solar_over_clock","solar_season_over_solar",
               "clock_season_over_clock","true_solar_over_wrong_sun")
        return {name:{"mean":float(x)} for name,x in zip(names,parts)}
    document={
        "method_version":"odsp-ri-solar-vs-clock-yearseason-v2-exploratory",
        "status":"EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE",
        "heldout_site_count":43,
        "scored_heldout_events":19916,
        "primary_heldout_solar_clock":{
            "solar_transfer_both_seasons_positive":False,
            "season_groups":{
                "winter":{"unique_physical_site_count":43,"metrics":metrics(w)},
                "summer":{"unique_physical_site_count":43,"metrics":metrics(s)},
            },
        },
    }
    plan={
        "schema_version":1,
        "analysis_id":audit.VERSION,
        "status":"POST_OUTCOME_ALGEBRAIC_AUDIT_NO_NEW_ECOLOGICAL_DATA",
        "source":{
            "first_original_run_id":37747931559,
            "original_json_sha256":audit.SHA,
            "original_scientific_status":"EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE",
            "original_heldout_site_count":43,
            "original_scored_events":19916,
            "re_download_of_wildlife_source_allowed":False,
        },
        "frozen_scoring_contrasts":{
            "SS_vs_CS":"(S_vs_C)+(SS_vs_S)-(CS_vs_C)",
        },
    }
    raw=json.dumps(document,sort_keys=True,allow_nan=False).encode()
    return raw,plan


def _run(monkeypatch,raw,plan):
    monkeypatch.setattr(audit,"SHA",hashlib.sha256(raw).hexdigest())
    plan["source"]["original_json_sha256"]=audit.SHA
    return audit.audit_four_model_parity(raw,plan)


def test_original_pooled_winter_advantage_disappears_with_season_parity(monkeypatch):
    raw,plan=_fixture()
    result=_run(monkeypatch,raw,plan)
    winter=result["comparisons"]["winter"]
    summer=result["comparisons"]["summer"]
    assert winter["original_same_site_weighted_pooled_solar_minus_clock"]>0
    assert summer["original_same_site_weighted_pooled_solar_minus_clock"]<0
    assert winter["season_conditional_solar_minus_clock"]==pytest.approx(
        -.03865692455840766,abs=1e-13
    )
    assert summer["season_conditional_solar_minus_clock"]==pytest.approx(
        -.038183433344461254,abs=1e-13
    )
    assert result["winter_pooled_solar_advantage_reverses_under_equal_season_information"] is True
    assert result["clock_season_model_higher_mean_than_solar_season_in_both_groups"] is True
    assert result["comparison_significance_or_coverage_qualified"] is False
    assert result["adjusted_difference_site_bootstrap_covariance_available"] is False
    assert result["separate_component_confidence_bounds_can_be_subtracted"] is False
    assert result["original_both_seasons_solar_superiority_supported"] is False
    assert result["refitted_models_or_recomputed_scores"] is False
    assert result["reopened_wildlife_source_zip_or_individual_detections"] is False
    json.dumps(result,allow_nan=False)


def test_winter_reversal_is_explained_algebraically_by_greater_clock_season_increment(monkeypatch):
    raw,plan=_fixture()
    result=_run(monkeypatch,raw,plan)
    winter=result["comparisons"]["winter"]
    assert winter["additional_gain_from_conditioning_clock_on_season"]==pytest.approx(
        .05909664872739589
    )
    assert winter["additional_gain_from_conditioning_solar_on_season"]==pytest.approx(
        -.007018735146054966
    )
    assert winter["clock_season_information_gain_minus_solar_season_information_gain"]==pytest.approx(
        .06611538387345085
    )
    assert winter["original_same_site_weighted_pooled_solar_minus_clock"] - winter[
        "clock_season_information_gain_minus_solar_season_information_gain"
    ]==pytest.approx(winter["season_conditional_solar_minus_clock"])


def test_frozen_result_hash_must_match_exact_first_run_bytes(monkeypatch):
    raw,plan=_fixture()
    monkeypatch.setattr(audit,"SHA",hashlib.sha256(raw).hexdigest())
    plan["source"]["original_json_sha256"]=audit.SHA
    with pytest.raises(ValueError,match="SHA256"):
        audit.audit_four_model_parity(raw+b"\n",plan)


def test_cannot_relabel_original_primary_as_supported(monkeypatch):
    raw,plan=_fixture()
    obj=json.loads(raw)
    obj["status"]="EXPLORATORY_SOLAR_TRANSPORT_SIGNAL"
    tamper=json.dumps(obj,sort_keys=True).encode()
    with pytest.raises(ValueError,match="scientific method"):
        _run(monkeypatch,tamper,plan)


def test_fail_closed_on_missing_season_component_or_nonfinite_gain(monkeypatch):
    raw,plan=_fixture()
    obj=json.loads(raw)
    del obj["primary_heldout_solar_clock"]["season_groups"]["winter"][
        "metrics"]["solar_season_over_solar"]
    changed=json.dumps(obj,sort_keys=True).encode()
    with pytest.raises(KeyError):
        _run(monkeypatch,changed,plan)

    obj=json.loads(raw)
    obj["primary_heldout_solar_clock"]["season_groups"]["summer"]["metrics"][
        "clock_season_over_clock"]["mean"]=float("nan")
    changed=json.dumps(obj,sort_keys=True).encode()
    with pytest.raises(ValueError,match="finite"):
        _run(monkeypatch,changed,plan)


def test_source_and_plan_freeze_must_match(monkeypatch):
    raw,plan=_fixture()
    plan["source"]["original_heldout_site_count"]=42
    with pytest.raises(ValueError,match="anchor"):
        _run(monkeypatch,raw,plan)
    raw,plan=_fixture()
    plan["frozen_scoring_contrasts"]["SS_vs_CS"]="S_vs_C - clock"
    with pytest.raises(ValueError,match="algebra"):
        _run(monkeypatch,raw,plan)
