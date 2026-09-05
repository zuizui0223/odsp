from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript" / "N2_MEE_MANUSCRIPT_DRAFT_v4.md"
MATRIX = ROOT / "N2_STATE_PREDICTION_EVIDENCE_MATRIX.json"


def _text() -> str:
    return MANUSCRIPT.read_text(encoding="utf-8")


def _abstract(text: str) -> str:
    start = text.index("## Abstract") + len("## Abstract")
    end = text.index("**Keywords:**", start)
    return text[start:end]


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def test_v4_has_state_prediction_as_primary_center():
    text = _text()
    assert text.startswith("# State-resolved ecological prediction:")
    assert "P(A|X)" in text
    assert "which ecological state is predicted, with what probability, and does that prediction transfer?" in text
    assert "ODSP is not a competing occurrence-SDM learner" in text


def test_v4_abstract_is_numbered_and_within_mee_limit():
    abstract = _abstract(_text())
    for number in ("1.", "2.", "3.", "4."):
        assert number in abstract
    assert _word_count(abstract) <= 350
    assert "27/30" in abstract
    assert "30/30" in abstract
    assert "mixed terminal state" in abstract


def test_v4_empirical_numbers_match_matrix():
    text = _text()
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    mh, bop = matrix["prospective_state_prediction_endpoints"]
    rf = bop["primary_random_forest"]

    assert str(mh["thinned_events"]) in text
    assert "only three eligible independent individuals" in text
    assert str(bop["eligible_events"]) in text
    assert "27 of 30" in text
    assert "All 30 individuals had positive Brier improvement" in text
    assert f"`+{rf['mean_gain_descriptive']:.5f}`" in text
    assert f"`+{rf['mean_brier_improvement_descriptive']:.5f}`" in text
    assert "`empirical_state_prediction_mixed`" in text


def test_v4_retains_prospective_and_claim_boundaries():
    text = _text()
    assert "frozen before outcome access" in text
    assert "No retuning" in text or "no retuning" in text
    assert "does not show that the predictors causally determine the state" in text
    assert "not automatically promoted to a subsequent N3 state artifact" in text
    assert "absolute altitude above mean sea level is not height above ground" in text


def test_v4_keeps_supporting_diagnostic_chain_but_not_as_primary_prediction_evidence():
    text = _text()
    for token in ("Tawaki", "European free-tailed bat", "Snapshot Serengeti"):
        assert token in text
    assert "These analyses are not additional state-prediction training datasets" in text


def test_v4_contains_required_policy_sections():
    text = _text()
    assert "## 2.12 Ethics and use of archived data" in text
    assert "## 2.13 Generative-AI assistance" in text
    assert "GPT-5.6 Sol" in text
