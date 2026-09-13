from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_MEE_STATE_PREDICTION_V5_CONTRACT.json"
RECEIPT = ROOT / "BOP_RODENT_SPECIES_BASELINE_AMENDMENT_RECEIPT.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v5_contract_is_narrow_and_preserves_v4_and_primary_bop_endpoint():
    contract = _read(CONTRACT)
    assert contract["base_manuscript"] == "n2-mee-state-prediction-manuscript-v4"
    assert contract["required_new_evidence"] == ["BOP_RODENT_SPECIES_BASELINE_AMENDMENT_RECEIPT.json"]
    primary = contract["bop_primary_endpoint_preserved"]
    assert primary["positive_log_gain_individuals"] == 27
    assert primary["eligible_individuals"] == 30
    assert primary["terminal_category"] == "empirical_state_prediction_mixed"
    assert primary["terminal_reclassification_allowed"] is False
    assert all(value is False for value in contract["v4_preservation"].values())


def test_v5_contract_matches_canonical_amendment_boundary():
    contract = _read(CONTRACT)
    receipt = _read(RECEIPT)
    decomposition = contract["descriptive_decomposition"]
    assert decomposition["post_outcome"] is receipt["post_outcome_amendment"] is True
    assert decomposition["model_refit_performed"] is receipt["model_refit_performed"] is False
    assert decomposition["raw_source_data_reaccessed"] is receipt["raw_source_data_reaccessed"] is False
    assert decomposition["retuning_performed"] is receipt["retuning_performed"] is False
    assert decomposition["can_override_primary_terminal"] is False
    assert contract["bop_primary_endpoint_preserved"]["terminal_category"] == receipt["frozen_primary_endpoint"]["terminal_category"]


def test_v5_scientific_boundary_forbids_reopening_or_causal_reinterpretation():
    boundary = _read(CONTRACT)["scientific_boundary"]
    assert boundary
    assert all(value is False for value in boundary.values())
