from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v6_contract_is_copy_edit_only_and_preserves_v5():
    contract = json.loads(
        (ROOT / "N2_MEE_STATE_PREDICTION_V6_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "n2-mee-state-prediction-manuscript-v6-copyedit"
    preserve = contract["required_preservation"]
    assert preserve["v5_manuscript_overwritten"] is False
    assert preserve["v5_handoff_packet_overwritten"] is False
    assert preserve["v5_visual_qa_receipts_overwritten"] is False
    assert preserve["empirical_endpoint_rerun"] is False
    assert preserve["bop_primary_comparator_changed"] is False
    assert preserve["bop_primary_terminal_changed"] is False
    assert contract["abstract_requirement"]["minimum_headroom_words"] == 10
    boundary = contract["scientific_boundary"]
    assert boundary["copy_edit_only"] is True
    assert boundary["new_empirical_evidence"] is False
    assert boundary["post_outcome_evidence_recast_as_prospective"] is False
