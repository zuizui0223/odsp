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
    assert "INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json" not in four.qualification_evidence
    assert "INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json" in twelve.qualification_evidence


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
    assert "INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json" in twelve.qualification_evidence


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


def test_registry_matches_python_and_all_evidence_files_exist():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["registry_id"] == "odsp-confirmatory-route-evidence-v2"
    assert payload["evidence_by_route_key"] == {
        key: list(value)
        for key, value in sorted(CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY.items())
    }
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

    independent_lattice = json.loads(
        Path("INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json").read_text()
    )
    assert independent_lattice["scientific_boundary"]["qualified_edge_family_sizes"] == [4, 12]

    paired_lattice = json.loads(
        Path("PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json").read_text()
    )
    assert paired_lattice["scientific_boundary"]["qualified_edge_family_sizes"] == [4, 12]


def test_unknown_route_key_has_no_evidence():
    assert qualification_evidence_for_route_key("future|unknown") == ()
