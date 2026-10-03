from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from odsp.confirmatory_route_evidence import (
    CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY,
    QUALIFICATION_EVIDENCE_SHA256_BY_ARTIFACT,
    qualification_evidence_artifacts_for_route_key,
)
from odsp.frozen_confirmatory_route import (
    build_frozen_confirmatory_route,
    verify_frozen_confirmatory_route,
)


REGISTRY = Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V3.json")
CONTENT_LOCK = Path("ODSP_CONFIRMATORY_EVIDENCE_CONTENT_LOCK_V1.json")
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


def test_ordered_evidence_snapshot_preserves_route_chain():
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
    frozen = build_frozen_confirmatory_route(
        validation_design="independent_groups",
        information_structure="filtration",
        contrast_count=2,
    )
    key = frozen["qualification_key"]
    artifact = frozen["qualification_evidence"][0]
    monkeypatch.delitem(
        QUALIFICATION_EVIDENCE_SHA256_BY_ARTIFACT,
        artifact,
        raising=True,
    )
    with pytest.raises(ValueError, match="SHA256"):
        qualification_evidence_artifacts_for_route_key(key)


def test_v3_registry_matches_code_registry_and_content_digests():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 3
    assert payload["registry_id"] == "odsp-confirmatory-route-evidence-v3"
    assert payload["evidence_by_route_key"] == {
        key: list(value)
        for key, value in sorted(CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY.items())
    }
    assert payload["artifact_sha256"] == dict(
        sorted(QUALIFICATION_EVIDENCE_SHA256_BY_ARTIFACT.items())
    )
    assert payload["governance"]["artifact_content_identity_frozen"] is True
    assert payload["governance"]["same_filename_changed_content_detected"] is True


def test_content_lock_contract_freezes_exact_ordered_artifact_digests():
    payload = json.loads(CONTENT_LOCK.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["contract_id"] == "odsp-confirmatory-evidence-content-lock-v1"
    assert payload["freeze"]["artifact_name_frozen"] is True
    assert payload["freeze"]["artifact_sha256_frozen"] is True
    assert payload["freeze"]["evidence_order_is_semantic"] is True
    assert payload["runtime"]["exact_snapshot_match_required"] is True
    assert payload["runtime"]["same_filename_changed_content_allowed"] is False
    assert payload["historical_governance"]["empirical_endpoint_rerun"] is False
    assert payload["historical_governance"]["terminal_reclassification"] is False
    assert payload["migration"]["legacy_manifest_auto_upgrade_allowed"] is False
    assert payload["migration"]["post_outcome_retroactive_upgrade_allowed"] is False
    assert payload["migration"]["pre_outcome_regeneration_allowed"] is True


def test_dedicated_content_lock_workflow_watches_every_registered_artifact():
    workflow = Path(".github/workflows/freeze-confirmatory-evidence-content-v4.yml").read_text(
        encoding="utf-8"
    )
    for artifact in sorted(_all_registered_artifacts()):
        assert artifact in workflow, (
            "dedicated content-lock workflow does not watch registered evidence artifact "
            f"{artifact}"
        )


def test_routing_contract_points_to_content_locked_v3_registry():
    payload = json.loads(ROUTING_CONTRACT.read_text(encoding="utf-8"))
    assert payload["qualification_evidence"]["registry"] == (
        "ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V3.json"
    )
    assert payload["qualification_evidence"]["artifact_sha256_frozen"] is True
