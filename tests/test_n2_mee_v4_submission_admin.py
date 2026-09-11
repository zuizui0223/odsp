from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TITLE_PAGE = ROOT / "manuscript" / "N2_MEE_TITLE_PAGE_TEMPLATE_v4.md"
COVER = ROOT / "manuscript" / "N2_MEE_COVER_LETTER_DRAFT_v4.md"
DISCLOSURES = ROOT / "manuscript" / "N2_MEE_DISCLOSURE_DRAFTS_v4.md"
CHECKLIST = ROOT / "N2_MEE_STATE_PREDICTION_V4_SUBMISSION_CHECKLIST.json"
POLICY_AUDIT = ROOT / "N2_MEE_SUBMISSION_POLICY_AUDIT_2026-09-12.json"
NEW_TITLE = "State-resolved ecological prediction: from flat suitability to transferable ecological-state distributions"
OLD_TITLE = "Beyond flat niche maps: separating added-axis thickness from transferable ecological organization"


def test_v4_admin_documents_use_state_prediction_title_and_claim():
    title = TITLE_PAGE.read_text(encoding="utf-8")
    cover = COVER.read_text(encoding="utf-8")
    disclosures = DISCLOSURES.read_text(encoding="utf-8")
    assert NEW_TITLE in title
    assert NEW_TITLE in cover
    assert OLD_TITLE not in title
    assert OLD_TITLE not in cover
    assert "P(A|X)" in cover
    assert "27 of 30" in cover
    assert "all 30" in cover
    assert "terminal result remains mixed" in cover
    assert "methodological contribution is **not** a workflow" in cover
    assert "Random forests and multinomial regression are therefore demonstration engines" in cover
    assert "## Data sources" in title
    assert "10.5281/zenodo.10054153" in title
    assert "10.5281/zenodo.10055071" in title
    assert "10.5061/dryad.5pt92" in title
    assert "GPT-5.6 Sol" in title
    assert "universal positive transfer" in disclosures


def test_v4_submission_checklist_preserves_manual_author_gates():
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    assert checklist["manuscript_title"] == NEW_TITLE
    assert checklist["guideline_checked_date"] == "2026-09-12"
    assert checklist["validated_manuscript"]["word_count"] == 5443
    assert checklist["validated_manuscript"]["abstract_word_count"] == 350
    assert checklist["validated_manuscript"]["methodological_gap_is_independent_of_focal_taxon"] is True
    assert checklist["validated_manuscript"]["upstream_prediction_learner_is_exchangeable"] is True
    assert all(checklist["automatic_items"].values())
    assert checklist["desk_screening_positioning"]["new_method_claim_is_not_pipeline_composition"] is True
    assert checklist["desk_screening_positioning"]["residual_editorial_scope_judgment_remains"] is True
    manual = checklist["manual_author_confirmation_required"]
    assert manual
    assert all(value is False for value in manual.values())
    assert "third_party_data_reuse_terms_or_permissions_confirmed_for_all_sources" in manual
    assert checklist["scientific_claim_ceiling"]["bop_terminal_category"] == "empirical_state_prediction_mixed"
    assert checklist["scientific_claim_ceiling"]["mh_terminal_category"] == "empirical_state_prediction_unavailable"
    assert checklist["ready_for_author_metadata_completion"] is True
    assert checklist["ready_for_submission_without_author_metadata_completion"] is False


def test_current_mee_policy_audit_is_editorial_only_and_fail_closed_on_manual_gates():
    audit = json.loads(POLICY_AUDIT.read_text(encoding="utf-8"))
    assert audit["audit_date"] == "2026-09-12"
    fit = audit["journal_fit_checks"]
    assert fit["methodological_gap_is_independent_of_focal_organism"] is True
    assert fit["known_truth_or_benchmark_validation_precedes_empirical_application"] is True
    assert fit["methodological_novelty_is_not_a_workflow_that_merely_links_existing_algorithms"] is True
    assert fit["residual_scope_decision_remains_editorial_judgment"] is True
    status = audit["current_v4_status"]
    assert status["manuscript_scientific_text_modified_by_this_audit"] is False
    assert status["empirical_endpoint_rerun_by_this_audit"] is False
    assert status["frozen_decision_rule_modified_by_this_audit"] is False
    ai = audit["ai_policy_check"]
    assert ai["application_named"] == "OpenAI ChatGPT"
    assert ai["model_version_named"] == "GPT-5.6 Sol"
    reuse = audit["third_party_data_reuse_check"]
    assert reuse["BOP_RODENT"]["reuse_status"].startswith("CC0")
    assert "CC0" in reuse["MH_ANTWERPEN"]["reuse_status"]
    assert reuse["all_source_terms_final_author_confirmation_complete"] is False
    readiness = audit["readiness"]
    assert readiness["scientific_and_technical_submission_package_ready"] is True
    assert readiness["desk_screening_positioning_hardened"] is True
    assert readiness["ready_for_submission_without_manual_author_gates"] is False
