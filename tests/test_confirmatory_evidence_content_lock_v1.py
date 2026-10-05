from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from odsp.confirmatory_route_evidence import (
    CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY,
    QUALIFICATION_EVIDENCE_SHA256_BY_ARTIFACT,
    qualification_evidence_artifacts_for_route_key,
    route_evidence_key,
)
from odsp.frozen_confirmatory_route import (
    build_frozen_confirmatory_route,
    verify_frozen_confirmatory_route,
)


REGISTRY_V3 = Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V3.json")
REGISTRY_V4 = Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V4.json")
REGISTRY_V5 = Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V5.json")
REGISTRY_V6 = Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V6.json")
CONTENT_LOCK_V1 = Path("ODSP_CONFIRMATORY_EVIDENCE_CONTENT_LOCK_V1.json")
CONTENT_LOCK_V2 = Path("ODSP_CONFIRMATORY_EVIDENCE_CONTENT_LOCK_V2.json")
CONTENT_LOCK_V3 = Path("ODSP_CONFIRMATORY_EVIDENCE_CONTENT_LOCK_V3.json")
CONTENT_LOCK_V4 = Path("ODSP_CONFIRMATORY_EVIDENCE_CONTENT_LOCK_V4.json")
ROUTING_CONTRACT = Path("ODSP_CONFIRMATORY_METHOD_ROUTING_CONTRACT.json")


def _all_registered_artifacts() -> set[str]:
    return {
        artifact
        for chain in CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY.values()
        for artifact in chain
    }


def test_every_registered_qualification_artifact_has_exact_source_sha256():
    artifacts = _all_registered_artifacts()
    assert artifacts == set(QUALIFICATION_EVIDENCE_SHA256_BY_ARTIFACT)
    for artifact in sorted(artifacts):
        expected = QUALIFICATION_EVIDENCE_SHA256_BY_ARTIFACT[artifact]
        assert len(expected) == 64
        assert expected == expected.lower()
        actual = hashlib.sha256(Path(artifact).read_bytes()).hexdigest()
        assert actual == expected, artifact


def test_ordered_evidence_snapshot_preserves_existing_route_chain():
    route = build_frozen_confirmatory_route(
        validation_design="independent_groups",
        information_structure="filtration",
        contrast_count=4,
    )
    assert route["qualification_evidence"]
    snapshot = route["qualification_evidence_artifacts"]
    assert [row["artifact"] for row in snapshot] == route["qualification_evidence"]
    assert [row["sha256"] for row in snapshot] == [
        QUALIFICATION_EVIDENCE_SHA256_BY_ARTIFACT[name]
        for name in route["qualification_evidence"]
    ]


def test_training_process_route_has_complete_ordered_v5_evidence_chain():
    key = route_evidence_key(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="none",
        contrast_count=2,
    )
    evidence = CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY[key]
    assert evidence == (
        "ODSP_TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_CONTRACT.json",
        "TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_QUALIFICATION_RECEIPT.json",
        "ODSP_TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_CONTRACT.json",
        "TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_RECEIPT.json",
        "ODSP_TRAINING_PROCESS_V5_PRIMARY_PROMOTION_GATE.json",
        "ODSP_TRAINING_PROCESS_V5_PRIMARY_PROMOTION_GATE_V2.json",
        "ODSP_TRAINING_PROCESS_MANAGED_GENERATION_CONTRACT.json",
        "ODSP_TRAINING_PROCESS_VALIDATION_FRAME_PROVENANCE_CONTRACT.json",
        "ODSP_TRAINING_PROCESS_V5_QUALIFICATION_IDENTITY_CONTRACT.json",
        "TRAINING_PROCESS_V5_QUALIFICATION_IDENTITY_RECEIPT.json",
    )
    snapshot = qualification_evidence_artifacts_for_route_key(key)
    assert [row["artifact"] for row in snapshot] == list(evidence)


def test_runtime_rejects_same_artifact_names_with_tampered_content_digest():
    frozen = build_frozen_confirmatory_route(
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        information_block_count=3,
    )
    tampered = json.loads(json.dumps(frozen))
    tampered["qualification_evidence_artifacts"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="confirmatory_route"):
        verify_frozen_confirmatory_route(
            tampered,
            validation_design="paired_shared_blocks",
            information_structure="complete_lattice",
            information_block_count=3,
        )


def test_snapshot_builder_fails_closed_when_route_evidence_digest_is_missing(monkeypatch):
    key = route_evidence_key(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="none",
        contrast_count=2,
    )
    artifact = CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY[key][0]
    monkeypatch.delitem(
        QUALIFICATION_EVIDENCE_SHA256_BY_ARTIFACT,
        artifact,
        raising=True,
    )
    with pytest.raises(ValueError, match="SHA256"):
        qualification_evidence_artifacts_for_route_key(key)


