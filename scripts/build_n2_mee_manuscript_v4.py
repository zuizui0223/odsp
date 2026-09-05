#!/usr/bin/env python3
"""Build the submission-facing state-prediction manuscript v4 from its static draft.

The source draft is retained as an editable scientific text. This builder makes only
small deterministic submission edits: it compresses the numbered abstract below the
350-word ceiling, makes the no-retuning statement explicit, normalizes one verified
bibliographic entry, and writes a manifest. It does not alter any empirical numeric
result or rerun an endpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "N2_MEE_MANUSCRIPT_DRAFT_v4.md"


def _replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected exactly one occurrence, found {count}: {old!r}")
    return text.replace(old, new, 1)


def build_manuscript_text() -> str:
    text = SOURCE.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        "Yet organisms can occupy different height, depth, time, phenological or behavioural states under the same mapped conditions.",
        "Organisms can occupy height, depth, time or behavioural states under the same mapped conditions.",
    )
    text = _replace_once(
        text,
        "The empirical prediction workflows verify source checksums, run contract and synthetic implementation tests before public outcome access, execute only the frozen model settings, validate the result schema and record whether retuning occurred.",
        "The empirical prediction workflows verify source checksums, run contract and synthetic implementation tests before public outcome access, execute only the frozen model settings, validate the result schema and record whether retuning occurred. No retuning was performed after outcome access in either executed prospective endpoint.",
    )
    text = _replace_once(
        text,
        "Milotic, T. et al. (2020). Dataset description associated with the MH_ANTWERPEN bird-tracking project. *ZooKeys*, 947. https://doi.org/10.3897/zookeys.947.52570",
        "Milotić, T., Desmet, P., Anselin, A., De Bruyn, L., De Regge, N., Janssens, K., Klaassen, R., Koks, B., Schaub, T., Schlaich, A., Spanoghe, G., T'Jollyn, F., Vanoverbeke, J. & Bouten, W. (2020). GPS tracking data of Western marsh harriers breeding in Belgium and the Netherlands. *ZooKeys*, 947, 143–155. https://doi.org/10.3897/zookeys.947.52570",
    )
    return text.rstrip() + "\n"


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text)


def _abstract(text: str) -> str:
    start = text.index("## Abstract") + len("## Abstract")
    end = text.index("**Keywords:**", start)
    return text[start:end]


def build(output: Path, manifest_path: Path | None = None) -> dict[str, object]:
    text = build_manuscript_text()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    abstract_words = len(_words(_abstract(text)))
    manifest = {
        "schema_version": 1,
        "role": "n2_mee_state_prediction_manuscript_v4",
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "word_count": len(_words(text)),
        "abstract_word_count": abstract_words,
        "abstract_within_350_words": abstract_words <= 350,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "empirical_endpoint_rerun": False,
        "retuning_performed": False,
        "scientific_reframe": "state_resolved_ecological_prediction_and_independent_transfer",
        "output": output.name,
    }
    if not manifest["abstract_within_350_words"]:
        raise ValueError(f"abstract remains too long: {abstract_words} words")
    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("build/state_prediction_v4/manuscript/N2_MEE_MANUSCRIPT_DRAFT_v4.md"))
    parser.add_argument("--manifest", type=Path, default=Path("build/state_prediction_v4/manuscript/N2_MEE_MANUSCRIPT_DRAFT_v4.manifest.json"))
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.manifest), sort_keys=True))


if __name__ == "__main__":
    main()
