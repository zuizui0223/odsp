#!/usr/bin/env python3
"""Build MEE manuscript v5 by integrating the BOP descriptive decomposition.

Version 5 starts from the frozen v4 manuscript builder output.  It does not rerun
an empirical endpoint or replace the prospectively frozen pooled comparator.  The
only scientific addition is the explicitly post-outcome species/context additive
decomposition recorded in BOP_RODENT_SPECIES_BASELINE_AMENDMENT_RECEIPT.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts.build_n2_mee_manuscript_v4 import build_manuscript_text as build_v4_text


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "BOP_RODENT_SPECIES_BASELINE_AMENDMENT_RECEIPT.json"


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


def _receipt() -> dict[str, object]:
    value = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if value["post_outcome_amendment"] is not True:
        raise ValueError("BOP decomposition must remain explicitly post-outcome")
    primary = value["frozen_primary_endpoint"]
    if primary["terminal_category"] != "empirical_state_prediction_mixed":
        raise ValueError("unexpected frozen BOP terminal category")
    if primary["positive_individual_count"] != 27 or primary["eligible_individual_count"] != 30:
        raise ValueError("unexpected frozen BOP individual counts")
    return value


def build_manuscript_text() -> str:
    receipt = _receipt()
    overall = receipt["overall_summary"]
    species = receipt["species_summary"]

    text = build_v4_text()
    text = _replace_once(
        text,
        "**Review draft:** anonymized state-prediction version 4",
        "**Review draft:** anonymized state-prediction version 5",
    )

    methods_anchor = (
        "The marginal comparator is estimated from the same training data as the state-resolved predictor and discards contextual organization. "
        "It therefore answers a concrete question: does the detailed state prediction outperform simply knowing the overall state frequencies available from the training sample?"
    )
    methods_addition = methods_anchor + (
        "\n\nFor the multi-species BOP_RODENT endpoint, species identity was itself a predictor, whereas the prospectively frozen primary comparator was the hierarchically weighted training marginal pooled across admitted species. "
        "The primary BOP gain must therefore be interpreted as the gain of a species-aware, context-conditioned predictor over a pooled lower-information baseline, not as a pure environmental-context effect. "
        "After the prospective endpoint had closed, we added an explicitly post-outcome descriptive decomposition using only the frozen result artifact. "
        "For each held-out individual, `G_total = mean_log_P_model - mean_log_P_pool` was partitioned as `G_species = mean_log_P_species - mean_log_P_pool` and `G_context = mean_log_P_model - mean_log_P_species`, so that `G_total = G_species + G_context`. "
        "The fold-specific species marginal was reconstructed from the same frozen hierarchical weighting used by the primary analysis: equal total weight among admitted species and equal total weight among training individuals within each species. "
        "The reconstructed pooled marginal reproduced the frozen marginal log scores to numerical precision. This secondary decomposition involved no model refit, no raw tracking-data re-access and no retuning, and it was not permitted to replace the prospective comparator or alter the 27/30 mixed terminal decision."
    )
    text = _replace_once(text, methods_anchor, methods_addition)

    results_anchor = (
        "Species-level sign patterns were heterogeneous. *Buteo buteo* was generalizing under the within-species all-positive rule (`5/5` positive) and *C. pygargus* was likewise generalizing (`9/9`). "
        "*C. aeruginosus* was mixed (`7/8`) and *C. cyaneus* was mixed (`6/8`). These secondary species categories did not override the all-individual mixed endpoint."
    )
    b = species["Buteo buteo"]
    a = species["Circus aeruginosus"]
    c = species["Circus cyaneus"]
    p = species["Circus pygargus"]
    results_addition = results_anchor + (
        "\n\nThe post-outcome descriptive baseline decomposition clarified what the pooled-comparator gain contained. "
        f"Across all 30 individuals, the descriptive mean total gain `{overall['mean_total_gain']:.5f}` nats/event decomposed into only `{overall['mean_species_component']:.5f}` nats/event from replacing the pooled marginal with the training-fold species marginal and `{overall['mean_context_within_species_component']:.5f}` nats/event of residual gain for the context-conditioned model over that species marginal; the context component was positive for {overall['positive_context_component_count']}/30 individuals. "
        f"The species means were heterogeneous: *B. buteo* `{b['mean_total_gain']:.5f} = {b['mean_species_component']:+.5f} + ({b['mean_context_within_species_component']:+.5f})`, *C. aeruginosus* `{a['mean_total_gain']:.5f} = {a['mean_species_component']:+.5f} + {a['mean_context_within_species_component']:+.5f}`, *C. cyaneus* `{c['mean_total_gain']:.5f} = {c['mean_species_component']:+.5f} + {c['mean_context_within_species_component']:+.5f}`, and *C. pygargus* `{p['mean_total_gain']:.5f} = {p['mean_species_component']:+.5f} + {p['mean_context_within_species_component']:+.5f}` nats/event (species-baseline plus within-species context component). "
        "Thus the unusually large *C. pygargus* total gain was not primarily a species-baseline effect, whereas *B. buteo* showed the opposite pattern, with a positive species component but a slightly negative mean within-species context component. "
        "Species-specific four-state altitude counts are supplied in the anonymous review evidence. Because this decomposition was added after outcome access, it is descriptive and leaves the prospective pooled-baseline score, 27/30 result and `empirical_state_prediction_mixed` terminal category unchanged."
    )
    text = _replace_once(text, results_anchor, results_addition)

    discussion_anchor = (
        "The BOP_RODENT result provides a prospective empirical demonstration of this principle. Context- and species-conditioned altitude probabilities improved primary log score for 90% of held-out individuals and Brier score for all individuals. Thus the richer response was not merely a descriptive decomposition of the training data. It carried predictive information for most independent organisms."
    )
    discussion_addition = discussion_anchor + (
        "\n\nThe comparator used for that prospective claim matters. Because the BOP predictor included species identity but the frozen marginal comparator pooled species, the original primary gain combines information associated with species membership and information associated with within-species environmental and spatiotemporal context. "
        "The post-outcome additive audit shows that the latter dominates the overall descriptive mean (`+0.49812` versus `+0.07279` nats/event), and it accounts for most of the large *C. pygargus* gain. "
        "However, this pattern is not universal: *B. buteo* had a slightly negative mean within-species context component despite a positive total gain. The decomposition therefore strengthens interpretation of the BOP result without converting it into a causal species effect or a claim that contextual prediction improves within every species."
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
        "role": "n2_mee_state_prediction_manuscript_v5",
        "base_manuscript_builder": "scripts/build_n2_mee_manuscript_v4.py",
        "new_evidence": RECEIPT.name,
        "word_count": len(_words(text)),
        "abstract_word_count": abstract_words,
        "abstract_within_350_words": abstract_words <= 350,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "empirical_endpoint_rerun": False,
        "primary_bop_comparator_changed": False,
        "primary_bop_terminal_changed": False,
        "post_outcome_decomposition_declared": True,
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
    parser.add_argument("--output", type=Path, default=Path("build/state_prediction_v5/manuscript/N2_MEE_MANUSCRIPT_DRAFT_v5.md"))
    parser.add_argument("--manifest", type=Path, default=Path("build/state_prediction_v5/manuscript/N2_MEE_MANUSCRIPT_DRAFT_v5.manifest.json"))
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.manifest), sort_keys=True))


if __name__ == "__main__":
    main()
