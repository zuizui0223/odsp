from __future__ import annotations

import json
from pathlib import Path

from odsp.confirmatory_method_routing import route_confirmatory_method
from odsp.confirmatory_route_evidence import (
    CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY,
    qualification_evidence_for_route_key,
)


REGISTRY = Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V2.json")


def test_independent_four_and_twelve_edge_routes_have_distinct_evidence_chains():
    four = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="none",
        external_validation="none",
        information_block_count=2,
    )
    twelve = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="none",
        external_validation="none",
        information_block_count=3,
    )
    assert four.canonical_surface == twelve.canonical_surface
    assert four.edge_count == 4
    assert twelve.edge_count == 12
    assert four.qualification_key != twelve.qualification_key
    assert four.qualification_evidence != twelve.qualification_evidence
    assert "INDEPENDENT_C4_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json" in four.qualification_evidence
    assert "INDEPENDENT_C12_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json" not in four.qualification_evidence
    assert "INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json" not in four.qualification_evidence
    assert "INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json" in twelve.qualification_evidence
    assert "INDEPENDENT_C12_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json" not in twelve.qualification_evidence


def test_all_refit_independent_lattice_evidence_tracks_family_size():
    four = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="none",
        information_block_count=2,
    )
    twelve = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="none",
        information_block_count=3,
    )
    common = "ODSP_ALL_REFIT_INDEPENDENT_DIRECTIONAL_LATTICE_4_12EDGE_CONTRACT.json"
    assert common in four.qualification_evidence
    assert common in twelve.qualification_evidence
    assert "INDEPENDENT_C4_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json" in four.qualification_evidence
    assert "INDEPENDENT_C12_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json" not in four.qualification_evidence
    assert "INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json" in twelve.qualification_evidence
    assert "INDEPENDENT_C12_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json" not in twelve.qualification_evidence


def test_independent_c4_filtration_carries_support_envelope_evidence():
    c2 = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="none",
        external_validation="none",
        contrast_count=2,
    )
    c4 = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="none",
        external_validation="none",
        contrast_count=4,
    )
    assert c2.qualification_key != c4.qualification_key
    assert c2.qualification_evidence == (
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
    )
    assert c4.qualification_evidence == (
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
        "INDEPENDENT_C4_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json",
    )


def test_paired_external_lattice_evidence_is_route_specific_and_frozen():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=3,
    )
    assert route.qualification_evidence == (
        "PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json",
        "ODSP_ALL_REFIT_PAIRED_POSITIVE_LATTICE_CONTRACT.json",
        "ODSP_UNTOUCHED_EXTERNAL_PAIRED_ALL_REFIT_LATTICE_V4_CONTRACT.json",
    )


def test_independent_external_lattice_evidence_is_family_specific_and_frozen():
    four = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=2,
    )
    twelve = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=3,
    )
    external = "ODSP_UNTOUCHED_EXTERNAL_INDEPENDENT_ALL_REFIT_LATTICE_V5_CONTRACT.json"
    assert four.role == "primary_confirmatory"
    assert twelve.role == "primary_confirmatory"
    assert four.qualification_evidence[-1] == external
    assert twelve.qualification_evidence[-1] == external
    assert "INDEPENDENT_C4_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json" in four.qualification_evidence
    assert "INDEPENDENT_C12_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json" not in four.qualification_evidence
    assert "INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json" in twelve.qualification_evidence
    assert "INDEPENDENT_C12_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json" in twelve.qualification_evidence
    assert four.qualification_key != twelve.qualification_key


def test_unqualified_and_sensitivity_routes_have_no_qualification_chain():
    unqualified = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="none",
        external_validation="none",
        information_block_count=4,
    )
    sensitivity = route_confirmatory_method(
        alternative="two_sided",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="fixed_set",
        external_validation="none",
        contrast_count=2,
    )
    assert unqualified.qualification_key is None
    assert unqualified.qualification_evidence == ()
    assert sensitivity.qualification_key is None
    assert sensitivity.qualification_evidence == ()


