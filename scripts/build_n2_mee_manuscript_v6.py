#!/usr/bin/env python3
"""Build submission-facing manuscript v6 as a copy-edit-only successor to v5.

Version 6 preserves every frozen empirical endpoint and numerical result from v5.
It makes two reviewer-facing language changes only:

1. add abstract headroom below the 350-word ceiling without changing its claims;
2. qualify BOP species-level sign categories as pooled-comparator categories so
   they cannot be misread as within-species context generalization.

The canonical v5 manuscript, handoff packet and visual-QA receipts are not
overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts.build_n2_mee_manuscript_v5 import build_manuscript_text as build_v5_text


def _replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected exactly one occurrence, found {count}: {old!r}")
    return text.replace(old, new, 1)


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text)


def _abstract(text: str) -> str:
    start = text.index("## Abstract") + len("## Abstract")
    end = text.index("**Keywords:**", start)
    return text[start:end]


def build_manuscript_text() -> str:
    text = build_v5_text()
    text = _replace_once(
        text,
        "**Review draft:** anonymized state-prediction version 5",
        "**Review draft:** anonymized state-prediction version 6",
    )

    old_abstract = (
        "The framework can sit above different learners, including random forests, "
        "multinomial regression and other probabilistic models. It does not guarantee "
        "universal transfer, infer causal drivers or determine the biological meaning "
        "of an axis; instead it provides a reproducible way to ask **which state, with "
        "what probability, and does that extra resolution generalize?**"
    )
    new_abstract = (
        "The framework can sit above different probabilistic learners. It does not "
        "guarantee universal transfer, infer causal drivers or determine axis meaning; "
        "instead it asks **which state, with what probability, and does that extra "
        "resolution generalize?**"
    )
    text = _replace_once(text, old_abstract, new_abstract)

    old_species_sentence = (
        "Species-level sign patterns were heterogeneous. *Buteo buteo* was generalizing "
        "under the within-species all-positive rule (`5/5` positive) and *C. pygargus* "
        "was likewise generalizing (`9/9`). *C. aeruginosus* was mixed (`7/8`) and "
        "*C. cyaneus* was mixed (`6/8`). These secondary species categories did not "
        "override the all-individual mixed endpoint."
    )
    new_species_sentence = (
        "Species-level sign patterns under the prospectively pooled comparator were "
        "heterogeneous. *Buteo buteo* met the pooled-comparator all-positive rule "
        "(`5/5` positive), as did *C. pygargus* (`9/9`); *C. aeruginosus* was mixed "
        "(`7/8`) and *C. cyaneus* was mixed (`6/8`). These secondary pooled-comparator "
        "categories did not override the all-individual mixed endpoint."
    )
    text = _replace_once(text, old_species_sentence, new_species_sentence)
    return text.rstrip() + "\n"


def build(output: Path, manifest_path: Path | None = None) -> dict[str, object]:
    text = build_manuscript_text()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    abstract_words = len(_words(_abstract(text)))
    manifest = {
        "schema_version": 1,
        "role": "n2_mee_state_prediction_manuscript_v6",
        "base_manuscript_builder": "scripts/build_n2_mee_manuscript_v5.py",
        "word_count": len(_words(text)),
        "abstract_word_count": abstract_words,
        "abstract_ceiling_words": 350,
        "abstract_headroom_words": 350 - abstract_words,
        "abstract_within_350_words": abstract_words <= 350,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "empirical_endpoint_rerun": False,
        "primary_bop_comparator_changed": False,
        "primary_bop_terminal_changed": False,
        "post_outcome_decomposition_changed": False,
        "copy_edit_only_successor_to_v5": True,
        "v5_submission_artifacts_overwritten": False,
        "output": output.name,
    }
    if not manifest["abstract_within_350_words"]:
        raise ValueError(f"abstract remains too long: {abstract_words} words")
    if manifest["abstract_headroom_words"] < 10:
        raise ValueError(
            f"abstract has insufficient editing headroom: {abstract_words} words"
        )
    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "build/state_prediction_v6/manuscript/N2_MEE_MANUSCRIPT_DRAFT_v6.md"
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "build/state_prediction_v6/manuscript/"
            "N2_MEE_MANUSCRIPT_DRAFT_v6.manifest.json"
        ),
    )
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.manifest), sort_keys=True))


if __name__ == "__main__":
    main()
