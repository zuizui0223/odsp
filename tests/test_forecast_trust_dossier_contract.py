from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dossier_contract_preserves_non_collapsing_boundaries():
    contract = json.loads((ROOT / "FORECAST_TRUST_DOSSIER_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"] == "odsp-forecast-trust-dossier-v1"
    roles = contract["data_role_separation"]
    assert roles["deployment_warning_can_override_validation_history"] is False
    assert roles["validation_admission_can_suppress_novelty_warning"] is False
    obligations = contract["frozen_obligations"]
    assert obligations["robust_strict_validation_still_admitted"] is True
    assert obligations["robust_strict_deployment_status"] == "strict_extrapolation_warning"
    assert obligations["too_few_blocks_validation_status"] == "unavailable"
    assert obligations["aggregate_confidence_score_emitted"] is False
    ceiling = contract["claim_boundary"]
    assert ceiling["dossier_is_new_statistical_evidence"] is False
    assert ceiling["novelty_is_error_probability"] is False
    assert ceiling["in_domain_status_guarantees_correct_prediction"] is False
