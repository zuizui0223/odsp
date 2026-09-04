from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.build_n2_mee_manuscript_v3 import build_manuscript_text


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


def test_final_submission_v3_receipt_pins_historical_bundle_metadata():
    """Keep the validated artifact immutable when ODSP evolves after submission v3."""

    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    bundle = receipt["anonymous_review_bundle_v3"]
    assert bundle["sha256"] == "1cf25b609527cdba5a210416148806b1e2c50934dd8d386d49f48b2df77a29dd"
    assert bundle["bytes"] == 109617
    assert bundle["file_count"] == 45
    assert bundle["python_file_ai_annotation_count"] == 33
    assert bundle["identity_scan_passed"] is True
    assert bundle["bundle_internal_pytest_conclusion"] == "success"


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
