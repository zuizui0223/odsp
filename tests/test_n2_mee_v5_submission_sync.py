from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_n2_mee_submission_handoff_v5 import build_packet  # noqa: E402


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v5_docx_render_contract_reuses_validated_formatter_without_inheriting_visual_qa():
    contract = _read(ROOT / "N2_MEE_REVIEW_DOCX_RENDER_CONTRACT_V5.json")
    assert contract["source_rule"]["source_is_output_of_v5_manuscript_builder"] is True
    assert contract["source_rule"]["v4_renderer_implementation_reused"] is True
    assert contract["source_rule"]["empirical_endpoints_are_not_rerun"] is True
    assert contract["source_rule"]["bop_primary_comparator_is_not_modified"] is True
    assert contract["visual_qa_boundary"]["v4_25_page_visual_qa_is_not_inherited_by_v5"] is True
    assert contract["visual_qa_boundary"]["v5_exact_upload_visual_approval_completed"] is False


def test_v5_submission_checklist_does_not_inherit_v4_docx_completion():
    checklist = _read(ROOT / "N2_MEE_STATE_PREDICTION_V5_SUBMISSION_CHECKLIST.json")
    auto = checklist["automatic_items"]
    assert auto["anonymous_review_bundle_v5_generated"] is True
    assert auto["anonymous_review_docx_v5_generated"] is False
    assert auto["anonymous_review_docx_v5_structural_validation_passed"] is False
    assert auto["anonymous_review_docx_v5_development_visual_qa_passed"] is False
    assert auto["submission_handoff_packet_v5_generated"] is False
    assert checklist["ready_for_submission_without_author_metadata_completion"] is False


def test_v5_handoff_is_copy_ready_but_author_gates_remain_unresolved():
    packet = build_packet()
    assert packet["generated_from_validated_v5_sources"] is True
    assert packet["abstract_word_count"] == 350
    assert len(packet["keywords"]) == 8
    assert packet["scientific_terminal_states"] == {
        "MH_ANTWERPEN": "empirical_state_prediction_unavailable",
        "BOP_RODENT": "empirical_state_prediction_mixed",
    }
    amendment = packet["bop_descriptive_amendment"]
    assert amendment["post_outcome"] is True
    assert amendment["can_reclassify_primary_endpoint"] is False
    assert amendment["mean_within_species_context_component_nats"] > amendment["mean_species_component_nats"]
    assert all(value in (None, False) for value in packet["author_only_fields"].values())
    assert packet["submission_system_state"]["ready_for_submission"] is False


def test_v5_admin_surfaces_name_the_post_outcome_boundary():
    cover = (ROOT / "manuscript" / "N2_MEE_COVER_LETTER_DRAFT_v5.md").read_text(encoding="utf-8")
    disclosures = (ROOT / "manuscript" / "N2_MEE_DISCLOSURE_DRAFTS_v5.md").read_text(encoding="utf-8")
    assert "explicitly post-outcome descriptive decomposition" in cover
    assert "did not refit the model" in cover
    assert "does not replace the prospective pooled comparator" in disclosures
    assert "causal effects of predictors or species identity" in disclosures
