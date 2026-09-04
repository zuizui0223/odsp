import json
from pathlib import Path
import zipfile

from scripts.build_n2_mee_review_bundle import (
    FORBIDDEN_IDENTITY_TOKENS,
    build_bundle,
)


ROOT = Path(__file__).resolve().parents[1]


def _read_zip_text(archive: Path, name: str) -> str:
    with zipfile.ZipFile(archive) as zf:
        return zf.read(name).decode("utf-8")


def test_review_bundle_is_deterministic_and_anonymous(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    first_info = build_bundle(first)
    second_info = build_bundle(second)

    assert first_info["sha256"] == second_info["sha256"]
    assert first_info["file_count"] >= 25

    with zipfile.ZipFile(first) as zf:
        names = sorted(zf.namelist())
        assert "README_REVIEW.md" in names
        assert "REVIEW_BUNDLE_MANIFEST.json" in names
        assert "review_evidence/EMPIRICAL_SUMMARY.json" in names
        assert "manuscript/N2_MEE_MANUSCRIPT_DRAFT_v1.md" in names
        assert "scripts/run_n2_serengeti_temporal_partition.py" in names
        assert "scripts/n2_bat_thickness_execute.py" in names
        assert ".git/config" not in names
        for name in names:
            if name.endswith((".py", ".md", ".json", ".toml", "LICENSE")):
                text = zf.read(name).decode("utf-8").lower()
                for token in FORBIDDEN_IDENTITY_TOKENS:
                    assert token not in text, (name, token)


def test_anonymous_empirical_summary_matches_terminal_records(tmp_path):
    archive = tmp_path / "review.zip"
    build_bundle(archive)
    summary = json.loads(_read_zip_text(archive, "review_evidence/EMPIRICAL_SUMMARY.json"))
    bat = json.loads((ROOT / "N2_BAT_THICKNESS_TERMINAL_DECISION.json").read_text())
    serengeti = json.loads((ROOT / "N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json").read_text())

    assert summary["tawaki"]["terminal_category"] == "empirical_gate_d_unavailable"
    assert summary["european_free_tailed_bat"]["terminal_category"] == bat["terminal_category"]
    assert summary["european_free_tailed_bat"]["information_nats_H_Z_given_XY"] == bat["primary"]["information_nats_H_Z_given_XY"]
    assert summary["snapshot_serengeti"]["terminal_category"] == serengeti["terminal_category"]
    assert summary["snapshot_serengeti"]["heldout_site_fold_gains"] == serengeti["heldout_gains"]
    assert summary["n3_state_artifact_included"] is False


def test_review_pyproject_points_to_anonymous_readme(tmp_path):
    archive = tmp_path / "review.zip"
    build_bundle(archive)
    pyproject = _read_zip_text(archive, "pyproject.toml")
    assert 'readme = "README_REVIEW.md"' in pyproject
    assert 'license = {text = "MIT"}' in pyproject