def test_historical_v2_registry_is_retained_as_a_current_registry_subset():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["registry_id"] == "odsp-confirmatory-route-evidence-v2"
    historical = payload["evidence_by_route_key"]
    assert historical
    for key, chain in historical.items():
        assert key in CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY
        assert list(CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY[key]) == chain

    for key, evidence in CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY.items():
        assert qualification_evidence_for_route_key(key) == evidence
        assert evidence
        for path in evidence:
            assert Path(path).is_file(), f"{key} references missing evidence {path}"


def test_registry_family_scope_matches_frozen_receipts():
    one_sided = json.loads(
        Path("ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json").read_text()
    )
    assert {int(row["contrast_count"]) for row in one_sided["scenarios"]} == {2, 4}

    c4 = json.loads(
        Path("INDEPENDENT_C4_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json").read_text()
    )
    assert c4["summary"]["support_anchor_counts"] == [8, 20, 50]
    assert c4["summary"]["qualification_pass"] is True

    c12 = json.loads(
        Path("INDEPENDENT_C12_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json").read_text()
    )
    assert c12["summary"]["support_anchor_counts"] == [8, 20, 50]
    assert c12["summary"]["group_count_anchor"] == 6
    assert c12["summary"]["contrast_count"] == 12
    assert c12["summary"]["qualification_pass"] is True

    independent_lattice = json.loads(
        Path("INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json").read_text()
    )
    assert independent_lattice["scientific_boundary"]["qualified_edge_family_sizes"] == [4, 12]

    paired_lattice = json.loads(
        Path("PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json").read_text()
    )
    assert paired_lattice["scientific_boundary"]["qualified_edge_family_sizes"] == [4, 12]


def test_training_process_v5_route_has_distinct_frozen_evidence_chain():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="none",
        contrast_count=2,
    )
    assert route.role == "primary_confirmatory"
    assert route.qualification_evidence == (
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


def test_active_v4_registry_matches_training_process_route_and_hashes():
    payload = json.loads(
        Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V4.json").read_text(
            encoding="utf-8"
        )
    )
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="none",
        contrast_count=2,
    )
    assert payload["registry_id"] == "odsp-confirmatory-route-evidence-v4"
    assert payload["evidence_by_route_key"][route.qualification_key] == list(
        route.qualification_evidence
    )
    for artifact in route.qualification_evidence:
        assert payload["artifact_sha256"][artifact]
        assert len(payload["artifact_sha256"][artifact]) == 64


def test_unknown_route_key_has_no_evidence():
    assert qualification_evidence_for_route_key("future|unknown") == ()


def test_routing_contract_freezes_route_context_evidence_governance():
    payload = json.loads(
        Path("ODSP_CONFIRMATORY_METHOD_ROUTING_CONTRACT.json").read_text(encoding="utf-8")
    )
    evidence = payload["qualification_evidence"]
    assert evidence["registry"] == "ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V6.json"
    assert evidence["artifact_sha256_frozen"] is True
    assert evidence["keyed_by_full_route_context"] is True
    assert evidence["surface_name_alone_is_sufficient"] is False
    assert evidence["missing_evidence_policy"] == "unqualified"
    assert evidence["runtime_recomputes_calibration"] is False


def test_training_process_external_v5_chain_extends_internal_chain_without_replacement():
    internal = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="none",
        contrast_count=2,
    )
    external = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="untouched_frozen",
        contrast_count=2,
    )
    assert external.role == "primary_confirmatory"
    assert external.qualification_evidence[: len(internal.qualification_evidence)] == (
        internal.qualification_evidence
    )
    assert external.qualification_evidence[len(internal.qualification_evidence):] == (
        "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT.json",
        "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT_V2.json",
        "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT_V3.json",
        "ODSP_TRAINING_PROCESS_V5_MANAGED_EXTERNAL_SCORING_CONTRACT.json",
        "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE.json",
        "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE_V2.json",
        "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE_V3.json",
        "ODSP_TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_CONTRACT_V2.json",
        "TRAINING_PROCESS_V5_EXTERNAL_FOCUSED_ENDPOINT_RECEIPT_V2.json",
        "TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_RECEIPT_V2.json",
        "ODSP_TRAINING_PROCESS_V5_EXTERNAL_ROUTE_PROMOTION_CONTRACT.json",
        "TRAINING_PROCESS_V5_EXTERNAL_EVIDENCE_HASH_RECEIPT.json",
        "ODSP_TRAINING_PROCESS_V5_EXTERNAL_REGISTRATION_CORRECTION_CONTRACT.json",
    )
    assert len(external.qualification_evidence) == 23


