from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "BOP_RODENT_SPECIES_BASELINE_AMENDMENT_CONTRACT.json"


def _load():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_amendment_is_explicitly_post_outcome_and_descriptive():
    contract = _load()
    assert contract["post_outcome_amendment"] is True
    assert contract["analysis_type"] == "descriptive_secondary_decomposition"
    assert contract["frozen_primary_endpoint"]["must_not_be_reclassified_by_this_amendment"] is True


def test_amendment_uses_only_frozen_result_artifact_without_refit():
    contract = _load()
    source = contract["source_evidence"]
    assert source["workflow_run_id"] == 33897335554
    assert source["artifact_id"] == 9946375169
    assert source["artifact_digest"] == "sha256:49291cf0f2c90955fc23bdc702ccef1ef8b710ce100c8e338c5fc6b91388b8f7"
    assert source["result_json_sha256"] == "9e681852d1982e03d9a0696ce5b78c8f367bbffcc401bc54e9b62368a211499d"
    assert source["model_refit_required"] is False
    assert source["raw_source_data_reaccess_required"] is False


def test_decomposition_identity_and_reporting_are_frozen():
    contract = _load()
    decomposition = contract["per_individual_decomposition"]
    assert decomposition["total_gain"].startswith("G_total")
    assert decomposition["species_component"].startswith("G_species")
    assert decomposition["context_within_species_component"].startswith("G_context")
    assert decomposition["identity"] == "G_total = G_species + G_context"
    assert decomposition["required_additivity_tolerance"] == 1e-12
    assert contract["reporting"]["heldout_state_counts_by_species"] is True
    assert contract["reporting"]["primary_terminal_decision_recomputed"] is False
    assert contract["reporting"]["primary_terminal_decision_changed"] is False


def test_claim_boundary_does_not_promote_amendment_to_new_primary_endpoint():
    contract = _load()
    prohibited = set(contract["claim_boundary"]["does_not_support"])
    assert "a newly prospective BOP endpoint" in prohibited
    assert "retuning or replacement of the frozen primary comparator" in prohibited
    assert "changing the 27/30 primary result or empirical_state_prediction_mixed terminal category" in prohibited
