from __future__ import annotations

import json
from pathlib import Path

from odsp.confirmatory_method_routing import route_confirmatory_method


CONTRACT = Path("ODSP_UNTOUCHED_EXTERNAL_INDEPENDENT_ALL_REFIT_LATTICE_V1_CONTRACT.json")


def test_machine_contract_freezes_independent_external_four_edge_scope():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["lattice_scope"]["supported_information_block_counts"] == [2]
    assert payload["lattice_scope"]["supported_edge_counts"] == [4]
    assert payload["lattice_scope"]["twelve_edge_family_supported"] is False
    assert payload["validation_design"]["independent_groups"] is True
    assert payload["external_validation"]["row_design_metadata_frozen"] is True
    assert payload["refit_boundary"]["refit_population_generalization_claimed"] is False
    assert payload["qualification_inheritance"]["fixed_set_all_refit_contract"] == "ODSP_ALL_REFIT_INDEPENDENT_DIRECTIONAL_LATTICE_4EDGE_CONTRACT.json"


def test_router_promotes_only_frozen_fixed_set_independent_external_lattice():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=2,
    )
    assert route.role == "primary_confirmatory"
    assert route.canonical_surface == (
        "odsp.untouched_external_refit_independent_positive_lattice_contract_v1."
        "run_untouched_external_independent_all_refit_lattice_contract_v1"
    )
    assert route.cli_sequence == (
        "odsp freeze-refits-external-independent-lattice",
        "odsp transfer-refits-external-independent-lattice",
    )

    larger = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=3,
    )
    assert larger.role == "unqualified"
    assert larger.edge_count == 12
