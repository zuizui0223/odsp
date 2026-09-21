from __future__ import annotations

import json
from pathlib import Path

from odsp.confirmatory_calibration_evidence import (
    CONFIRMATORY_EVIDENCE_BY_SURFACE,
    qualification_evidence_for_surface,
)
from odsp.confirmatory_method_routing import route_confirmatory_method


REGISTRY = Path("ODSP_CONFIRMATORY_CALIBRATION_EVIDENCE_REGISTRY.json")


def _json(path: str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _scenario_contrast_counts(path: str) -> set[int]:
    payload = _json(path)
    return {int(row["contrast_count"]) for row in payload["scenarios"] if "contrast_count" in row}


def test_router_independent_one_sided_filtration_scope_equals_frozen_receipt():
    qualified = _scenario_contrast_counts(
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json"
    )
    assert qualified == {2, 4}
    for count in range(1, 7):
        route = route_confirmatory_method(
            alternative="greater",
            validation_design="independent_groups",
            information_structure="filtration",
            upstream_refits="none",
            external_validation="none",
            contrast_count=count,
        )
        assert (route.role == "primary_confirmatory") is (count in qualified)


def test_router_paired_one_sided_filtration_scope_equals_frozen_receipt():
    payload = _json("PAIRED_ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json")
    qualified = {int(payload["first_1000_simulation_run"]["contrast_count"])}
    assert qualified == {2}
    for count in range(1, 6):
        route = route_confirmatory_method(
            alternative="greater",
            validation_design="paired_shared_blocks",
            information_structure="filtration",
            upstream_refits="none",
            external_validation="none",
            contrast_count=count,
        )
        assert (route.role == "primary_confirmatory") is (count in qualified)


def test_router_paired_lattice_scope_equals_frozen_receipt():
    payload = _json("PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json")
    qualified_edges = {
        int(value) for value in payload["scientific_boundary"]["qualified_edge_family_sizes"]
    }
    assert qualified_edges == {4, 12}
    for blocks in range(1, 5):
        edge_count = blocks * 2 ** (blocks - 1)
        route = route_confirmatory_method(
            alternative="greater",
            validation_design="paired_shared_blocks",
            information_structure="complete_lattice",
            upstream_refits="none",
            external_validation="none",
            information_block_count=blocks,
        )
        assert route.edge_count == edge_count
        assert (route.role == "primary_confirmatory") is (edge_count in qualified_edges)


def test_router_independent_two_sided_scope_equals_frozen_receipt():
    qualified = _scenario_contrast_counts(
        "MULTICONTRAST_BOOTSTRAP_T_V2_OPERATING_CHARACTERISTICS_RECEIPT.json"
    )
    assert qualified == {2, 4}
    for count in range(1, 7):
        route = route_confirmatory_method(
            alternative="two_sided",
            validation_design="independent_groups",
            information_structure="filtration",
            upstream_refits="none",
            external_validation="none",
            contrast_count=count,
        )
        assert (route.role == "bidirectional_confirmatory") is (count in qualified)

    for blocks in range(1, 5):
        edge_count = blocks * 2 ** (blocks - 1)
        route = route_confirmatory_method(
            alternative="two_sided",
            validation_design="independent_groups",
            information_structure="complete_lattice",
            upstream_refits="none",
            external_validation="none",
            information_block_count=blocks,
        )
        assert route.edge_count == edge_count
        assert (route.role == "bidirectional_confirmatory") is (edge_count in qualified)


def test_primary_routes_emit_exact_frozen_qualification_evidence():
    independent = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="none",
        external_validation="none",
        contrast_count=2,
    )
    assert independent.qualification_evidence == (
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
    )

    independent_lattice = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="none",
        external_validation="none",
        information_block_count=2,
    )
    assert independent_lattice.qualification_evidence == (
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
        "ODSP_INDEPENDENT_DIRECTIONAL_LATTICE_4EDGE_CONTRACT.json",
    )

    all_refit_independent_lattice = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="none",
        information_block_count=2,
    )
    assert all_refit_independent_lattice.qualification_evidence == (
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
        "ODSP_INDEPENDENT_DIRECTIONAL_LATTICE_4EDGE_CONTRACT.json",
        "ODSP_ALL_REFIT_INDEPENDENT_DIRECTIONAL_LATTICE_4EDGE_CONTRACT.json",
    )

    paired_external_lattice = route_confirmatory_method(
        alternative="greater",
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=3,
    )
    assert paired_external_lattice.qualification_evidence == (
        "PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json",
        "ODSP_ALL_REFIT_PAIRED_POSITIVE_LATTICE_CONTRACT.json",
        "ODSP_UNTOUCHED_EXTERNAL_PAIRED_ALL_REFIT_LATTICE_V4_CONTRACT.json",
    )


def test_bidirectional_route_emits_frozen_qualification_evidence():
    route = route_confirmatory_method(
        alternative="two_sided",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="none",
        external_validation="none",
        contrast_count=4,
    )
    assert route.qualification_evidence == (
        "MULTICONTRAST_BOOTSTRAP_T_V2_OPERATING_CHARACTERISTICS_RECEIPT.json",
    )


def test_unqualified_route_has_no_qualification_evidence():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=4,
    )
    assert route.role == "unqualified"
    assert route.qualification_evidence == ()


def test_evidence_registry_matches_python_registry_and_all_files_exist():
    payload = _json(str(REGISTRY))
    assert payload["schema_version"] == 1
    assert payload["registry_id"] == "odsp-confirmatory-calibration-evidence-v1"
    assert payload["surface_evidence"] == {
        key: list(value) for key, value in sorted(CONFIRMATORY_EVIDENCE_BY_SURFACE.items())
    }
    for surface, files in CONFIRMATORY_EVIDENCE_BY_SURFACE.items():
        assert qualification_evidence_for_surface(surface) == files
        for path in files:
            assert Path(path).is_file(), f"{surface} references missing evidence {path}"


def test_unknown_surface_has_no_qualification_evidence():
    assert qualification_evidence_for_surface("odsp.future.unknown") == ()
