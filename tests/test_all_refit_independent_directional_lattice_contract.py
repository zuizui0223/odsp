from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path("ODSP_ALL_REFIT_INDEPENDENT_DIRECTIONAL_LATTICE_4EDGE_CONTRACT.json")


def test_contract_freezes_fixed_set_intersection_logic():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["contract_id"] == "odsp-all-refit-independent-directional-lattice-4edge-v1"
    assert payload["information_block_count"] == 2
    assert payload["edge_count"] == 4
    assert payload["intersection_union_rule_used"] is True
    assert payload["all_supplied_refits_must_pass_same_edge"] is True
    assert payload["different_refit_paths_can_be_combined"] is False


def test_contract_does_not_turn_refits_into_probability_sample():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    boundary = payload["refit_boundary"]
    assert boundary["refit_independence_assumed"] is False
    assert boundary["refit_sampling_distribution_assumed"] is False
    assert boundary["refit_population_generalization_claimed"] is False
    assert boundary["additional_refit_axis_multiplicity_correction_applied"] is False


def test_contract_inherits_per_refit_four_edge_qualification():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    inheritance = payload["qualification_inheritance"]
    assert inheritance["source_contract"] == "ODSP_INDEPENDENT_DIRECTIONAL_LATTICE_4EDGE_CONTRACT.json"
    assert inheritance["new_refit_population_fwer_claim"] is False
    assert inheritance["per_refit_familywise_certification_required"] is True
    assert payload["untouched_external_validation_included"] is False
