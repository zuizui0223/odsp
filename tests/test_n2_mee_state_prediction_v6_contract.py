from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v6_contract_preserves_v5_primary_and_declares_population_amendment():
    contract = json.loads(
        (ROOT / "N2_MEE_STATE_PREDICTION_V6_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert (
        contract["contract_id"]
        == "n2-mee-state-prediction-manuscript-v6-population-amendment"
    )
    preserve = contract["required_preservation"]
    assert preserve["v5_manuscript_overwritten"] is False
    assert preserve["v5_handoff_packet_overwritten"] is False
    assert preserve["v5_visual_qa_receipts_overwritten"] is False
    assert preserve["empirical_endpoint_rerun"] is False
    assert preserve["bop_primary_comparator_changed"] is False
    assert preserve["bop_primary_terminal_changed"] is False
    assert preserve["bop_existing_post_outcome_decomposition_changed"] is False

    amendment = contract["population_amendment"]
    assert amendment["post_outcome"] is True
    assert amendment["analysis_type"] == "descriptive_secondary_population_transfer"
    assert amendment["familywise_confirmatory_claim"] is False
    assert amendment["primary_endpoint_reclassified"] is False
    assert amendment["group"] == "heldout_individual"
    assert amendment["population_cluster"] == "species"
    assert amendment["represented_cluster_count"] == 4

    assert contract["abstract_requirement"]["minimum_headroom_words"] == 10
    boundary = contract["scientific_boundary"]
    assert boundary["copy_edit_only"] is False
    assert boundary["new_post_outcome_descriptive_summary"] is True
    assert boundary["prospective_status_changed"] is False
    assert boundary["post_outcome_evidence_recast_as_prospective"] is False
    assert boundary["causal_claim_added"] is False
    assert boundary["universal_transfer_claim_added"] is False
