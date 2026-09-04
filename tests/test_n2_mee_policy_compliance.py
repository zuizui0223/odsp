from __future__ import annotations

import json
from pathlib import Path
import re
import zipfile

from scripts.build_n2_mee_manuscript_v3 import build_manuscript_text
from scripts.build_n2_mee_review_bundle_v3 import AI_HEADER, FORBIDDEN_IDENTITY_TOKENS, build_bundle


ROOT = Path(__file__).resolve().parents[1]


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _abstract(text: str) -> str:
    start = text.index("## Abstract") + len("## Abstract")
    end = text.index("**Keywords:**", start)
    return text[start:end]


def test_policy_manuscript_v3_keeps_science_and_adds_required_disclosures():
    text = build_manuscript_text()
    abstract = _abstract(text)

    assert re.findall(r"(?m)^([1-4])\. ", abstract) == ["1", "2", "3", "4"]
    assert _word_count(abstract) <= 350
    assert _word_count(text) <= 8000
    assert "## 2.11 Ethics and use of archived data" in text
    assert "## 2.12 Generative-AI assistance" in text
    assert "OpenAI ChatGPT (GPT-5.6 Sol)" in text

    # Closed empirical values remain verbatim in the integrated policy version.
    for value in (
        "1.3918623004770097",
        "4.022333876564191",
        "-0.43541033813280833",
        "-0.021938657402345435",
        "1.6396235816361795",
        "5.153229376935854",
        "0.22427598739601606",
        "0.0572411993741857",
        "0.045158861333215006",
        "0.04514355468571751",
    ):
        assert value in text


def test_review_bundle_v3_is_deterministic_anonymous_and_ai_annotated(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    a = build_bundle(first)
    b = build_bundle(second)

    assert a["sha256"] == b["sha256"]
    assert a["python_file_ai_annotation_count"] >= 20

    with zipfile.ZipFile(first) as archive:
        names = archive.namelist()
        assert "manuscript/N2_MEE_MANUSCRIPT_DRAFT_v3.md" in names
        assert "manuscript/N2_MEE_MANUSCRIPT_DRAFT_v2.md" not in names
        assert "AI_ASSISTANCE_DISCLOSURE.md" in names
        assert "manuscript/N2_MEE_TITLE_PAGE_TEMPLATE.md" not in names
        assert "manuscript/N2_MEE_COVER_LETTER_DRAFT.md" not in names

        manifest = json.loads(archive.read("REVIEW_BUNDLE_MANIFEST.json").decode("utf-8"))
        assert manifest["schema_version"] == 3
        assert manifest["contains_generative_ai_disclosure"] is True
        assert manifest["contains_archived_data_ethics_statement"] is True
        assert manifest["python_file_ai_annotation_mode"] == "whole_file_conservative"
        assert manifest["python_file_ai_annotation_count"] == a["python_file_ai_annotation_count"]

        for name in names:
            if name.endswith(".py"):
                text = archive.read(name).decode("utf-8")
                assert "Generative-AI assistance disclosure:" in text
            if name.endswith((".py", ".md", ".json", ".toml")) or name == "LICENSE":
                lower = archive.read(name).decode("utf-8").lower()
                for token in FORBIDDEN_IDENTITY_TOKENS:
                    assert token not in lower, (name, token)


def test_final_submission_admin_files_are_explicitly_separate_and_unconfirmed():
    checklist = json.loads((ROOT / "N2_MEE_FINAL_SUBMISSION_CHECKLIST.json").read_text(encoding="utf-8"))
    assert all(checklist["automatic_items"].values())
    assert not any(checklist["manual_author_confirmation_required"].values())
    assert checklist["ready_for_author_metadata_completion"] is True
    assert checklist["ready_for_submission_without_author_metadata_completion"] is False

    title_page = (ROOT / "manuscript" / "N2_MEE_TITLE_PAGE_TEMPLATE.md").read_text(encoding="utf-8")
    assert "Supplemental Document Not for Review" in title_page
    running = re.search(r"## Running headline\n\n\*\*(.+?)\*\*", title_page).group(1)
    assert len(running) <= 45
    assert "[AUTHOR 1 FULL NAME]" in title_page
    assert "[CORRESPONDING AUTHOR EMAIL]" in title_page

    cover = (ROOT / "manuscript" / "N2_MEE_COVER_LETTER_DRAFT.md").read_text(encoding="utf-8")
    assert "[AUTHOR CONFIRMATION REQUIRED" in cover
    assert "1,873" in cover
    assert "2.49 × 10⁻14" in cover
