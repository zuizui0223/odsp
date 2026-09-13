from __future__ import annotations

import re

from scripts.build_n2_mee_manuscript_v4 import build_manuscript_text as build_v4_text
from scripts.build_n2_mee_manuscript_v5 import build_manuscript_text as build_v5_text


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text)


def _abstract(text: str) -> str:
    start = text.index("## Abstract") + len("## Abstract")
    end = text.index("**Keywords:**", start)
    return text[start:end]


def test_v5_preserves_v4_and_creates_a_distinct_submission_surface():
    v4 = build_v4_text()
    v5 = build_v5_text()
    assert "anonymized state-prediction version 4" in v4
    assert "anonymized state-prediction version 5" not in v4
    assert "anonymized state-prediction version 5" in v5
    assert "anonymized state-prediction version 4" not in v5
    assert v4 != v5


def test_v5_keeps_abstract_unchanged_and_within_mee_limit():
    v4 = build_v4_text()
    v5 = build_v5_text()
    assert _abstract(v5) == _abstract(v4)
    assert len(_words(_abstract(v5))) <= 350


def test_v5_declares_the_primary_bop_comparator_and_post_outcome_decomposition():
    text = build_v5_text()
    required = (
        "species identity was itself a predictor",
        "prospectively frozen primary comparator was the hierarchically weighted training marginal pooled across admitted species",
        "explicitly post-outcome descriptive decomposition",
        "`G_total = mean_log_P_model - mean_log_P_pool`",
        "`G_species = mean_log_P_species - mean_log_P_pool`",
        "`G_context = mean_log_P_model - mean_log_P_species`",
        "no model refit, no raw tracking-data re-access and no retuning",
        "not permitted to replace the prospective comparator or alter the 27/30 mixed terminal decision",
    )
    for phrase in required:
        assert phrase in text


def test_v5_reports_overall_and_species_decomposition_without_reclassification():
    text = build_v5_text()
    required = (
        "`0.57091` nats/event",
        "`0.07279` nats/event",
        "`0.49812` nats/event",
        "positive for 23/30 individuals",
        "*B. buteo* `0.23031 = +0.27362 + (-0.04331)`",
        "*C. aeruginosus* `0.34952 = -0.14877 + +0.49829`",
        "*C. cyaneus* `0.24555 = -0.10225 + +0.34780`",
        "*C. pygargus* `1.24613 = +0.31376 + +0.93237`",
        "Species-specific four-state altitude counts are supplied in the anonymous review evidence.",
        "27/30 result and `empirical_state_prediction_mixed` terminal category unchanged",
    )
    for phrase in required:
        assert phrase in text


def test_v5_discussion_does_not_recast_primary_gain_as_pure_context_or_causal_species_effect():
    text = build_v5_text()
    assert "not as a pure environmental-context effect" in text
    assert "does not convert the BOP result into a causal species effect" in text
    assert "contextual prediction improves within every species" in text
