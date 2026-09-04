from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "BOP_RODENT_STATE_PREDICTION_CONTRACT.json"


def _load():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_contract_is_prospective_and_new_endpoint():
    c = _load()
    assert c["contract_id"] == "bop-rodent-state-prediction-v1"
    assert c["outcome_access_before_freeze"] is False
    assert c["source"]["archive_doi"] == "10.5281/zenodo.10055071"
    assert c["source"]["public_metadata_individual_count"] == 35
    assert c["source"]["public_metadata_species_count"] == 5
    assert c["closed_endpoints_untouched"] == {
        "tawaki": True,
        "tadarida_teniotis": True,
        "snapshot_serengeti": True,
        "mh_antwerpen": True,
    }


def test_contract_freezes_same_altitude_states_and_multi_species_features():
    c = _load()
    assert [x["label"] for x in c["prediction_target"]["fixed_bins_m_amsl"]] == [
        "low_lt50",
        "lower_mid_50_200",
        "upper_mid_200_500",
        "high_ge500",
    ]
    assert c["prediction_target"]["same_bins_as_mh_antwerpen"] is True
    assert c["covariates"]["categorical"] == ["species_identity_one_hot"]
    assert c["covariates"]["no_feature_selection_after_outcome_access"] is True


def test_contract_requires_real_multi_species_individual_independence():
    c = _load()["independence_and_admission"]
    assert c["minimum_eligible_individuals_per_admitted_species"] == 3
    assert c["minimum_admitted_species"] == 3
    assert c["minimum_total_eligible_individuals"] == 12
    assert c["cross_validation"] == "five deterministic individual-group folds"
    assert "sha256" in c["fold_assignment"]
    assert c["pooled_heldout_mass_can_rescue_conflicting_individuals"] is False


def test_contract_freezes_primary_rf_and_all_individual_terminal():
    c = _load()
    rf = c["models"]["primary"]
    assert rf["name"] == "random_forest"
    assert rf["n_estimators"] == 500
    assert rf["min_samples_leaf"] == 25
    assert rf["random_state"] == 20260905
    assert c["models"]["model_selection_after_outcome_access"] is False
    terminal = c["terminal_rule_primary_rf"]
    assert terminal["generalizing"].startswith("every scored held-out individual")
    assert terminal["mean_gain_is_descriptive_only"] is True
    assert terminal["sensitivity_model_cannot_override_primary_terminal"] is True


def test_contract_pins_all_v3_gps_checksums():
    files = _load()["source"]["gps_files"]
    assert [(x["name"], x["md5"]) for x in files] == [
        ("BOP_RODENT-gps-2020.csv.gz", "c2309baee0edf6bf4f923ab981d59749"),
        ("BOP_RODENT-gps-2021.csv.gz", "6ed130a247f4e9ecba13253a76c69ae6"),
        ("BOP_RODENT-gps-2022.csv.gz", "f1622dc9bcfc3c3f72101a7ce0ecd719"),
    ]
