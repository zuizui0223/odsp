from __future__ import annotations

import re

from scripts.build_n2_mee_manuscript_v5 import build_manuscript_text as build_v5_text
from scripts.build_n2_mee_manuscript_v6 import build_manuscript_text as build_v6_text


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text)


def _abstract(text: str) -> str:
    start = text.index("## Abstract") + len("## Abstract")
    end = text.index("**Keywords:**", start)
    return text[start:end]


def test_v6_is_distinct_copy_edit_successor_without_mutating_v5_surface():
    v5 = build_v5_text()
    v6 = build_v6_text()
    assert "anonymized state-prediction version 5" in v5
    assert "anonymized state-prediction version 6" not in v5
    assert "anonymized state-prediction version 6" in v6
    assert v5 != v6


def test_v6_creates_real_abstract_headroom_without_changing_claim_direction():
    v5_abstract = _abstract(build_v5_text())
    v6_abstract = _abstract(build_v6_text())
    assert len(_words(v5_abstract)) == 350
    assert 330 <= len(_words(v6_abstract)) <= 340
    assert len(_words(v6_abstract)) <= 350
    assert "27/30 individuals" in v6_abstract
    assert "30/30" in v6_abstract
    assert "mixed terminal state" in v6_abstract
    assert "does not guarantee universal transfer" in v6_abstract


def test_v6_qualifies_buteo_category_by_the_prospective_pooled_comparator():
    text = build_v6_text()
    assert (
        "*Buteo buteo* was generalizing under the within-species all-positive rule"
        not in text
    )
    assert "Species-level sign patterns under the prospectively pooled comparator" in text
    assert "*Buteo buteo* met the pooled-comparator all-positive rule (`5/5` positive)" in text
    assert "These secondary pooled-comparator categories did not override" in text


def test_v6_preserves_bop_decomposition_and_terminal_boundaries():
    text = build_v6_text()
    required = (
        "`0.57091` nats/event",
        "`0.07279` nats/event",
        "`0.49812` nats/event",
        "positive for 23/30 individuals",
        "*B. buteo* `0.23031 = +0.27362 - 0.04331`",
        "*C. pygargus* `1.24613 = +0.31376 + 0.93237`",
        "27/30 result and `empirical_state_prediction_mixed` terminal category unchanged",
        "not as a pure environmental-context effect",
        "without converting it into a causal species effect",
    )
    for phrase in required:
        assert phrase in text
