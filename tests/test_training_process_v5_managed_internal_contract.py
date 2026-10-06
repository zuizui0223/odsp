from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path("ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_VALIDATION_CONTRACT.json")
PROMOTION = Path("ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_PROMOTION_GATE.json")
IDENTITY = Path("ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_IDENTITY_CONTRACT.json")


def test_managed_internal_layer_does_not_change_v5_statistics():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    boundary = payload["statistical_boundary"]
    assert boundary["statistical_method_changed"] is False
    assert boundary["v5_operating_characteristics_recomputed"] is False
    assert boundary["process_mean_estimand_changed"] is False
    assert payload["canonical_candidate_surface"] == (
        "odsp.training_process_managed_internal_v5."
        "run_managed_internal_training_process_v5"
    )
    assert payload["chronology"][
        "validation_freeze_must_strictly_precede_declared_first_validation_outcome_access"
    ] is True


def test_managed_internal_promotion_is_narrow_and_external_route_stays_frozen():
    payload = json.loads(PROMOTION.read_text(encoding="utf-8"))
    semantics = payload["promotion_semantics"]
    assert semantics["new_statistical_method"] is False
    assert semantics["statistical_recalibration_required"] is False
    assert semantics["managed_model_to_score_derivation_required_for_new_primary_route"] is True
    scope = payload["scope"]
    assert scope["contrast_count"] == 2
    assert scope["contrast_count_4"] is False
    assert scope["paired"] is False
    assert scope["complete_lattice"] is False
    external = payload["external_route_boundary"]
    assert external["untouched_external_primary_surface_changed"] is False
    assert external["immutable_external_internal_v5_snapshot_changed"] is False
    assert external["external_route_evidence_chain_rewritten"] is False


def test_identity_contract_requires_focused_evidence_before_promotion():
    payload = json.loads(IDENTITY.read_text(encoding="utf-8"))
    assert payload["canonical_surface"] == (
        "odsp.training_process_managed_internal_v5."
        "run_managed_internal_training_process_v5"
    )
    focused = payload["focused_evidence_required"]
    assert focused["official_github_actions_run_required"] is True
    assert focused["focused_test_receipt_required"] is True
    assert focused["managed_internal_contract_sha256_required"] is True
    assert payload["boundary"]["statistical_operating_characteristics_recomputed"] is False
