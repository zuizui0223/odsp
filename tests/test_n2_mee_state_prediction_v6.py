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


def test_v6_preserves_v5_as_historical_surface() -> None:
    v5 = build_v5_text()
    v6 = build_v6_text()
    assert "anonymized state-prediction version 5" in v5
    assert "anonymized state-prediction version 6" not in v5
    assert "anonymized state-prediction version 6" in v6
    assert "anonymized state-prediction version 5" not in v6
    assert v5 != v6


def test_v6_abstract_is_distributional_and_within_mee_limit() -> None:
    abstract = _abstract(build_v6_text())
    assert len(_words(abstract)) <= 350
    required = (
        "ecological-state distribution prediction",
        "probability mass function for finite states",
        "density for continuous or circular states",
        "joint density for composite states",
        "`G_j = E[log q_train(A|X) - log q0_train(A)]`",
        "same reference measure",
        "10/10 cross-geometry obligations",
    )
    for phrase in required:
        assert phrase in abstract


def test_v6_methods_separate_common_score_from_geometry_specific_quantities() -> None:
    text = build_v6_text()
    required = (
        "does not require continuous altitude, depth or time to be discretized",
        "p(z,t|X)=p(t|X)p(z|X,t)",
        "same realized state against the same reference measure",
        "common change of units or Jacobian",
        "Secondary diagnostics remain state-space-specific",
        "continuous predictions can report RMSE and CRPS",
        "circular predictions can report circular error",
        "neither a symmetric dependence measure nor a causal effect",
        "does not make differential entropy coordinate-invariant",
        "justify `exp(H)` as an effective-state count for continuous variables",
    )
    for phrase in required:
        assert phrase in text


def test_v6_reports_two_distinct_generality_layers() -> None:
    text = build_v6_text()
    assert "1,873 representation-level obligations passed" in text
    assert "All 10/10 cross-geometry obligations passed" in text
    assert "maximum absolute error `4.44e-16`" in text
    assert "finite-discrete, continuous, circular and joint continuous-circular" in text
    assert "State-space generality is broader than current biological validation" in text
    assert "differential entropy changes under reparameterization" in text


def test_v6_preserves_v5_bop_decomposition_and_terminal_boundaries() -> None:
    text = build_v6_text()
    required = (
        "explicitly post-outcome descriptive decomposition",
        "`G_total = mean_log_P_model - mean_log_P_pool`",
        "`G_species = mean_log_P_species - mean_log_P_pool`",
        "`G_context = mean_log_P_model - mean_log_P_species`",
        "27/30 result and `empirical_state_prediction_mixed` terminal category unchanged",
        "`empirical_state_prediction_unavailable`",
        "zero random-forest held-out folds were executed",
    )
    for phrase in required:
        assert phrase in text


def test_v6_does_not_claim_continuous_biological_validation() -> None:
    text = build_v6_text()
    assert (
        "continuous, circular and joint modules in this paper provide implementation-level and known-structure validation rather than new prospective biological endpoints"
        in text
    )
    assert "Wider biological generality requires prospectively designed distribution-prediction endpoints" in text
