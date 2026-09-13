from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from scripts.build_n2_mee_review_bundle import FORBIDDEN_IDENTITY_TOKENS
from scripts.build_n2_mee_review_bundle_v3 import AI_HEADER
from scripts.build_n2_mee_review_bundle_v5 import build_bundle


def _members(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def test_v5_review_bundle_is_deterministic_and_replaces_v4_submission_surface(tmp_path):
    a = tmp_path / "a.zip"
    b = tmp_path / "b.zip"
    first = build_bundle(a)
    second = build_bundle(b)
    assert first["sha256"] == second["sha256"]
    assert hashlib.sha256(a.read_bytes()).hexdigest() == first["sha256"]

    files = _members(a)
    required = {
        "manuscript/N2_MEE_MANUSCRIPT_DRAFT_v5.md",
        "manuscript/N2_MEE_TABLE1_DRAFT_v5.md",
        "manuscript/N2_MEE_FIGURE_CAPTIONS_DRAFT_v5.md",
        "review_evidence/BOP_SPECIES_BASELINE_DECOMPOSITION.json",
        "N2_MEE_STATE_PREDICTION_V5_CONTRACT.json",
        "odsp/bop_species_baseline.py",
        "tests/test_bop_species_baseline.py",
        "REVIEW_BUNDLE_MANIFEST.json",
    }
    assert required.issubset(files)
    assert "manuscript/N2_MEE_MANUSCRIPT_DRAFT_v4.md" not in files
    assert "BOP_RODENT_SPECIES_BASELINE_AMENDMENT_RECEIPT.json" not in files
    assert "BOP_RODENT_SPECIES_BASELINE_AMENDMENT_CONTRACT.json" not in files


def test_v5_review_evidence_is_sanitized_and_preserves_primary_endpoint(tmp_path):
    path = tmp_path / "review.zip"
    build_bundle(path)
    files = _members(path)
    evidence = json.loads(files["review_evidence/BOP_SPECIES_BASELINE_DECOMPOSITION.json"])
    primary = evidence["primary_endpoint_preserved"]
    assert evidence["post_outcome_amendment"] is True
    assert primary["terminal_category"] == "empirical_state_prediction_mixed"
    assert primary["positive_individual_count"] == 27
    assert primary["eligible_individual_count"] == 30
    assert primary["terminal_decision_recomputed"] is False
    assert primary["terminal_decision_changed"] is False
    assert evidence["model_refit_performed"] is False
    assert evidence["raw_source_data_reaccessed"] is False
    assert evidence["retuning_performed"] is False

    total_counts = sum(
        sum(row["state_counts"].values())
        for row in evidence["species_summary"].values()
    )
    assert total_counts == 154655

    serialized = json.dumps(evidence).lower()
    for forbidden in (
        "workflow_run_id",
        "artifact_id",
        "artifact_digest",
        "source_head_sha",
        "result_json_sha256",
        "runner_pr_number",
    ):
        assert forbidden not in serialized


def test_v5_review_bundle_excludes_identity_and_governance_surfaces(tmp_path):
    path = tmp_path / "review.zip"
    build_bundle(path)
    files = _members(path)
    forbidden_paths = (
        ".github/",
        "forecast_assessment",
        "evaluation_access",
        "evaluation_ledger",
        "trust_dossier",
        "robust_model_selection",
    )
    for name, content in files.items():
        lowered_name = name.lower()
        assert not any(token in lowered_name for token in forbidden_paths), name
        try:
            text = content.decode("utf-8").lower()
        except UnicodeDecodeError:
            continue
        for token in FORBIDDEN_IDENTITY_TOKENS:
            assert token not in text, (name, token)


def test_v5_review_bundle_manifest_and_ai_annotations(tmp_path):
    path = tmp_path / "review.zip"
    built = build_bundle(path)
    files = _members(path)
    manifest = json.loads(files["REVIEW_BUNDLE_MANIFEST.json"])
    assert manifest["schema_version"] == 5
    assert manifest["contains_state_prediction_manuscript_v5"] is True
    assert manifest["contains_post_outcome_bop_decomposition"] is True
    assert manifest["contains_raw_bop_amendment_receipt"] is False
    assert manifest["bop_primary_terminal_reclassified"] is False
    assert manifest["contains_internal_workflow_or_pr_provenance"] is False

    python_files = [name for name in files if name.endswith(".py")]
    assert built["python_file_ai_annotation_count"] == len(python_files)
    for name in python_files:
        assert AI_HEADER.splitlines()[0].encode("utf-8") in files[name]
