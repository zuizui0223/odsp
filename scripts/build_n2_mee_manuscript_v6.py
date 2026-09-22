#!/usr/bin/env python3
"""Build manuscript v6 with copy edits plus the BOP population amendment.

Version 6 preserves every prospective empirical endpoint from v5.  It keeps the
two reviewer-facing copy edits introduced in the earlier v6 draft and adds one
scientific item only: the explicitly post-outcome descriptive population-transfer
summary frozen in BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_n2_mee_manuscript_v5 import build_manuscript_text as build_v5_text


POPULATION_RECEIPT = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT.json"


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


def _population_receipt() -> dict[str, object]:
    value = json.loads(POPULATION_RECEIPT.read_text(encoding="utf-8"))
    if value["post_outcome_amendment"] is not True:
        raise ValueError("BOP population summary must remain explicitly post-outcome")
    if value["analysis_type"] != "descriptive_secondary_population_transfer":
        raise ValueError("unexpected BOP population analysis type")
    primary = value["frozen_primary_endpoint"]
    if primary["terminal_category"] != "empirical_state_prediction_mixed":
        raise ValueError("BOP primary terminal category drifted")
    if primary["terminal_decision_changed"] is not False:
        raise ValueError("BOP population amendment changed the primary endpoint")
    population = value["population_result"]
    if population["familywise_confirmatory_claim"] is not False:
        raise ValueError("population amendment must remain descriptive")
    return value


def build_manuscript_text() -> str:
    population_receipt = _population_receipt()
    population = population_receipt["population_result"]
    total = population["total_gain"]
    species_step, context_step = population["steps"]

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

    methods_anchor = (
        "The reconstructed pooled marginal reproduced the frozen marginal log scores to numerical precision. "
        "This secondary decomposition involved no model refit, no raw tracking-data re-access and no retuning, "
        "and it was not permitted to replace the prospective comparator or alter the 27/30 mixed terminal decision."
    )
    methods_addition = methods_anchor + (
        "\n\nUsing the same frozen individual gains, we additionally summarized transfer "
        "at the population-of-individuals level as a post-outcome descriptive amendment. "
        "Each held-out individual contributed equal weight, while species was treated as "
        "the resampling cluster (four represented species). We report the mean total "
        "first-to-final gain, a species-cluster percentile-bootstrap interval, the fraction "
        "of individuals with positive gain and its cluster-bootstrap lower bound, "
        "between-individual dispersion, a labelled normal-theory new-individual prediction "
        "interval, and empirical gain quantiles. Total first-to-final transfer was reported "
        "separately from the non-skippable adjacent-step ceiling. This amendment did not "
        "refit models, re-access raw tracking data, retune any rule or alter the prospective "
        "primary endpoint."
    )
    text = _replace_once(text, methods_anchor, methods_addition)

    results_anchor = (
        "Species-specific four-state altitude counts are supplied in the anonymous review evidence. "
        "Because this decomposition was added after outcome access, it is descriptive and leaves the "
        "prospective pooled-baseline score, 27/30 result and `empirical_state_prediction_mixed` terminal category unchanged."
    )
    results_addition = results_anchor + (
        "\n\nThe population summary gave a more graded description of that mixed primary result. "
        f"The frozen total log-score gain averaged `{total['mean_gain']:.5f}` nats/event across individuals, "
        f"with a 95% species-cluster bootstrap interval of `[{total['mean_gain_lower']:.5f}, {total['mean_gain_upper']:.5f}]`; "
        f"{total['positive_group_count']}/30 individuals were positive and the cluster-bootstrap lower bound on the positive fraction was `{total['positive_fraction_lower']:.3f}`. "
        f"Between-individual heterogeneity remained substantial: the labelled normal-theory new-individual prediction interval was `[{total['prediction_lower']:.3f}, {total['prediction_upper']:.3f}]`, while the empirical 10th percentile was still positive (`{total['empirical_p10']:.3f}`). "
        f"The pooled-to-species increment remained uncertain at the population-mean level (`[{species_step['mean_gain_lower']:.3f}, {species_step['mean_gain_upper']:.3f}]`), whereas the species-to-context increment was positive (`[{context_step['mean_gain_lower']:.3f}, {context_step['mean_gain_upper']:.3f}]`). "
        "Accordingly, the non-skippable stepwise population ceiling remained pooled even though total first-to-final transfer was positive. "
        "Because only four species clusters were represented, the cluster-level uncertainty is descriptive and should not be read as precise species-superpopulation inference."
    )
    text = _replace_once(text, results_anchor, results_addition)

    discussion_anchor = (
        "However, this pattern is not universal: *B. buteo* had a slightly negative mean within-species context component despite a positive total gain. "
        "The decomposition therefore strengthens interpretation of the BOP result without converting it into a causal species effect or a claim that contextual prediction improves within every species."
    )
    discussion_addition = discussion_anchor + (
        "\n\nThe population summary separates two questions that the binary mixed label compresses. "
        "At the level of the total frozen gain, the mean remained positive under species-cluster resampling and the empirical lower tail was mostly positive, supporting broad but not universal transfer across the observed individuals. "
        "At the level of a new individual, the prediction interval still crossed zero, so appreciable heterogeneity remains. "
        "Likewise, decomposing the information ladder shows that a positive total gain need not imply that every intermediate increment is independently supported. "
        "We therefore retain the prospective mixed endpoint and the conservative stepwise ceiling while using the population summary to describe effect magnitude, prevalence and heterogeneity rather than forcing all three questions into a single unanimity category."
    )
    text = _replace_once(text, discussion_anchor, discussion_addition)

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
        "new_evidence": POPULATION_RECEIPT.name,
        "word_count": len(_words(text)),
        "abstract_word_count": abstract_words,
        "abstract_ceiling_words": 350,
        "abstract_headroom_words": 350 - abstract_words,
        "abstract_within_350_words": abstract_words <= 350,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "empirical_endpoint_rerun": False,
        "primary_bop_comparator_changed": False,
        "primary_bop_terminal_changed": False,
        "existing_post_outcome_decomposition_changed": False,
        "post_outcome_population_amendment_added": True,
        "copy_edit_only_successor_to_v5": False,
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
