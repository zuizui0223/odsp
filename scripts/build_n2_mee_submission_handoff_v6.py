#!/usr/bin/env python3
"""Build a copy-ready N2 MEE v6 submission handoff from validated artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_n2_mee_manuscript_v6 import build_manuscript_text  # noqa: E402


TITLE_PAGE = ROOT / "manuscript" / "N2_MEE_TITLE_PAGE_TEMPLATE_v6.md"
COVER_LETTER = ROOT / "manuscript" / "N2_MEE_COVER_LETTER_DRAFT_v6.md"
DISCLOSURES = ROOT / "manuscript" / "N2_MEE_DISCLOSURE_DRAFTS_v6.md"
POPULATION_RECEIPT = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _plain(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    return text.strip()


def _section(text: str, heading: str, next_heading: str | None = None) -> str:
    start = text.index(heading) + len(heading)
    if next_heading is None:
        return text[start:].strip()
    end = text.index(next_heading, start)
    return text[start:end].strip()


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def build_packet(docx_validation_path: Path) -> dict[str, object]:
    validation = _read(docx_validation_path)
    if validation.get("passed") is not True:
        raise ValueError("v6 DOCX must pass structural validation before handoff")
    failed = validation.get("failed_checks")
    if failed not in ([], None):
        raise ValueError("v6 DOCX validation contains failed checks")

    manuscript = build_manuscript_text()
    title_page = TITLE_PAGE.read_text(encoding="utf-8")
    population_receipt = _read(POPULATION_RECEIPT)
    population = population_receipt["population_result"]
    total = population["total_gain"]

    title = manuscript.splitlines()[0].removeprefix("# ").strip()
    abstract = _plain(_section(manuscript, "## Abstract", "**Keywords:**"))
    keyword_line = manuscript.split("**Keywords:**", 1)[1].splitlines()[0].strip()
    keywords = [item.strip() for item in keyword_line.split(";") if item.strip()]
    running = _plain(_section(title_page, "## Running headline", "## Authors and affiliations"))

    author_only = {
        "authors_and_order": None,
        "affiliations_and_addresses": None,
        "corresponding_author_contact": None,
        "credit_roles": None,
        "named_ai_code_accountable_author": None,
        "acknowledgements": None,
        "funding": None,
        "conflict_of_interest": None,
        "all_author_approval": False,
        "not_under_consideration_elsewhere_confirmed": False,
        "third_party_reuse_terms_confirmed_for_all_sources": False,
        "data_availability_wording_approved": False,
        "ethics_wording_approved": False,
        "generative_ai_wording_approved": False,
        "translated_abstract_decision_made": False,
        "exact_upload_files_visually_approved_by_author": False,
    }

    return {
        "schema_version": 1,
        "handoff_id": "n2-mee-state-prediction-v6-submission-handoff",
        "generated_from_validated_v6_sources": True,
        "journal": "Methods in Ecology and Evolution",
        "article_type": "Research Article",
        "title": title,
        "running_headline": running,
        "abstract": abstract,
        "abstract_word_count": _word_count(abstract),
        "keywords": keywords,
        "submission_files": {
            "anonymous_main_manuscript_docx": "N2_MEE_ANONYMOUS_REVIEW_v6.docx",
            "separate_title_page": TITLE_PAGE.relative_to(ROOT).as_posix(),
            "cover_letter": COVER_LETTER.relative_to(ROOT).as_posix(),
            "disclosure_drafts": DISCLOSURES.relative_to(ROOT).as_posix(),
        },
        "scientific_terminal_states": {
            "MH_ANTWERPEN": "empirical_state_prediction_unavailable",
            "BOP_RODENT": "empirical_state_prediction_mixed",
        },
        "bop_population_amendment": {
            "post_outcome": population_receipt["post_outcome_amendment"],
            "descriptive_secondary": population_receipt["analysis_type"]
            == "descriptive_secondary_population_transfer",
            "mean_total_gain_nats": total["mean_gain"],
            "cluster_bootstrap_lower": total["mean_gain_lower"],
            "cluster_bootstrap_upper": total["mean_gain_upper"],
            "positive_individuals": total["positive_group_count"],
            "eligible_individuals": total["group_count"],
            "positive_fraction_lower": total["positive_fraction_lower"],
            "new_individual_prediction_lower": total["prediction_lower"],
            "new_individual_prediction_upper": total["prediction_upper"],
            "empirical_p10": total["empirical_p10"],
            "represented_species_clusters": population["cluster_count"],
            "stepwise_population_ceiling": population[
                "population_mean_supported_ceiling"
            ],
            "can_reclassify_primary_endpoint": False,
        },
        "mechanical_submission_status": {
            "manuscript_v6_generated": True,
            "review_docx_v6_generated": True,
            "review_docx_v6_structurally_validated": True,
            "exact_upload_visual_approval_completed": False,
        },
        "author_only_fields": author_only,
        "submission_system_state": {
            "nonpersonal_metadata_packet_ready": True,
            "metadata_entered_in_submission_system": False,
            "ready_for_submission": False,
        },
        "scientific_source_modified": False,
        "empirical_endpoint_rerun": False,
        "frozen_decision_rule_modified": False,
        "prospective_bop_endpoint_reclassified": False,
        "n2_to_n3_promoted": False,
    }


def render_markdown(packet: dict[str, object]) -> str:
    return (
        "# N2 MEE v6 submission-system handoff\n\n"
        f"**Journal:** {packet['journal']}  \n"
        f"**Article type:** {packet['article_type']}  \n"
        f"**Title:** {packet['title']}  \n"
        f"**Running headline:** {packet['running_headline']}\n\n"
        "## Abstract\n\n" + packet["abstract"] + "\n\n"
        "## Keywords\n\n" + "; ".join(packet["keywords"]) + "\n\n"
        "## BOP population amendment\n\n"
        + json.dumps(packet["bop_population_amendment"], ensure_ascii=False)
        + "\n\n## Still requires author confirmation\n\n"
        + "\n".join(
            f"- {key}: {value}"
            for key, value in packet["author_only_fields"].items()
        )
        + "\n\nThis handoff does not authorize submission and does not alter any prospective scientific endpoint.\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx-validation", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    packet = build_packet(args.docx_validation)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.markdown.write_text(render_markdown(packet), encoding="utf-8")
    print(
        json.dumps(
            {
                "abstract_word_count": packet["abstract_word_count"],
                "keywords": len(packet["keywords"]),
                "ready_for_submission": False,
            }
        )
    )


if __name__ == "__main__":
    main()
