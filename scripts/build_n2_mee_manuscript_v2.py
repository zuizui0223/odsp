#!/usr/bin/env python3
"""Build manuscript v2 by integrating validated generality evidence into v1.

The v1 manuscript remains the frozen first full draft. This builder performs only
textual integration: it inserts the already validated generality Methods, Results
and Discussion text, updates the abstract and peer-review packaging wording, and
renumbers downstream headings deterministically. It does not rerun or alter any
empirical endpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "N2_MEE_MANUSCRIPT_DRAFT_v1.md"
GENERALITY = ROOT / "manuscript" / "N2_MEE_GENERALITY_SECTION_v1.md"
SUMMARY = ROOT / "N2_GENERALITY_BENCHMARK_SUMMARY.json"


def _section(text: str, heading: str, next_heading: str | None) -> str:
    start = text.index(heading) + len(heading)
    end = len(text) if next_heading is None else text.index(next_heading, start)
    return text[start:end].strip()


def _replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected exactly one occurrence, found {count}: {old[:80]!r}")
    return text.replace(old, new, 1)


def build_manuscript_text() -> str:
    text = SOURCE.read_text(encoding="utf-8")
    insert = GENERALITY.read_text(encoding="utf-8")
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    result = summary["result"]
    if result["check_count"] != 1873 or result["failed_count"] != 0:
        raise ValueError("generality summary does not match the validated benchmark")

    abstract2_old = (
        "2. We introduce an information-theoretic framework for non-negative ecological support tensors. "
        "Added-axis thickness is measured by conditional information `H(A|B)` and its effective state count "
        "`exp(H(A|B))` after a declared base state `B` is known. Fitted organization is kept distinct from "
        "held-out transferability, which is scored as `E[log P_model(A|B) - log P_model(A)]` against an explicit "
        "marginal comparator. Prospectively independent groups are scored separately, with cross-fitting when "
        "each held-out group requires its own training support. Analytic known-truth families and concealed "
        "finite-observation benchmarks test thick-but-unorganized, stable-generalizing and shifted-non-generalizing "
        "states before empirical application."
    )
    abstract2_new = abstract2_old + (
        " Axis-agnostic invariance and composition were then stress-tested across 128 random two- to six-dimensional "
        "support tensors and additional multi-axis systems before empirical interpretation."
    )
    text = _replace_once(text, abstract2_old, abstract2_new)

    abstract4_old = (
        "4. Projection loss therefore has at least two empirically separable components: how much added-axis state "
        "remains after projection and whether the organization of that state transfers to independent observations. "
        "Treating estimability, thickness, organization and transferability as separate inferential layers prevents "
        "descriptively rich multidimensional fits from being promoted automatically to generalizable ecological "
        "structure. The framework is axis-agnostic, while biological interpretation remains explicitly tied to the "
        "observation semantics of each added dimension."
    )
    abstract4_new = abstract4_old + (
        " Its representation-level genericity is supported over finite discrete support tensors, while biological "
        "generality remains bounded by the semantics and independent validation design of each application."
    )
    text = _replace_once(text, abstract4_old, abstract4_new)

    text = _replace_once(
        text,
        "the code, machine-readable analysis contracts, synthetic benchmarks and terminal result receipts will be provided in an anonymized review archive.",
        "the code, machine-readable analysis contracts, synthetic and generality benchmarks, terminal scientific summaries and the integrated manuscript v2 will be provided in a deterministic anonymized review archive.",
    )

    intro_old = (
        "We validate this hierarchy before empirical application. Analytic known-truth families were constructed so "
        "that support can be thick but unorganized, stably organized, or organized in the fitted sample but shifted "
        "in held-out data. Concealed finite-observation benchmarks then test whether the intended quantities can be "
        "recovered under sampling. Finally, we apply prospectively frozen versions of the framework to three public "
        "empirical systems with different added-axis semantics and observation architectures."
    )
    intro_new = (
        "We validate this hierarchy before empirical application. Analytic known-truth families were constructed so "
        "that support can be thick but unorganized, stably organized, or organized in the fitted sample but shifted "
        "in held-out data. Concealed finite-observation benchmarks test finite-sampling recovery, while a separate "
        "axis-agnostic property benchmark tests representation invariance, information identities and multi-axis "
        "composition across high-dimensional support tensors. Finally, we apply prospectively frozen versions of the "
        "framework to three public empirical systems with different added-axis semantics and observation architectures."
    )
    text = _replace_once(text, intro_old, intro_new)

    methods = _section(
        insert,
        "## Methods insert — Generality and invariance validation",
        "## Results insert — The evidence core was invariant across high-dimensional representations",
    )
    results = _section(
        insert,
        "## Results insert — The evidence core was invariant across high-dimensional representations",
        "## Discussion insert — What kind of generality is supported",
    )
    discussion = _section(
        insert,
        "## Discussion insert — What kind of generality is supported",
        None,
    )

    # Renumber existing Methods headings from the bottom up, then insert 2.6.
    for old, new in (("## 2.9 ", "## 2.10 "), ("## 2.8 ", "## 2.9 "), ("## 2.7 ", "## 2.8 "), ("## 2.6 ", "## 2.7 ")):
        text = text.replace(old, new)
    text = _replace_once(
        text,
        "## 2.7 Observation semantics and prospective empirical gates",
        "## 2.6 Generality and invariance validation\n\n" + methods + "\n\n## 2.7 Observation semantics and prospective empirical gates",
    )

    # Renumber Results after 3.1, then insert generality as 3.2.
    for old, new in (("## 3.7 ", "## 3.8 "), ("## 3.6 ", "## 3.7 "), ("## 3.5 ", "## 3.6 "), ("## 3.4 ", "## 3.5 "), ("## 3.3 ", "## 3.4 "), ("## 3.2 ", "## 3.3 ")):
        text = text.replace(old, new)
    text = _replace_once(
        text,
        "## 3.3 The Tawaki vertical endpoint was prospectively unestimable",
        "## 3.2 The evidence core was invariant across high-dimensional representations\n\n" + results + "\n\n## 3.3 The Tawaki vertical endpoint was prospectively unestimable",
    )

    # Insert generality after the axis-semantics discussion and renumber later sections.
    text = text.replace("## 4.6 Projection-aware inference should end before downstream state promotion", "## 4.7 Projection-aware inference should end before downstream state promotion")
    text = text.replace("## 4.5 Cross-system differences demonstrate states, not mechanisms", "## 4.6 Cross-system differences demonstrate states, not mechanisms")
    text = _replace_once(
        text,
        "## 4.6 Cross-system differences demonstrate states, not mechanisms",
        "## 4.5 What kind of generality is supported\n\n" + discussion + "\n\n## 4.6 Cross-system differences demonstrate states, not mechanisms",
    )

    text = text.replace("**Review draft:** anonymized working version", "**Review draft:** anonymized integrated version 2")
    text = text.rstrip() + "\n"
    return text


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build(output: Path, manifest_path: Path | None = None) -> dict[str, object]:
    text = build_manuscript_text()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "role": "integrated_anonymous_mee_manuscript_v2",
        "source_manuscript": SOURCE.relative_to(ROOT).as_posix(),
        "generality_insert": GENERALITY.relative_to(ROOT).as_posix(),
        "generality_summary": SUMMARY.relative_to(ROOT).as_posix(),
        "word_count": _word_count(text),
        "sha256": _sha256_text(text),
        "output": output.name,
        "empirical_endpoints_rerun": False,
    }
    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("manuscript/N2_MEE_MANUSCRIPT_DRAFT_v2.md"))
    parser.add_argument("--manifest", type=Path, default=Path("manuscript/N2_MEE_MANUSCRIPT_DRAFT_v2.manifest.json"))
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.manifest), sort_keys=True))


if __name__ == "__main__":
    main()
