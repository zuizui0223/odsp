"""Immutable internal-v5 qualification snapshot for external route composition.

This module deliberately does not import the live confirmatory routing registry.
The external v5 endpoint verifies the exact internal evidence chain that had
already been qualified before the external route was registered.  That avoids a
self-reference in which adding the external route to the live registry would
change the external endpoint's own frozen implementation closure.
"""
from __future__ import annotations

from pathlib import Path

from .training_process_freeze_manifest import _file_sha256


INTERNAL_V5_CANONICAL_SURFACE = (
    "odsp.training_process_confirmatory_v5."
    "certify_predeclared_training_process_positive_information_v5"
)
INTERNAL_V5_QUALIFICATION_KEY = (
    "alternative=greater|validation_design=independent_groups|"
    "information_structure=filtration|"
    "upstream_refits=predeclared_training_process|"
    "external_validation=none|contrast_count=2"
)
INTERNAL_V5_QUALIFICATION_REGISTRY_ID = "odsp-confirmatory-route-evidence-v4"
_REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

INTERNAL_V5_EVIDENCE: tuple[tuple[str, str], ...] = (
    (
        "ODSP_TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_CONTRACT.json",
        "f82180186bbc333244b80625c67394cd6117c0c75d028caf580e5e9a6cc689af",
    ),
    (
        "TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_QUALIFICATION_RECEIPT.json",
        "f813acc7b9c57bc0b621bc823ee7bd1d45fe68af05a4d645729cb903c8da41ea",
    ),
    (
        "ODSP_TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_CONTRACT.json",
        "67cbb1da0f76a82cb879ef555f58adc20348656b1713db449aa96cdb7b452394",
    ),
    (
        "TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_RECEIPT.json",
        "5880800bd80bf691b6cbfb880b27af29218fe5d260595658d4c878872f15031d",
    ),
    (
        "ODSP_TRAINING_PROCESS_V5_PRIMARY_PROMOTION_GATE.json",
        "05bebc8627c83e94cc6d1d54657083987b4fe5ba01876faf6c57aa7138fdd57e",
    ),
    (
        "ODSP_TRAINING_PROCESS_V5_PRIMARY_PROMOTION_GATE_V2.json",
        "92d25f7ab3979ebbf1f98eab3df142c820750bbd67a38f7ea001eb0b9a017dbc",
    ),
    (
        "ODSP_TRAINING_PROCESS_MANAGED_GENERATION_CONTRACT.json",
        "dd63556b8be22d3dee405b8071238d64db22b4d0382b739d37eb29e617f9afbb",
    ),
    (
        "ODSP_TRAINING_PROCESS_VALIDATION_FRAME_PROVENANCE_CONTRACT.json",
        "a0ec68a9cb2a83399f8b861ac217eaf0c02c23a8458cbc36c74da42210e48999",
    ),
    (
        "ODSP_TRAINING_PROCESS_V5_QUALIFICATION_IDENTITY_CONTRACT.json",
        "86e185703e40d8ca33ecf81a7376587bfe85e1ab5b295cd8e32499f34f740227",
    ),
    (
        "TRAINING_PROCESS_V5_QUALIFICATION_IDENTITY_RECEIPT.json",
        "c6cbe36f2581b0c1b5ec2fe9e4670a887b07f7a491a567cd9fd4f3c304a12278",
    ),
)


def build_internal_v5_qualification_snapshot() -> dict[str, object]:
    """Verify and return the immutable internal-v5 evidence snapshot."""

    artifacts: list[dict[str, str]] = []
    for artifact, expected_sha256 in INTERNAL_V5_EVIDENCE:
        path = _REPOSITORY_ROOT / artifact
        if not path.is_file():
            raise FileNotFoundError(path)
        observed = _file_sha256(path)
        if observed != expected_sha256:
            raise ValueError(
                "internal v5 qualification evidence content mismatch: "
                f"{artifact}; expected={expected_sha256}, observed={observed}"
            )
        artifacts.append({"artifact": artifact, "sha256": observed})

    return {
        "role": "primary_confirmatory",
        "canonical_surface": INTERNAL_V5_CANONICAL_SURFACE,
        "qualification_key": INTERNAL_V5_QUALIFICATION_KEY,
        "qualification_registry_id": INTERNAL_V5_QUALIFICATION_REGISTRY_ID,
        "qualification_evidence": [
            artifact for artifact, _ in INTERNAL_V5_EVIDENCE
        ],
        "qualification_evidence_artifacts": artifacts,
    }
