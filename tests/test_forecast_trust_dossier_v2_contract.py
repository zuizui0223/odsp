from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_dossier_v2_contract_preserves_evidence_boundaries():
    contract=json.loads((ROOT/"FORECAST_TRUST_DOSSIER_V2_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-forecast-trust-dossier-v2"
    rule=contract["decision_rule"]
    assert rule["validation_admission_source"]=="BiasRobustCandidateScore.bias_robust_trusted_admissible"
    assert rule["sampling_weight_sensitivity_can_rewrite_validation_history"] is False
    assert rule["bounded_reweighting_sensitivity_can_rewrite_validation_history"] is False
    assert rule["deployment_novelty_can_rewrite_validation_history"] is False
    assert rule["in_domain_status_can_rescue_failed_validation"] is False
    assert rule["aggregate_confidence_score_emitted"] is False
    boundary=contract["claim_boundary"]
    assert boundary["dossier_adds_new_statistical_evidence"] is False
    assert boundary["sampling_weight_stability_proves_no_observation_bias"] is False
    assert boundary["critical_gamma_is_inferred_from_data_generating_process"] is False
    assert boundary["novelty_is_error_probability"] is False
