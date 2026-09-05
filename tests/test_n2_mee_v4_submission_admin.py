from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TITLE_PAGE = ROOT / "manuscript" / "N2_MEE_TITLE_PAGE_TEMPLATE_v4.md"
COVER = ROOT / "manuscript" / "N2_MEE_COVER_LETTER_DRAFT_v4.md"
DISCLOSURES = ROOT / "manuscript" / "N2_MEE_DISCLOSURE_DRAFTS_v4.md"
CHECKLIST = ROOT / "N2_MEE_STATE_PREDICTION_V4_SUBMISSION_CHECKLIST.json"
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
    assert "10.5281/zenodo.10054153" in title
    assert "10.5281/zenodo.10055071" in title
    assert "universal positive transfer" in disclosures


def test_v4_submission_checklist_preserves_manual_author_gates():
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    assert checklist["manuscript_title"] == NEW_TITLE
    assert checklist["validated_manuscript"]["word_count"] == 5443
    assert checklist["validated_manuscript"]["abstract_word_count"] == 350
    assert all(checklist["automatic_items"].values())
    manual = checklist["manual_author_confirmation_required"]
    assert manual
    assert all(value is False for value in manual.values())
    assert checklist["scientific_claim_ceiling"]["bop_terminal_category"] == "empirical_state_prediction_mixed"
    assert checklist["scientific_claim_ceiling"]["mh_terminal_category"] == "empirical_state_prediction_unavailable"
    assert checklist["ready_for_author_metadata_completion"] is True
    assert checklist["ready_for_submission_without_author_metadata_completion"] is False
