from __future__ import annotations

import json
from pathlib import Path

from odsp.confirmatory_method_routing import route_confirmatory_method


CONTRACT = Path("ODSP_UNTOUCHED_EXTERNAL_INDEPENDENT_ALL_REFIT_LATTICE_V2_CONTRACT.json")


def test_machine_contract_freezes_independent_external_four_and_twelve_edge_scope():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["lattice_scope"]["supported_information_block_counts"] == [2, 3]
    assert payload["lattice_scope"]["supported_edge_counts"] == [4, 12]
    assert payload["lattice_scope"]["thirty_two_or_more_edge_family_supported"] is False
    assert payload["external_validation"]["confirmatory_route_frozen"] is True
    assert payload["external_validation"]["qualification_evidence_content_frozen"] is True
    assert payload["external_validation"]["implementation_identity_frozen"] is True
    assert payload["refit_boundary"]["refit_population_generalization_claimed"] is False


def test_router_promotes_frozen_fixed_set_independent_external_lattice_for_qualified_families():
    for blocks, edges in ((2, 4), (3, 12)):
        route = route_confirmatory_method(
            alternative="greater",
            validation_design="independent_groups",
            information_structure="complete_lattice",
            upstream_refits="fixed_set",
            external_validation="untouched_frozen",
            information_block_count=blocks,
        )
        assert route.role == "primary_confirmatory"
        assert route.edge_count == edges
        assert route.canonical_surface == (
            "odsp.untouched_external_refit_independent_positive_lattice_contract_v2."
            "run_untouched_external_independent_all_refit_lattice_contract_v2"
        )
        assert route.qualification_evidence
        assert route.requires_preoutcome_freeze is True

    larger = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=4,
    )
    assert larger.role == "unqualified"
    assert larger.edge_count == 32
