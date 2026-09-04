#!/usr/bin/env python3
"""Build MEE manuscript v3 by adding ethics and generative-AI disclosures to v2.

The validated scientific content and all closed empirical endpoints are inherited
unchanged from manuscript v2. This builder only adds submission-policy statements
for archived-data ethics and generative-AI assistance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts.build_n2_mee_manuscript_v2 import build_manuscript_text as build_v2_text


ROOT = Path(__file__).resolve().parents[1]

ETHICS_TEXT = """## 2.11 Ethics and use of archived data

This study did not conduct new animal capture, handling, manipulation or field sampling. It reanalyses publicly archived ecological datasets collected by the original data providers. Ethical approvals, permits and animal-welfare procedures governing the original data collection remain those reported by the corresponding source studies and data archives. No new intervention involving animals or human participants was conducted for the present analysis.
"""

AI_TEXT = """## 2.12 Generative-AI assistance

OpenAI ChatGPT (GPT-5.6 Sol) was used as a development assistant for language editing, code drafting and revision, test scaffolding, documentation and repository organization. The authors defined the scientific questions, prospective analysis contracts, estimands, frozen decision rules and claim boundaries; executed and validated the analyses; inspected outputs and failures; reviewed the submitted code and text; and retained full responsibility for interpretation and submission. Because development was iterative and exact line-level provenance is not recoverable for all AI-assisted code, submitted review-code files are conservatively annotated at whole-file level when AI assistance may have contributed to their drafting or revision.
"""


def build_manuscript_text() -> str:
    text = build_v2_text()
    marker = "# 3. Results\n"
    if text.count(marker) != 1:
        raise ValueError("expected exactly one Results heading in manuscript v2")
    if "## 2.11 Ethics and use of archived data" in text or "## 2.12 Generative-AI assistance" in text:
        raise ValueError("v2 source already contains v3 disclosure sections")
    text = text.replace(marker, ETHICS_TEXT + "\n" + AI_TEXT + "\n" + marker, 1)
    text = text.replace("**Review draft:** anonymized integrated version 2", "**Review draft:** anonymized policy-compliant version 3", 1)
    return text.rstrip() + "\n"


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _abstract_word_count(text: str) -> int:
    start = text.index("## Abstract") + len("## Abstract")
    end = text.index("**Keywords:**", start)
    return _word_count(text[start:end])


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build(output: Path, manifest_path: Path | None = None) -> dict[str, object]:
    text = build_manuscript_text()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "role": "integrated_anonymous_mee_manuscript_v3_policy_compliant",
        "source": "scripts/build_n2_mee_manuscript_v2.py",
        "word_count": _word_count(text),
        "abstract_word_count": _abstract_word_count(text),
        "sha256": _sha256_text(text),
        "ethics_archived_data_statement_present": True,
        "generative_ai_methods_disclosure_present": True,
        "empirical_endpoints_rerun": False,
        "scientific_claims_changed": False,
        "output": output.name,
    }
    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("manuscript/N2_MEE_MANUSCRIPT_DRAFT_v3.md"))
    parser.add_argument("--manifest", type=Path, default=Path("manuscript/N2_MEE_MANUSCRIPT_DRAFT_v3.manifest.json"))
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.manifest), sort_keys=True))


if __name__ == "__main__":
    main()
