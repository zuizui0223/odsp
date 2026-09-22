from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path("ODSP_ALL_REFIT_INDEPENDENT_DIRECTIONAL_LATTICE_4_12EDGE_CONTRACT.json")


def test_contract_freezes_four_and_twelve_edge_fixed_set_scope():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["contract_id"] == "odsp-all-refit-independent-directional-lattice-4-12edge-v1"
    assert payload["qualified_information_block_counts"] == [2, 3]
    assert payload["qualified_edge_counts"] == [4, 12]
    assert payload["unqualified_next_edge_count"] == 32
    assert payload["intersection_union_rule_used"] is True
    assert payload["all_supplied_refits_must_pass_same_edge"] is True
    assert payload["different_refit_paths_can_be_combined"] is False
    assert payload["qualification_inheritance"]["source_contract"] == (
        "ODSP_INDEPENDENT_DIRECTIONAL_LATTICE_4_12EDGE_CONTRACT.json"
    )
    assert payload["qualification_inheritance"]["new_refit_population_fwer_claim"] is False
    assert payload["refit_boundary"]["refit_population_generalization_claimed"] is False
    assert payload["untouched_external_validation_included"] is False
