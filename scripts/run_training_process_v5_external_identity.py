"""Snapshot the exact qualified external training-process v5 implementation."""
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
from odsp.training_process_external_freeze_v1 import (
    EXTERNAL_SURFACE,
    build_internal_v5_route_snapshot,
)
from odsp.training_process_freeze_manifest import _file_sha256


CONTRACTS = (
    "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT.json",
    "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT_V2.json",
    "ODSP_TRAINING_PROCESS_V5_MANAGED_EXTERNAL_SCORING_CONTRACT.json",
    "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE.json",
    "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE_V2.json",
    "ODSP_TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_CONTRACT_V2.json",
    "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT_V3.json",
    "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE_V3.json",
)


def build_snapshot() -> dict[str, object]:
    return {
        "schema_version": 2,
        "canonical_surface": EXTERNAL_SURFACE,
        "implementation_lock_id": IMPLEMENTATION_LOCK_ID,
        "implementation_source_snapshot": [
            dict(row)
            for row in implementation_source_snapshot_for_surface(
                EXTERNAL_SURFACE
            )
        ],
        "runtime_environment_lock_id": ENVIRONMENT_LOCK_ID,
        "runtime_environment_snapshot": (
            runtime_environment_snapshot_for_surface(EXTERNAL_SURFACE)
        ),
        "internal_v5_route_snapshot": build_internal_v5_route_snapshot(),
        "external_contract_sha256": {
            path: _file_sha256(Path(path)) for path in CONTRACTS
        },
    }


def main() -> None:
    payload = build_snapshot()
    Path("/tmp/training-process-v5-external-identity.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        "TRAINING_PROCESS_V5_EXTERNAL_IDENTITY="
        + json.dumps(payload, sort_keys=True)
    )


if __name__ == "__main__":
    main()
