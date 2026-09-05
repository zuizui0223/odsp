from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "PREDICTION_TRUST_LAYER_CONTRACT.json"
V4_RECEIPT = ROOT / "N2_MEE_STATE_PREDICTION_V4_FINAL_READINESS_RECEIPT.json"


def test_prediction_trust_contract_preserves_frozen_v4_and_claim_boundaries():
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert c["contract_id"] == "odsp-prediction-trust-layer-v1"
    assert c["version_line"] == "0.11-development"

    conformal = c["components"]["conformal_state_uncertainty"]
    assert conformal["conditional_coverage_guaranteed"] is False
    assert conformal["distribution_shift_robustness_guaranteed"] is False

    novelty = c["components"]["environmental_novelty"]
    assert novelty["novelty_is_prediction_correction"] is False
    assert novelty["novelty_proves_prediction_failure"] is False
    assert novelty["positive_affine_feature_rescaling_invariance_required"] is True

    profile = c["components"]["generalization_profile"]
    assert profile["coarse_level_positive_may_override_fine_level_failure"] is False
    assert profile["pooled_observation_mass_may_rescue_conflicting_group"] is False
    assert profile["in_sample_predictions_allowed_for_transfer_claim"] is False

    frozen = c["frozen_v4_preservation"]
    assert not any(frozen.values())


def test_v4_readiness_receipt_remains_present_and_scientifically_closed():
    r = json.loads(V4_RECEIPT.read_text(encoding="utf-8"))
    assert r["receipt_id"] == "n2-mee-state-prediction-v4-final-readiness"
    assert r["prospective_empirical_prediction"]["MH_ANTWERPEN"]["terminal_category"] == "empirical_state_prediction_unavailable"
    assert r["prospective_empirical_prediction"]["BOP_RODENT"]["terminal_category"] == "empirical_state_prediction_mixed"
    assert r["prospective_empirical_prediction"]["BOP_RODENT"]["primary_positive_log_gain_individuals"] == 27
    assert r["scientific_boundary"]["bop_mixed_terminal_relaxed"] is False
    assert r["scientific_boundary"]["mh_unavailable_endpoint_rescued"] is False


def test_trust_layer_is_publicly_exported_without_changing_frozen_review_modules():
    init_text = (ROOT / "odsp" / "__init__.py").read_text(encoding="utf-8")
    for token in (
        "fit_state_conformal_calibrator",
        "fit_environmental_novelty_model",
        "generalization_profile_from_probability_field",
        "run_prediction_trust_benchmark",
    ):
        assert token in init_text

    builder = (ROOT / "scripts" / "build_n2_mee_review_bundle_v4.py").read_text(encoding="utf-8")
    assert 'FROZEN_REVIEW_PACKAGE_VERSION = "0.10.0"' in builder
    assert "prediction_uncertainty.py" not in builder.split("PREDICTION_MODULES = (", 1)[1].split(")", 1)[0]
    assert "prediction_novelty.py" not in builder.split("PREDICTION_MODULES = (", 1)[1].split(")", 1)[0]
    assert "generalization_profile.py" not in builder.split("PREDICTION_MODULES = (", 1)[1].split(")", 1)[0]
