from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit_bop_new_group_gain_envelope import (
    RECEIPT,
    build_report,
)


def test_frozen_bop_descriptive_rank_audit_is_read_only_and_exact():
    report = build_report()
    assert report["frozen_terminal_category"] == "empirical_state_prediction_mixed"
    assert report["frozen_positive_group_count"] == 27
    assert report["frozen_scored_group_count"] == 30
    assert report["model_refit_performed"] is False
    assert report["raw_gps_accessed"] is False
    assert report["original_terminal_reclassified"] is False
    assert "DESCRIPTIVE" in report["score_role_warning"]
    assert report["source_archived_result_sha256"] == (
        "9e681852d1982e03d9a0696ce5b78c8f367bbffcc401bc54e9b62368a211499d"
    )

    pooled = report["pooled_cross_species_descriptive"]
    p90 = pooled["alpha_0_10"]
    p95 = pooled["alpha_0_05"]
    assert p90["calibration_group_count"] == 30
    assert p90["finite_sample_rank"] == 3
    assert p90["lower_gain_bound"] == pytest.approx(-0.026803112398177786)
    assert p95["finite_sample_rank"] == 1
    assert p95["lower_gain_bound"] == pytest.approx(-0.23078224313265183)
    assert not p90["bound_above_threshold"]
    assert p90["inference_status"].startswith("descriptive_only")
    assert not p90["exchangeability_verified_by_software"]
    assert p90["not_a_mean_gain_confidence_interval"]

    species = report["within_species_descriptive"]
    assert sorted(species) == [
        "Buteo buteo",
        "Circus aeruginosus",
        "Circus cyaneus",
        "Circus pygargus",
    ]
    for name in ("Buteo buteo", "Circus aeruginosus", "Circus cyaneus"):
        item = species[name]["alpha_0_10"]
        assert item["finite_sample_rank"] == 0
        assert item["lower_gain_bound"] is None
        assert not item["bound_above_threshold"]

    pygargus = species["Circus pygargus"]["alpha_0_10"]
    assert pygargus["calibration_group_count"] == 9
    assert pygargus["finite_sample_rank"] == 1
    assert pygargus["lower_gain_bound"] == pytest.approx(0.9823947116213676)
    assert pygargus["bound_above_threshold"]
    assert species["Circus pygargus"]["alpha_0_05"]["lower_gain_bound"] is None

    # Export must be standards-compliant JSON: no +/-Infinity.
    json.dumps(report, allow_nan=False)


def test_frozen_source_changed_positive_count_is_rejected(tmp_path: Path):
    original = json.loads(RECEIPT.read_text(encoding="utf-8"))
    original["primary_random_forest"]["positive_individual_count"] = 30
    copy = tmp_path / "tampered.json"
    copy.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(ValueError, match="summary mismatch"):
        build_report(copy)


def test_frozen_source_changed_species_gains_is_rejected(tmp_path: Path):
    original = json.loads(RECEIPT.read_text(encoding="utf-8"))
    original["primary_random_forest"]["species_categories"]["Buteo buteo"]["gains"][0] = 999.0
    copy = tmp_path / "tampered.json"
    copy.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(ValueError, match="species gains"):
        build_report(copy)


def test_frozen_source_changed_contract_is_rejected(tmp_path: Path):
    original = json.loads(RECEIPT.read_text(encoding="utf-8"))
    original["contract_id"] = "retuned"
    copy = tmp_path / "tampered.json"
    copy.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(ValueError, match="frozen BOP source"):
        build_report(copy)
