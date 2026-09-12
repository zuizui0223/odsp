from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_n2_mee_submission_handoff import build_packet  # noqa: E402

PACKET = ROOT / "N2_MEE_SUBMISSION_HANDOFF_PACKET.json"
CHECKLIST = ROOT / "N2_MEE_STATE_PREDICTION_V4_SUBMISSION_CHECKLIST.json"


def test_canonical_handoff_is_exact_builder_output():
    canonical = json.loads(PACKET.read_text(encoding="utf-8"))
    assert build_packet() == canonical


def test_copy_ready_nonpersonal_metadata_is_complete_and_bounded():
    packet = build_packet()
    assert packet["journal"] == "Methods in Ecology and Evolution"
    assert packet["article_type"] == "Research Article"
    assert packet["title"].startswith("State-resolved ecological prediction:")
    assert packet["running_headline"] == "State-resolved ecological prediction"
    assert packet["abstract_word_count"] == 350
    assert packet["abstract"].startswith("1. Ecological prediction")
    assert packet["abstract"].count("\n\n") == 3
    assert len(packet["keywords"]) == 8
    assert packet["scientific_terminal_states"]["MH_ANTWERPEN"] == "empirical_state_prediction_unavailable"
    assert packet["scientific_terminal_states"]["BOP_RODENT"] == "empirical_state_prediction_mixed"
    assert packet["submission_system_state"]["nonpersonal_metadata_packet_ready"] is True
    assert packet["submission_system_state"]["metadata_entered_in_submission_system"] is False
    assert packet["submission_system_state"]["ready_for_submission"] is False


def test_author_only_fields_remain_uninferred_and_submission_remains_blocked():
    packet = build_packet()
    fields = packet["author_only_fields"]
    for key in (
        "authors_and_order",
        "affiliations_and_addresses",
        "corresponding_author_contact",
        "credit_roles",
        "named_ai_code_accountable_author",
        "acknowledgements",
        "funding",
        "conflict_of_interest",
    ):
        assert fields[key] is None
    for key, value in fields.items():
        if key not in {
            "authors_and_order",
            "affiliations_and_addresses",
            "corresponding_author_contact",
            "credit_roles",
            "named_ai_code_accountable_author",
            "acknowledgements",
            "funding",
            "conflict_of_interest",
        }:
            assert value is False


def test_checklist_separates_automated_render_from_final_author_approval():
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    assert checklist["schema_version"] == 3
    auto = checklist["automatic_items"]
    assert auto["anonymous_review_docx_single_column_double_spaced_line_numbered_and_page_numbered"] is True
    assert auto["anonymous_review_docx_structural_validation_passed"] is True
    assert auto["anonymous_review_docx_25_page_development_visual_qa_passed"] is True
    assert auto["submission_handoff_packet_generated_from_validated_v4_text"] is True
    manual = checklist["manual_author_confirmation_required"]
    assert manual["submission_system_metadata_entered"] is False
    assert manual["final_author_visual_approval_of_exact_submission_files"] is False
    assert all(value is False for value in manual.values())


def test_handoff_is_administrative_only():
    packet = build_packet()
    assert packet["scientific_source_modified"] is False
    assert packet["empirical_endpoint_rerun"] is False
    assert packet["frozen_decision_rule_modified"] is False
    assert packet["n2_to_n3_promoted"] is False
