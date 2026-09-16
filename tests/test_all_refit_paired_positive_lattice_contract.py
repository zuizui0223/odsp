from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path("ODSP_ALL_REFIT_PAIRED_POSITIVE_LATTICE_CONTRACT.json")


def test_contract_limits_lattice_to_calibrated_family_sizes():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    scope = payload["lattice_scope"]
    assert scope["minimum_information_blocks"] == 2
    assert scope["maximum_information_blocks"] == 3
    assert scope["qualified_edge_family_sizes"] == [4, 12]
    assert scope["four_or_more_information_blocks_supported"] is False
    assert scope["best_path_can_override_failed_edge"] is False
    assert scope["shapley_can_override_failed_edge"] is False


def test_contract_requires_same_edge_in_every_refit():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    refit = payload["refit_axis"]
    assert refit["composition_rule"] == "intersection_union_all_components_must_reject"
    assert refit["all_supplied_refits_must_pass_the_same_edge"] is True
    assert refit["different_successful_paths_across_refits_can_be_combined"] is False
    assert refit["refit_independence_assumed"] is False
    assert refit["refit_population_generalization_claimed"] is False
    assert refit["additional_refit_axis_multiplicity_correction_applied"] is False


def test_contract_keeps_paired_shared_block_boundary():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    design = payload["validation_design"]
    assert design["validation_group_independence_assumed"] is False
    assert design["exact_positive_mass_shared_block_support_required"] is True
    assert design["shared_block_exchangeability_assumed"] is True
    assert design["missing_shared_blocks_imputed"] is False
    assert design["same_shared_block_draw_used_across_all_groups_and_edges_within_refit"] is True


def test_contract_inherits_validation_calibration_without_refit_population_claim():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    calibration = payload["calibration_inheritance"]
    assert calibration["paired_directional_4_edge_null_panel_qualified"] is True
    assert calibration["paired_directional_12_edge_null_panel_qualified"] is True
    assert calibration["new_refit_population_calibration_claimed"] is False
