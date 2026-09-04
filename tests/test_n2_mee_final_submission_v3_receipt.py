from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.build_n2_mee_manuscript_v3 import build_manuscript_text
from scripts.build_n2_mee_review_bundle_v3 import build_bundle


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "N2_MEE_FINAL_SUBMISSION_V3_RECEIPT.json"


def test_final_submission_v3_receipt_regenerates_manuscript_exactly():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    text = build_manuscript_text()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()

    assert digest == receipt["manuscript_v3"]["sha256"]
    assert receipt["manuscript_v3"]["word_count"] == 6569
    assert receipt["manuscript_v3"]["abstract_word_count"] == 280
    assert receipt["manuscript_v3"]["scientific_claims_changed_from_v2"] is False
    assert receipt["manuscript_v3"]["empirical_endpoints_rerun"] is False


def test_final_submission_v3_receipt_regenerates_anonymous_bundle_exactly(tmp_path):
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    archive = tmp_path / "review-v3.zip"
    built = build_bundle(archive)

    assert built["sha256"] == receipt["anonymous_review_bundle_v3"]["sha256"]
    assert built["bytes"] == receipt["anonymous_review_bundle_v3"]["bytes"]
    assert built["file_count"] == receipt["anonymous_review_bundle_v3"]["file_count"]
    assert built["python_file_ai_annotation_count"] == receipt["anonymous_review_bundle_v3"]["python_file_ai_annotation_count"]


def test_final_submission_v3_receipt_keeps_author_only_items_unresolved():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    checklist = json.loads((ROOT / "N2_MEE_FINAL_SUBMISSION_CHECKLIST.json").read_text(encoding="utf-8"))

    assert receipt["readiness"]["technical_submission_package_ready"] is True
    assert receipt["readiness"]["journal_policy_drafts_ready"] is True
    assert receipt["readiness"]["author_metadata_completion_required"] is True
    assert receipt["readiness"]["ready_for_submission_without_author_metadata_completion"] is False
    assert not any(checklist["manual_author_confirmation_required"].values())


def test_final_submission_v3_scientific_boundaries_remain_closed():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    boundary = receipt["scientific_boundary"]

    assert boundary["tawaki_rerun_or_retune"] is False
    assert boundary["bat_rerun_or_retune"] is False
    assert boundary["serengeti_rerun_or_retune"] is False
    assert boundary["gate_e_reopened"] is False
    assert boundary["n2_terminal_summary_promoted_to_n3_state"] is False
    assert boundary["packaging_or_policy_changes_scientific_endpoint"] is False