def test_historical_v5_registry_is_retained_as_prefix_before_chronology_correction():
    payload = json.loads(
        Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V5.json").read_text(
            encoding="utf-8"
        )
    )
    external = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="untouched_frozen",
        contrast_count=2,
    )
    frozen = payload["evidence_by_route_key"][external.qualification_key]
    assert payload["schema_version"] == 5
    assert payload["registry_id"] == "odsp-confirmatory-route-evidence-v5"
    assert len(frozen) == 20
    assert list(external.qualification_evidence[:20]) == frozen
    assert list(external.qualification_evidence[20:]) == [
        "ODSP_TRAINING_PROCESS_V5_EXTERNAL_ROUTE_PROMOTION_CONTRACT.json",
        "TRAINING_PROCESS_V5_EXTERNAL_EVIDENCE_HASH_RECEIPT.json",
        "ODSP_TRAINING_PROCESS_V5_EXTERNAL_REGISTRATION_CORRECTION_CONTRACT.json",
    ]
    for artifact in frozen:
        digest = payload["artifact_sha256"][artifact]
        assert len(digest) == 64
        int(digest, 16)


def test_v4_registry_is_retained_as_subset_of_active_v5_registry():
    old = json.loads(
        Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V4.json").read_text(
            encoding="utf-8"
        )
    )
    new = json.loads(
        Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V5.json").read_text(
            encoding="utf-8"
        )
    )
    for key, chain in old["evidence_by_route_key"].items():
        assert new["evidence_by_route_key"][key] == chain
    for artifact, digest in old["artifact_sha256"].items():
        assert new["artifact_sha256"][artifact] == digest


def test_active_v6_registry_reactivates_external_chain_after_official_hash_replay():
    old = json.loads(
        Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V5.json").read_text(
            encoding="utf-8"
        )
    )
    new = json.loads(
        Path("ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V6.json").read_text(
            encoding="utf-8"
        )
    )
    external = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="untouched_frozen",
        contrast_count=2,
    )
    key = external.qualification_key
    assert new["schema_version"] == 6
    assert new["registry_id"] == "odsp-confirmatory-route-evidence-v6"
    assert new["evidence_by_route_key"][key] == list(external.qualification_evidence)
    for old_key, old_chain in old["evidence_by_route_key"].items():
        if old_key == key:
            assert new["evidence_by_route_key"][old_key][: len(old_chain)] == old_chain
        else:
            assert new["evidence_by_route_key"][old_key] == old_chain
    for artifact, digest in old["artifact_sha256"].items():
        assert new["artifact_sha256"][artifact] == digest
    assert set(new["artifact_sha256"]) - set(old["artifact_sha256"]) == {
        "ODSP_TRAINING_PROCESS_V5_EXTERNAL_ROUTE_PROMOTION_CONTRACT.json",
        "TRAINING_PROCESS_V5_EXTERNAL_EVIDENCE_HASH_RECEIPT.json",
        "ODSP_TRAINING_PROCESS_V5_EXTERNAL_REGISTRATION_CORRECTION_CONTRACT.json",
    }
    governance = new["governance"]
    assert governance["registry_v5_retained_for_historical_provenance"] is True
    assert governance["registry_v5_external_registration_met_strict_hash_replay_order"] is False
    assert governance["registry_v6_created_after_official_external_hash_replay"] is True
    assert governance["external_hash_replay_run_id"] == 37306487541
    assert governance["external_activation_meta_evidence_content_locked"] is True
