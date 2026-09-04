from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "BOP_RODENT_STATE_PREDICTION_CONTRACT.json"
RECEIPT = ROOT / "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json"


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_terminal_receipt_preserves_prospective_contract_and_no_retuning():
    contract = _read(CONTRACT)
    receipt = _read(RECEIPT)

    assert receipt["contract_id"] == contract["contract_id"] == "bop-rodent-state-prediction-v1"
    assert contract["outcome_access_before_freeze"] is False
    assert receipt["prospective_provenance"]["contract_merged_before_outcome_access"] is True
    assert receipt["prospective_provenance"]["retuning_performed"] is False
    assert receipt["source"]["archive_doi"] == contract["source"]["archive_doi"]
    assert receipt["source"]["movebank_study_id"] == contract["source"]["movebank_study_id"]
    assert [item["expected_md5"] for item in receipt["source"]["file_md5s"]] == [
        item["md5"] for item in contract["source"]["gps_files"]
    ]
    assert all(item["expected_md5"] == item["observed_md5"] for item in receipt["source"]["file_md5s"])


def test_terminal_receipt_pins_primary_mixed_result_without_mean_rescue():
    receipt = _read(RECEIPT)
    primary = receipt["primary_random_forest"]
    gains = np.asarray(primary["individual_gains"], dtype=float)

    assert primary["terminal_category"] == "empirical_state_prediction_mixed"
    assert primary["eligible_individual_count"] == 30
    assert primary["positive_individual_count"] == 27
    assert primary["nonpositive_individual_count"] == 3
    assert int(np.count_nonzero(gains > 0)) == 27
    assert int(np.count_nonzero(gains <= 0)) == 3
    assert np.isclose(float(np.mean(gains)), primary["mean_gain_descriptive"], atol=1e-15)
    assert np.isclose(float(np.median(gains)), primary["median_gain_descriptive"], atol=1e-15)
    assert primary["mean_gain_descriptive"] > 0
    assert primary["reason"] == "frozen_all_individual_primary_rf_gain_rule"
    assert primary["positive_brier_improvement_count"] == 30


def test_terminal_receipt_species_categories_preserve_individual_conflict():
    receipt = _read(RECEIPT)
    species = receipt["primary_random_forest"]["species_categories"]

    assert species["Buteo buteo"]["category"] == "generalizing"
    assert species["Buteo buteo"]["positive_count"] == 5
    assert species["Circus pygargus"]["category"] == "generalizing"
    assert species["Circus pygargus"]["positive_count"] == 9
    assert species["Circus aeruginosus"]["category"] == "mixed"
    assert species["Circus aeruginosus"]["positive_count"] == 7
    assert species["Circus cyaneus"]["category"] == "mixed"
    assert species["Circus cyaneus"]["positive_count"] == 6


def test_terminal_receipt_sensitivity_cannot_override_primary_terminal():
    receipt = _read(RECEIPT)
    sensitivity = receipt["multinomial_logit_sensitivity"]

    assert sensitivity["eligible_individual_count"] == 30
    assert sensitivity["positive_individual_count"] == 22
    assert sensitivity["nonpositive_individual_count"] == 8
    assert sensitivity["mean_gain_descriptive"] > 0
    assert receipt["primary_random_forest"]["terminal_category"] == "empirical_state_prediction_mixed"


def test_terminal_receipt_keeps_scientific_ceiling_closed():
    receipt = _read(RECEIPT)
    assert receipt["closed_endpoints_untouched"] == {
        "mh_antwerpen": True,
        "snapshot_serengeti": True,
        "tadarida_teniotis": True,
        "tawaki": True,
    }
    unsupported = set(receipt["interpretation"]["does_not_support"])
    assert "height above ground without terrain correction" in unsupported
    assert "causal effects of weather, time, geography or species identity" in unsupported
    assert "universal transfer to bird species outside the admitted public dataset" in unsupported
