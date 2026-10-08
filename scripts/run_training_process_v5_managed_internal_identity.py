"""Snapshot managed-internal v5 source/runtime identity after focused tests."""
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
from odsp.training_process_freeze_manifest import _file_sha256
from odsp.training_process_internal_freeze_v1 import MANAGED_INTERNAL_SURFACE


ARTIFACTS = (
    "ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_VALIDATION_CONTRACT.json",
    "ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_VALIDATION_CONTRACT_V2.json",
    "ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_PROMOTION_GATE.json",
    "ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_PROMOTION_GATE_V2.json",
    "ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_PROMOTION_GATE_V3.json",
    "ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_IDENTITY_CONTRACT.json",
    "ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_FOCUSED_RECEIPT_CONTRACT.json",
)


def build_snapshot() -> dict[str, object]:
    return {
        "schema_version": 1,
        "canonical_surface": MANAGED_INTERNAL_SURFACE,
        "implementation_lock_id": IMPLEMENTATION_LOCK_ID,
        "implementation_source_snapshot": [
            dict(row)
            for row in implementation_source_snapshot_for_surface(
                MANAGED_INTERNAL_SURFACE
            )
        ],
        "runtime_environment_lock_id": ENVIRONMENT_LOCK_ID,
        "runtime_environment_snapshot": runtime_environment_snapshot_for_surface(
            MANAGED_INTERNAL_SURFACE
        ),
        "contract_sha256": {
            artifact: _file_sha256(Path(artifact))
            for artifact in ARTIFACTS
        },
    }


def main() -> None:
    payload = build_snapshot()
    path = Path("/tmp/training-process-v5-managed-internal-identity.json")
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
