"""Snapshot the qualified training-process v5 implementation and runtime identity."""
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

SURFACE = "odsp.training_process_confirmatory_v5.certify_predeclared_training_process_positive_information_v5"


def main() -> None:
    payload = {
        "schema_version": 1,
        "canonical_surface": SURFACE,
        "implementation_lock_id": IMPLEMENTATION_LOCK_ID,
        "implementation_source_snapshot": [
            dict(row) for row in implementation_source_snapshot_for_surface(SURFACE)
        ],
        "runtime_environment_lock_id": ENVIRONMENT_LOCK_ID,
        "runtime_environment_snapshot": runtime_environment_snapshot_for_surface(SURFACE),
    }
    Path("/tmp/training-process-v5-identity.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
