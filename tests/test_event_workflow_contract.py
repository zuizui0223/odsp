from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_event_workflow_contract_keeps_scientific_choices_explicit():
    contract = json.loads(
        (ROOT / "N2_EVENT_WORKFLOW_CONTRACT.json").read_text(encoding="utf-8")
    )
    assert contract["contract_id"] == "n2-event-workflow-baseline-hierarchy-v1"
    assert contract["baseline_semantics"]["requested_baseline_does_not_change_model_fit"] is True
    assert contract["independence_semantics"]["group_is_scoring_unit"] is True
    assert contract["independence_semantics"]["groups_may_not_span_folds"] is True
    assert contract["independence_semantics"]["groups_may_not_span_strata"] is True
    assert contract["bop_shadow_parity"]["canonical_bop_endpoint_reimplemented"] is False
    assert contract["bop_shadow_parity"]["frozen_bop_artifacts_modified"] is False
    boundary = contract["scientific_boundaries"]
    assert boundary["frozen_empirical_endpoint_rerun"] is False
    assert boundary["frozen_terminal_reclassification"] is False
    assert boundary["baseline_choice_is_automatic"] is False
    assert boundary["training_weight_policy_is_automatic"] is False
    assert boundary["causality_claimed"] is False
