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

V2_ABSTRACT = """1. Ecological niches are commonly mapped in two dimensions although organismal support can also vary with height, depth, time and other state axes. Adding dimensions to a fitted model does not by itself show that hidden state is estimable, organized or independently generalizable. We therefore separate projection-loss magnitude from the transferability of the organization that produces it.

2. For non-negative support tensors, we quantify added-axis thickness with `H(A|B)` and `exp[H(A|B)]`, fitted organization with mutual information, and held-out transferability with `E[log P_model(A|B)-log P_model(A)]` against the model marginal. Independent groups are scored separately and cross-fitted where required. Known-truth tests distinguish thick-unorganized, stable-generalizing and shifted-non-generalizing states. Axis-agnostic properties were additionally tested across 128 random two- to six-dimensional tensors and multi-axis systems: all 1,873 obligations passed, with maximum absolute error `2.49×10^-14`.

3. Three prospectively bounded empirical applications occupied different states. A Tawaki GPS-dive endpoint was structurally unavailable before biological thickness was opened. European free-tailed bat tracking was vertically thick after horizontal location was known (`H(Z|X,Y)=1.392` nats; 4.02 effective states), but both sealed-individual gains were negative. Snapshot Serengeti detections were temporally broad within sites (`H(T|Site)=1.640`; 5.15 of six effective states), species-partitioned (`I(Species;T|Site)=0.224`; permutation `p=0.005`), and generalizing, with positive gains in all three held-out site folds.

4. Projection loss therefore has separable components: how much added-axis state remains and whether its organization transfers independently. The inferential machinery is axis-agnostic over validated finite discrete support tensors and portable across heterogeneous observation architectures, while biological interpretation remains bounded by each axis's observation semantics and validation design."""


def _section(text: str, heading: str, next_heading: str | None) -> str:
    start = text.index(heading) + len(heading)
    end = len(text) if next_heading is None else text.index(next_heading, start)
    return text[start:end].strip()


def _replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected exactly one occurrence, found {count}: {old[:80]!r}")
    return text.replace(old, new, 1)


def _replace_abstract(text: str) -> str:
    start_marker = "## Abstract\n\n"
    end_marker = "\n\n**Keywords:**"
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise ValueError("manuscript abstract markers are not unique")
    prefix, rest = text.split(start_marker, 1)
    _, suffix = rest.split(end_marker, 1)
    return prefix + start_marker + V2_ABSTRACT + end_marker + suffix


def build_manuscript_text() -> str:
    text = SOURCE.read_text(encoding="utf-8")
    insert = GENERALITY.read_text(encoding="utf-8")
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    result = summary["result"]
    if result["check_count"] != 1873 or result["failed_count"] != 0:
        raise ValueError("generality summary does not match the validated benchmark")

    text = _replace_abstract(text)

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

    for old, new in (("## 2.9 ", "## 2.10 "), ("## 2.8 ", "## 2.9 "), ("## 2.7 ", "## 2.8 "), ("## 2.6 ", "## 2.7 ")):
        text = text.replace(old, new)
    text = _replace_once(
        text,
        "## 2.7 Observation semantics and prospective empirical gates",
        "## 2.6 Generality and invariance validation\n\n" + methods + "\n\n## 2.7 Observation semantics and prospective empirical gates",
    )

    for old, new in (("## 3.7 ", "## 3.8 "), ("## 3.6 ", "## 3.7 "), ("## 3.5 ", "## 3.6 "), ("## 3.4 ", "## 3.5 "), ("## 3.3 ", "## 3.4 "), ("## 3.2 ", "## 3.3 ")):
        text = text.replace(old, new)
    text = _replace_once(
        text,
        "## 3.3 The Tawaki vertical endpoint was prospectively unestimable",
        "## 3.2 The evidence core was invariant across high-dimensional representations\n\n" + results + "\n\n## 3.3 The Tawaki vertical endpoint was prospectively unestimable",
    )

    text = text.replace("## 4.6 Projection-aware inference should end before downstream state promotion", "## 4.7 Projection-aware inference should end before downstream state promotion")
    text = text.replace("## 4.5 Cross-system differences demonstrate states, not mechanisms", "## 4.6 Cross-system differences demonstrate states, not mechanisms")
    text = _replace_once(
        text,
        "## 4.6 Cross-system differences demonstrate states, not mechanisms",
        "## 4.5 What kind of generality is supported\n\n" + discussion + "\n\n## 4.6 Cross-system differences demonstrate states, not mechanisms",
    )

    text = text.replace("**Review draft:** anonymized working version", "**Review draft:** anonymized integrated version 2")
    return text.rstrip() + "\n"


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
