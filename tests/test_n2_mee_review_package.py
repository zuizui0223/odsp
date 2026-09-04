from __future__ import annotations

import json
from pathlib import Path
import zipfile

from scripts.build_n2_mee_review_bundle import FORBIDDEN_IDENTITY_TOKENS, build_bundle


ROOT = Path(__file__).resolve().parents[1]


def _read_zip_text(archive: Path, name: str) -> str:
    with zipfile.ZipFile(archive) as zf:
        return zf.read(name).decode("utf-8")


def test_review_bundle_is_deterministic_anonymous_and_contains_v2(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    first_info = build_bundle(first)
    second_info = build_bundle(second)
    assert first_info["sha256"] == second_info["sha256"]
    assert first_info["file_count"] >= 30

    with zipfile.ZipFile(first) as zf:
        names = sorted(zf.namelist())
        required = {
            "README_REVIEW.md",
            "REVIEW_BUNDLE_MANIFEST.json",
            "review_evidence/EMPIRICAL_SUMMARY.json",
            "review_evidence/GENERALITY_SUMMARY.json",
            "manuscript/N2_MEE_MANUSCRIPT_DRAFT_v2.md",
            "odsp/added_axis_evidence.py",
            "odsp/generality_benchmark.py",
            "tests/test_n2_generality_benchmark.py",
            "tests/test_n2_extended_information_laws.py",
            "scripts/run_n2_serengeti_temporal_partition.py",
            "scripts/n2_bat_thickness_execute.py",
        }
        assert required.issubset(names)
        assert ".git/config" not in names
        for name in names:
            if name.endswith((".py", ".md", ".json", ".toml", "LICENSE")):
                text = zf.read(name).decode("utf-8").lower()
                for token in FORBIDDEN_IDENTITY_TOKENS:
                    assert token not in text, (name, token)


def test_review_bundle_empirical_and_generality_summaries_match_closed_sources(tmp_path):
    archive = tmp_path / "review.zip"
    build_bundle(archive)
    empirical = json.loads(_read_zip_text(archive, "review_evidence/EMPIRICAL_SUMMARY.json"))
    generic = json.loads(_read_zip_text(archive, "review_evidence/GENERALITY_SUMMARY.json"))
    bat = json.loads((ROOT / "N2_BAT_THICKNESS_TERMINAL_DECISION.json").read_text())
    serengeti = json.loads((ROOT / "N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json").read_text())
    generality = json.loads((ROOT / "N2_GENERALITY_BENCHMARK_SUMMARY.json").read_text())

    assert empirical["tawaki"]["terminal_category"] == "empirical_gate_d_unavailable"
    assert empirical["european_free_tailed_bat"]["terminal_category"] == bat["terminal_category"]
    assert empirical["european_free_tailed_bat"]["information_nats_H_Z_given_XY"] == bat["primary"]["information_nats_H_Z_given_XY"]
    assert empirical["snapshot_serengeti"]["terminal_category"] == serengeti["terminal_category"]
    assert empirical["snapshot_serengeti"]["heldout_site_fold_gains"] == serengeti["heldout_gains"]
    assert empirical["n3_state_artifact_included"] is False

    assert generic["result"] == generality["result"]
    assert generic["settings"] == generality["settings"]
    assert generic["claim_boundary"]["universal_biological_outcomes_supported"] is False
    assert generic["claim_boundary"]["causal_interpretation_supported"] is False


def test_review_bundle_manifest_is_fail_closed_on_identity_and_internal_provenance(tmp_path):
    archive = tmp_path / "review.zip"
    build_bundle(archive)
    manifest = json.loads(_read_zip_text(archive, "REVIEW_BUNDLE_MANIFEST.json"))
    assert manifest["bundle_role"] == "double_anonymous_peer_review"
    assert manifest["contains_git_history"] is False
    assert manifest["contains_author_identity"] is False
    assert manifest["contains_internal_workflow_or_pr_provenance"] is False
    assert manifest["contains_integrated_manuscript_v2"] is True
    assert manifest["contains_generality_validation"] is True


def test_review_pyproject_points_to_anonymous_readme(tmp_path):
    archive = tmp_path / "review.zip"
    build_bundle(archive)
    pyproject = _read_zip_text(archive, "pyproject.toml")
    assert 'readme = "README_REVIEW.md"' in pyproject
    assert 'license = {text = "MIT"}' in pyproject
