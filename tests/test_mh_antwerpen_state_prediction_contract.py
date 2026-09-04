from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "MH_ANTWERPEN_STATE_PREDICTION_CONTRACT.json"


def _load():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_contract_is_prospective_and_uses_new_public_endpoint():
    c = _load()
    assert c["contract_id"] == "mh-antwerpen-state-prediction-v1"
    assert c["outcome_access_before_freeze"] is False
    assert c["source"]["archive_doi"] == "10.5281/zenodo.10054153"
    assert c["source"]["movebank_study_id"] == 938783961
    assert c["frozen_endpoints_untouched"] == {
        "tawaki": True,
        "tadarida_teniotis": True,
        "snapshot_serengeti": True,
    }


def test_contract_freezes_target_covariates_and_independence():
    c = _load()
    bins = c["prediction_target"]["fixed_bins_m_amsl"]
    assert [x["label"] for x in bins] == [
        "low_lt50",
        "lower_mid_50_200",
        "upper_mid_200_500",
        "high_ge500",
    ]
    assert c["prediction_target"]["binning_may_not_be_retuned_after_data_access"] is True
    assert c["covariates"]["primary_X"] == [
        "external_temperature_c",
        "latitude",
        "longitude",
        "sin_local_solar_hour",
        "cos_local_solar_hour",
        "sin_day_of_year",
        "cos_day_of_year",
    ]
    assert c["independence_and_admission"]["independent_group"] == "individual-local-identifier"
    assert c["independence_and_admission"]["cross_validation"] == "leave-one-eligible-individual-out"
    assert c["independence_and_admission"]["minimum_eligible_individuals"] == 4


def test_contract_freezes_primary_model_and_terminal_rule():
    c = _load()
    rf = c["models"]["primary"]
    assert rf == {
        "name": "random_forest",
        "n_estimators": 500,
        "min_samples_leaf": 20,
        "max_features": "sqrt",
        "random_state": 20260905,
        "class_weight": None,
    }
    assert c["models"]["model_selection_after_outcome_access"] is False
    terminal = c["terminal_rule_primary_rf"]
    assert terminal["generalizing"].startswith("every eligible held-out individual")
    assert terminal["mean_gain_is_descriptive_only"] is True
    assert terminal["sensitivity_model_cannot_override_primary_terminal"] is True


def test_contract_pins_all_public_gps_checksums():
    files = _load()["source"]["gps_files"]
    assert [x["name"] for x in files] == [
        "MH_ANTWERPEN-gps-2018.csv.gz",
        "MH_ANTWERPEN-gps-2019.csv.gz",
        "MH_ANTWERPEN-gps-2020.csv.gz",
        "MH_ANTWERPEN-gps-2021.csv.gz",
        "MH_ANTWERPEN-gps-2022.csv.gz",
    ]
    assert all(len(x["md5"]) == 32 for x in files)