def test_historical_v5_registry_is_retained_without_rewrite():
    old = json.loads(REGISTRY_V5.read_text(encoding="utf-8"))
    new = json.loads(REGISTRY_V6.read_text(encoding="utf-8"))
    assert old["schema_version"] == 5
    assert old["registry_id"] == "odsp-confirmatory-route-evidence-v5"
    assert old["governance"]["artifact_content_identity_frozen"] is True
    assert old["governance"]["same_filename_changed_content_detected"] is True
    for key, chain in old["evidence_by_route_key"].items():
        assert new["evidence_by_route_key"][key][: len(chain)] == chain
    for artifact, digest in old["artifact_sha256"].items():
        assert new["artifact_sha256"][artifact] == digest


def test_v4_registry_is_retained_for_historical_provenance():
    old = json.loads(REGISTRY_V4.read_text(encoding="utf-8"))
    new = json.loads(REGISTRY_V5.read_text(encoding="utf-8"))
    assert old["schema_version"] == 4
    assert old["registry_id"] == "odsp-confirmatory-route-evidence-v4"
    for key, chain in old["evidence_by_route_key"].items():
        assert new["evidence_by_route_key"][key] == chain
    for artifact, digest in old["artifact_sha256"].items():
        assert new["artifact_sha256"][artifact] == digest


def test_v3_registry_is_retained_as_historical_artifact():
    payload = json.loads(REGISTRY_V3.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 3
    assert payload["registry_id"] == "odsp-confirmatory-route-evidence-v3"
    assert all(
        "predeclared_training_process" not in key
        for key in payload["evidence_by_route_key"]
    )


def test_historical_content_lock_v3_is_retained_for_process_external_evidence():
    payload = json.loads(CONTENT_LOCK_V3.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 3
    assert payload["contract_id"] == "odsp-confirmatory-evidence-content-lock-v3"
    assert payload["composes_with"]["evidence_registry"] == (
        "odsp-confirmatory-route-evidence-v5"
    )
    assert payload["freeze"]["artifact_name_frozen"] is True
    assert payload["freeze"]["artifact_sha256_frozen"] is True
    assert payload["freeze"]["evidence_order_is_semantic"] is True
    assert payload["runtime"]["exact_snapshot_match_required"] is True
    assert payload["runtime"]["same_filename_changed_content_allowed"] is False
    assert payload["scope"]["training_process_external_c2_route_included"] is True
    assert payload["historical_governance"][
        "evidence_content_lock_v2_deleted_or_rewritten"
    ] is False


def test_content_lock_v2_is_retained_for_historical_provenance():
    payload = json.loads(CONTENT_LOCK_V2.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["contract_id"] == "odsp-confirmatory-evidence-content-lock-v2"


def test_v1_content_lock_is_retained_for_historical_provenance():
    payload = json.loads(CONTENT_LOCK_V1.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["contract_id"] == "odsp-confirmatory-evidence-content-lock-v1"


def test_dedicated_active_content_lock_workflow_watches_every_registered_artifact():
    workflow = Path(".github/workflows/freeze-confirmatory-evidence-content-v6.yml").read_text(
        encoding="utf-8"
    )
    for artifact in sorted(_all_registered_artifacts()):
        assert artifact in workflow, (
            "active content-lock workflow does not watch registered evidence artifact "
            f"{artifact}"
        )
    assert "ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V6.json" in workflow
    assert "ODSP_CONFIRMATORY_EVIDENCE_CONTENT_LOCK_V4.json" in workflow


def test_routing_contract_points_to_content_locked_v6_registry():
    payload = json.loads(ROUTING_CONTRACT.read_text(encoding="utf-8"))
    assert payload["qualification_evidence"]["registry"] == (
        "ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V6.json"
    )
    assert payload["qualification_evidence"]["content_lock_contract"] == (
        "ODSP_CONFIRMATORY_EVIDENCE_CONTENT_LOCK_V4.json"
    )
    assert payload["qualification_evidence"]["artifact_sha256_frozen"] is True
    assert payload["qualification_evidence"]["registry_v5_retained_for_historical_provenance"] is True
    assert payload["qualification_evidence"]["external_v5_initial_registration_met_strict_hash_replay_order"] is False
    assert payload["qualification_evidence"]["external_v6_registration_after_official_hash_replay"] is True


def test_v6_registry_matches_active_code_registry_and_content_digests():
    payload = json.loads(REGISTRY_V6.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 6
    assert payload["registry_id"] == "odsp-confirmatory-route-evidence-v6"
    assert payload["evidence_by_route_key"] == {
        key: list(value)
        for key, value in sorted(CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY.items())
    }
    assert payload["artifact_sha256"] == dict(
        sorted(QUALIFICATION_EVIDENCE_SHA256_BY_ARTIFACT.items())
    )


def test_content_lock_v4_freezes_corrected_active_registry():
    payload = json.loads(CONTENT_LOCK_V4.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 4
    assert payload["contract_id"] == "odsp-confirmatory-evidence-content-lock-v4"
    assert payload["composes_with"]["evidence_registry"] == (
        "odsp-confirmatory-route-evidence-v6"
    )
    assert payload["historical_governance"]["evidence_registry_v5_deleted_or_rewritten"] is False
    assert payload["historical_governance"]["evidence_content_lock_v3_deleted_or_rewritten"] is False
