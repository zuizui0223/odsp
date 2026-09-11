from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_MEE_REVIEW_DOCX_RENDER_CONTRACT.json"


def test_review_docx_render_contract_is_format_only():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = contract["source_rule"]
    assert source["source_is_output_of_existing_v4_manuscript_builder"] is True
    assert source["scientific_v4_source_is_not_modified_by_rendering"] is True
    assert source["empirical_endpoints_are_not_rerun"] is True
    assert source["frozen_decision_rules_are_not_modified"] is True
    assert source["n2_to_n3_boundary_is_not_modified"] is True


def test_review_docx_render_contract_matches_mee_mechanical_requirements():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    render = contract["render_requirements"]
    assert render["single_column"] is True
    assert render["double_line_spacing"] is True
    assert render["continuous_line_numbering"] is True
    assert render["page_numbering"] is True
    assert render["anonymous_main_document"] is True
    assert render["title_page_not_embedded"] is True


def test_review_docx_render_does_not_overclaim_submission_readiness():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    boundary = contract["claim_boundary"]
    assert boundary["render_validation_changes_scientific_evidence"] is False
    assert boundary["render_validation_proves_journal_acceptance"] is False
    assert boundary["render_validation_replaces_final_author_visual_check"] is False
    assert boundary["render_validation_completes_author_metadata"] is False
    assert boundary["render_validation_confirms_all_third_party_permissions"] is False
