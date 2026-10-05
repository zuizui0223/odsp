from __future__ import annotations
import json
from pathlib import Path

P=Path("ODSP_TRAINING_PROCESS_V5_EXTERNAL_REGISTRATION_CORRECTION_CONTRACT.json")

def test_registry_v5_chronology_error_is_explicit_not_rewritten():
    p=json.loads(P.read_text(encoding="utf-8"))
    c=p["chronology"]
    assert c["registration_preceded_official_hash_ci_completion_seconds"] == 103
    assert c["v5_registration_satisfied_frozen_ordering_rule"] is False
    d=p["disposition"]
    assert d["registry_v5_retained_for_historical_provenance"] is True
    assert d["registry_v5_rewritten"] is False
    assert d["registry_v5_is_not_active_after_v6_promotion"] is True

def test_correction_does_not_change_statistics_or_claim_retroactive_success():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert p["disposition"]["statistical_qualification_results_changed"] is False
    assert p["disposition"]["external_endpoint_implementation_changed"] is False
    assert p["prospective_boundary"]["no_retroactive_claim_that_registry_v5_met_its_ordering_gate"] is True
