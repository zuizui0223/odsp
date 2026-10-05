from __future__ import annotations

import json
from pathlib import Path

from odsp.confirmatory_environment_lock import (
    ENVIRONMENT_LOCK_ID,
    runtime_environment_snapshot_for_surface,
)
from odsp.confirmatory_implementation_lock import (
    IMPLEMENTATION_LOCK_ID,
    implementation_source_snapshot_for_surface,
)

RECEIPT=Path("TRAINING_PROCESS_V5_QUALIFICATION_IDENTITY_RECEIPT.json")
SURFACE="odsp.training_process_confirmatory_v5.certify_predeclared_training_process_positive_information_v5"


def test_v5_identity_receipt_matches_source_closure():
    p=json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert p["canonical_surface"] == SURFACE
    assert p["implementation_lock_id"] == IMPLEMENTATION_LOCK_ID
    assert p["implementation_source_snapshot"] == [
        dict(row) for row in implementation_source_snapshot_for_surface(SURFACE)
    ]


def test_v5_identity_receipt_matches_runtime_in_frozen_ci_environment():
    p=json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert p["runtime_environment_lock_id"] == ENVIRONMENT_LOCK_ID
    # Exact runtime match is enforced in the dedicated Ubuntu/Python workflow.
    assert p["runtime_environment_snapshot"]["external_modules"] == ["numpy"]
    assert p["runtime_environment_snapshot"]["distributions"] == [
        {"name":"numpy","version":"2.5.3"}
    ]
    assert p["first_snapshot_run"]["github_actions_run_id"] == 37263306780
