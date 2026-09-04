from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.build_n2_mee_manuscript_v2 import build_manuscript_text
from scripts.build_n2_mee_review_bundle import build_bundle


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "N2_MEE_SUBMISSION_READINESS_RECEIPT.json"


def test_submission_readiness_receipt_matches_integrated_manuscript():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    text = build_manuscript_text()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert digest == receipt["integrated_manuscript_v2"]["sha256"]
    assert receipt["integrated_manuscript_v2"]["word_count"] == 6398
    assert receipt["integrated_manuscript_v2"]["abstract_numbered_parts"] == 4
    assert receipt["integrated_manuscript_v2"]["abstract_max_words_tested"] == 350
    assert receipt["integrated_manuscript_v2"]["empirical_terminal_values_preserved"] is True


def test_submission_readiness_receipt_matches_deterministic_review_bundle(tmp_path):
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    archive = tmp_path / "review.zip"
    built = build_bundle(archive)
    expected = receipt["anonymous_review_bundle"]
    assert built["sha256"] == expected["sha256"]
    assert built["bytes"] == expected["bytes"]
    assert built["file_count"] == expected["file_count"]
    assert expected["identity_token_scan_passed"] is True
    assert expected["bundle_internal_pytest_conclusion"] == "success"


def test_submission_readiness_receipt_pins_main_workflows_and_artifact():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    main = receipt["main_validation"]
    artifact = receipt["submission_artifact"]
    assert main["head_sha"] == "6af0536ac72d55652e132015af9c6a421373a7b0"
    assert main["regular_test_run_id"] == 33865207343
    assert main["regular_test_conclusion"] == "success"
    assert main["submission_package_run_id"] == 33865207160
    assert main["submission_package_conclusion"] == "success"
    assert artifact["artifact_id"] == 9933679843
    assert artifact["artifact_digest"] == "sha256:7ecedd279f2f0ecb14b26669d01a73a89c0988046f6d6c01d4340d128cbbf721"


def test_submission_readiness_does_not_change_scientific_boundaries():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    boundary = receipt["scientific_boundary"]
    assert boundary == {
        "tawaki_rerun_or_retune": False,
        "bat_rerun_or_retune": False,
        "serengeti_rerun_or_retune": False,
        "gate_e_reopened": False,
        "n2_terminal_summary_promoted_to_n3_state": False,
        "submission_packaging_changes_scientific_endpoint": False,
    }
    readiness = receipt["readiness"]
    assert all(readiness.values())
