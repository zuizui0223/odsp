from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_dossier_v3_contract_preserves_v2_and_radius_boundaries():
    contract=json.loads((ROOT/"FORECAST_TRUST_DOSSIER_V3_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-forecast-trust-dossier-v3-radius"
    inheritance=contract["inheritance"]
    assert inheritance["v2_validation_semantics_unchanged"] is True
    assert inheritance["v2_robustness_profile_semantics_unchanged"] is True
    radius=contract["radius_layer"]
    assert radius["radius_can_rewrite_validation_history"] is False
    assert radius["radius_can_rescue_failed_validation"] is False
    assert radius["certified_gamma_and_break_gamma_retained_separately"] is True
    assert radius["aggregate_confidence_score_emitted"] is False
    boundary=contract["claim_boundary"]
    assert boundary["dossier_v3_adds_new_statistical_evidence"] is False
    assert boundary["radius_is_probability_of_correctness"] is False
    assert boundary["radius_proves_no_observation_bias"] is False
