from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from scripts.build_n2_mee_review_bundle import FORBIDDEN_IDENTITY_TOKENS
from scripts.build_n2_mee_review_bundle_v4 import AI_HEADER, build_bundle


def _members(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def test_v4_review_bundle_is_deterministic_and_state_prediction_centered(tmp_path):
    a = tmp_path / "a.zip"
    b = tmp_path / "b.zip"
    first = build_bundle(a)
    second = build_bundle(b)
    assert first["sha256"] == second["sha256"]
    assert hashlib.sha256(a.read_bytes()).hexdigest() == first["sha256"]
    assert first["file_count"] >= 50

    files = _members(a)
    required = {
        "manuscript/N2_MEE_MANUSCRIPT_DRAFT_v4.md",
        "manuscript/N2_MEE_TABLE1_DRAFT_v4.md",
        "manuscript/N2_MEE_FIGURE_CAPTIONS_DRAFT_v4.md",
        "review_evidence/STATE_PREDICTION_SUMMARY.json",
        "STATE_RESOLVED_PREDICTION_CONTRACT.json",
        "MH_ANTWERPEN_STATE_PREDICTION_CONTRACT.json",
        "BOP_RODENT_STATE_PREDICTION_CONTRACT.json",
        "odsp/state_prediction.py",
        "odsp/state_prediction_benchmark.py",
        "odsp/covariate_state_prediction.py",
        "odsp/mh_antwerpen_prediction.py",
        "odsp/bop_rodent_prediction.py",
        "tests/test_state_prediction.py",
        "tests/test_covariate_state_prediction.py",
        "tests/test_mh_antwerpen_state_prediction.py",
        "tests/test_bop_rodent_state_prediction.py",
        "REVIEW_BUNDLE_MANIFEST.json",
    }
    assert required.issubset(files)
    assert "manuscript/N2_MEE_MANUSCRIPT_DRAFT_v3.md" not in files
    assert "MH_ANTWERPEN_STATE_PREDICTION_RECEIPT.json" not in files
    assert "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json" not in files


def test_v4_review_bundle_excludes_identity_and_internal_provenance(tmp_path):
    archive_path = tmp_path / "review.zip"
    build_bundle(archive_path)
    files = _members(archive_path)
    for name, content in files.items():
        try:
            text = content.decode("utf-8").lower()
        except UnicodeDecodeError:
            continue
        for token in FORBIDDEN_IDENTITY_TOKENS:
            assert token not in text, (name, token)

    manifest = json.loads(files["REVIEW_BUNDLE_MANIFEST.json"])
    assert manifest["contains_git_history"] is False
    assert manifest["contains_author_identity"] is False
    assert manifest["contains_internal_workflow_or_pr_provenance"] is False
    assert manifest["contains_raw_terminal_receipts_with_internal_provenance"] is False
    assert manifest["contains_state_prediction_manuscript_v4"] is True


def test_v4_review_bundle_has_ai_annotations_and_sanitized_evidence(tmp_path):
    archive_path = tmp_path / "review.zip"
    built = build_bundle(archive_path)
    files = _members(archive_path)
    python_files = [name for name in files if name.endswith(".py")]
    assert built["python_file_ai_annotation_count"] == len(python_files)
    for name in python_files:
        assert AI_HEADER.splitlines()[0].encode("utf-8") in files[name]

    summary = json.loads(files["review_evidence/STATE_PREDICTION_SUMMARY.json"])
    endpoints = summary["prospective_state_prediction_endpoints"]
    assert endpoints[0]["terminal_category"] == "empirical_state_prediction_unavailable"
    assert endpoints[1]["primary_random_forest"]["terminal_category"] == "empirical_state_prediction_mixed"
    assert endpoints[1]["primary_random_forest"]["positive_gain_individuals"] == 27
    assert endpoints[1]["primary_random_forest"]["positive_brier_improvement_individuals"] == 30
    serialized = json.dumps(summary).lower()
    assert "workflow_run_id" not in serialized
    assert "runner_pr_number" not in serialized
