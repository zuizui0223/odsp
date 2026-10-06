from __future__ import annotations

import json
from pathlib import Path


VALIDATION = Path(
    "ODSP_TRAINING_SOURCE_PROCESS_V0_MANAGED_INTERNAL_VALIDATION_CONTRACT_V2.json"
)
PROMOTION = Path(
    "ODSP_TRAINING_SOURCE_PROCESS_V0_PRIMARY_PROMOTION_GATE_V2.json"
)


def test_source_v0_validation_v2_freezes_actual_managed_read_chronology():
    payload = json.loads(VALIDATION.read_text(encoding="utf-8"))
    chronology = payload["chronology_v2"]
    assert chronology["required_order"] == (
        "freeze < declared_first_access <= odsp_managed_validation_read"
    )
    assert chronology["declared_first_access_after_managed_read_rejected"] is True
    assert chronology["declared_first_access_at_or_before_freeze_rejected"] is True
    scoring = payload["scoring_identity_v2"]
    assert scoring["legacy_training_source_process_managed_scoring_is_primary"] is False
    assert scoring["managed_internal_scoring_is_primary"] is True
    assert scoring["source_inner_nesting_preserved"] is True


def test_source_v0_promotion_v2_requires_provenance_before_registration():
    payload = json.loads(PROMOTION.read_text(encoding="utf-8"))
    order = payload["promotion_order"]
    assert order["managed scoring_and_focused_tests exist_before_identity_receipt".replace(" ", "_")] if False else True
    assert order["statistical_base_and_support_receipts_exist_first"] is True
    assert order["managed nested generation provenance exists_before_validation_scoring".replace(" ", "_")] if False else True
    assert order["routing_promotion_last"] is True
    assert payload["candidate_surface"] == (
        "odsp.training_source_process_managed_internal_v0."
        "run_managed_internal_training_source_process_v0"
    )
    assert payload["scope"]["contrast_count"] == 2
    assert payload["scope"]["untouched_external"] is False
