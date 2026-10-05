"""Print exact SHA256s for the frozen training-process v5 evidence chain."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ARTIFACTS = (
    "ODSP_TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_CONTRACT.json",
    "TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_QUALIFICATION_RECEIPT.json",
    "TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_RECEIPT.json",
    "TRAINING_PROCESS_V5_QUALIFICATION_IDENTITY_RECEIPT.json",
    "ODSP_TRAINING_PROCESS_MANAGED_GENERATION_CONTRACT.json",
    "ODSP_TRAINING_PROCESS_VALIDATION_FRAME_PROVENANCE_CONTRACT.json",
    "ODSP_TRAINING_PROCESS_V5_PRIMARY_PROMOTION_GATE.json",
)

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    payload = {name: sha256(Path(name)) for name in ARTIFACTS}
    print("TRAINING_PROCESS_V5_EVIDENCE_SHA256=" + json.dumps(payload, sort_keys=True))

if __name__ == "__main__":
    main()
