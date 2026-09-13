from __future__ import annotations

from pathlib import Path


GOVERNANCE_TOKENS = (
    "forecast_assessment",
    "forecast_provenance",
    "forecast_trust",
    "forecast_model_comparison",
    "forecast_stacking",
    "prediction_trust",
    "trust_aware",
    "trust_dossier",
    "trusted_state_prediction",
    "evaluation_access",
    "evaluation_content",
    "evaluation_ledger",
    "ledger_binding",
    "checkpoint",
    "provenance",
    "bias_robust",
    "robust_model_selection",
    "robust_trust",
    "block_aware",
    "block_definition",
    "bounded_reweighting",
    "joint_bias",
    "joint_robustness",
    "simultaneous_group",
    "model_refit",
    "aligned_refit",
    "refit_scheme",
    "groupwise_coverage",
    "heldout_row_alignment",
    "selection_provenance",
    "training_provenance",
)

SUBMISSION_TOKENS = (
    "n2_mee",
    "submission",
    "review_bundle",
    "review_distribution",
    "handoff",
    "anonymous_review",
    "docx",
    "render",
    "title_page",
    "cover_letter",
    "final_readiness",
    "policy_compliance",
)

LANES = ("core", "governance", "submission")


def classify_test_path(path: str | Path) -> str:
    """Classify a test module by repository role, not by outcome.

    `core` is the default scientific lane.  Governance and submission markers are
    carved out explicitly so new ordinary scientific tests remain in the fast
    default lane unless their filename declares one of these infrastructure roles.
    """

    name = Path(path).name.lower()
    if any(token in name for token in SUBMISSION_TOKENS):
        return "submission"
    if any(token in name for token in GOVERNANCE_TOKENS):
        return "governance"
    return "core"
