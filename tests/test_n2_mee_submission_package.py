from __future__ import annotations

import json
from pathlib import Path
import re

from scripts.build_n2_mee_figures import figure_data
from scripts.build_n2_mee_manuscript_v2 import build_manuscript_text


ROOT = Path(__file__).resolve().parents[1]


def _abstract(text: str) -> str:
    return text.split("## Abstract\n", 1)[1].split("**Keywords:**", 1)[0]


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def test_integrated_v2_contains_validated_generality_sections_and_numbers():
    text = build_manuscript_text()
    assert "**Review draft:** anonymized integrated version 2" in text
    assert "## 2.6 Generality and invariance validation" in text
    assert "## 3.2 The evidence core was invariant across high-dimensional representations" in text
    assert "## 4.5 What kind of generality is supported" in text
    assert "1,873 of 1,873" in text
    assert "2.4868995751603507e-14" in text
    assert "## Methods insert" not in text
    assert "## Results insert" not in text
    assert "## Discussion insert" not in text


def test_v2_preserves_closed_empirical_terminal_values():
    text = build_manuscript_text()
    bat = json.loads((ROOT / "N2_BAT_THICKNESS_TERMINAL_DECISION.json").read_text())
    serengeti = json.loads((ROOT / "N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json").read_text())
    assert str(bat["primary"]["information_nats_H_Z_given_XY"]) in text
    assert str(bat["primary"]["effective_vertical_states"]) in text
    for item in bat["primary"]["sealed_individual_scores"]:
        assert str(item["mean_log_score_gain"]) in text
    assert str(serengeti["temporal_information_nats"]) in text
    assert str(serengeti["effective_temporal_states"]) in text
    assert str(serengeti["partition_information_nats"]) in text
    for gain in serengeti["heldout_gains"]:
        assert str(gain) in text


def test_v2_abstract_remains_four_part_and_within_mee_limit():
    abstract = _abstract(build_manuscript_text())
    parts = re.findall(r"(?m)^([1-4])\. ", abstract)
    assert parts == ["1", "2", "3", "4"]
    assert _word_count(abstract) <= 350


def test_v2_heading_sequence_is_unique_after_integration():
    text = build_manuscript_text()
    for heading in (
        "## 2.6 Generality and invariance validation",
        "## 2.7 Observation semantics and prospective empirical gates",
        "## 2.8 Empirical application 1: Tawaki structural estimability",
        "## 2.9 Empirical application 2: European free-tailed bat vertical thickness",
        "## 2.10 Empirical application 3: Snapshot Serengeti temporal partitioning",
        "## 3.2 The evidence core was invariant across high-dimensional representations",
        "## 3.3 The Tawaki vertical endpoint was prospectively unestimable",
        "## 3.8 Empirical lanes occupied three distinct inferential states",
        "## 4.5 What kind of generality is supported",
        "## 4.6 Cross-system differences demonstrate states, not mechanisms",
        "## 4.7 Projection-aware inference should end before downstream state promotion",
    ):
        assert text.count(heading) == 1, heading


def test_figure_data_is_terminal_and_generality_record_backed():
    data = figure_data()
    bat = json.loads((ROOT / "N2_BAT_THICKNESS_TERMINAL_DECISION.json").read_text())
    serengeti = json.loads((ROOT / "N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json").read_text())
    generality = json.loads((ROOT / "N2_GENERALITY_BENCHMARK_SUMMARY.json").read_text())
    assert data["empirical"]["bat"]["information_nats"] == bat["primary"]["information_nats_H_Z_given_XY"]
    assert data["empirical"]["serengeti"]["gains"] == serengeti["heldout_gains"]
    assert data["generality"]["check_count"] == generality["result"]["check_count"] == 1873
    assert data["generality"]["failed_count"] == 0
    assert data["generality"]["maximum_absolute_error"] == 2.4868995751603507e-14


def test_integrated_v2_has_no_repository_or_author_identity_tokens():
    lowered = build_manuscript_text().lower()
    for token in ("zuizui0223", "zhang ruiqi", "rachelzhang", "rachel zhang"):
        assert token not in lowered
