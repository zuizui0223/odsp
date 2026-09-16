from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path("ODSP_UNTOUCHED_EXTERNAL_PAIRED_ALL_REFIT_LATTICE_V4_CONTRACT.json")


def test_v4_contract_freezes_complete_lattice_before_outcome_access():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    freeze = payload["pre_outcome_freeze"]
    assert freeze["external_row_roster_frozen"] is True
    assert freeze["paired_row_metadata_frozen"] is True
    assert freeze["pairing_metadata_fields"] == ["row_id", "group", "block", "weight"]
    assert freeze["pairing_metadata_digest"] == "sha256_of_canonical_row_id_sorted_json"
    assert freeze["post_outcome_row_to_group_reassignment_allowed"] is False
    assert freeze["post_outcome_row_to_block_reassignment_allowed"] is False
    assert freeze["post_outcome_weight_change_allowed"] is False
    assert freeze["information_block_definitions_frozen"] is True
    assert freeze["complete_subset_node_table_frozen"] is True
    assert freeze["node_score_column_mapping_frozen"] is True
    assert freeze["edge_family_size_frozen"] is True
    assert freeze["inferential_settings_frozen"] is True
    assert freeze["caller_supplied_freeze_timestamp_allowed"] is False
    assert freeze["manifest_overwrite_allowed"] is False
    assert freeze["roster_outcome_columns_allowed"] is False


def test_v4_contract_stays_inside_calibrated_4_and_12_edge_scope():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    scope = payload["lattice_scope"]
    assert scope["supported_information_block_counts"] == [2, 3]
    assert scope["qualified_edge_family_sizes"] == [4, 12]
    assert scope["four_or_more_information_blocks_supported"] is False
    assert scope["best_path_can_override_failed_edge"] is False
    assert scope["shapley_can_override_failed_edge"] is False


def test_v4_contract_requires_same_edge_across_all_refits():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    refit = payload["refit_axis"]
    assert refit["composition_rule"] == "intersection_union_all_components_must_reject"
    assert refit["all_supplied_refits_must_pass_the_same_edge"] is True
    assert refit["different_successful_paths_across_refits_can_be_combined"] is False
    assert refit["refit_independence_assumed"] is False
    assert refit["refit_population_generalization_claimed"] is False
    assert refit["reference_or_average_refit_can_override_failure"] is False


def test_v4_contract_retains_paired_shared_block_boundary():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    design = payload["validation_design"]
    assert design["validation_group_independence_assumed"] is False
    assert design["exact_positive_mass_shared_block_support_required"] is True
    assert design["shared_block_exchangeability_assumed"] is True
    assert design["missing_shared_blocks_imputed"] is False
    assert design["post_outcome_common_block_subset_allowed"] is False


def test_v4_contract_keeps_external_provenance_boundary_explicit():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    external = payload["external_validation"]
    assert external["freeze_manifest_hash_verified"] is True
    assert external["freeze_manifest_semantics_verified"] is True
    assert external["runtime_provenance_ids_must_match_frozen_manifest"] is True
    assert external["runtime_pairing_metadata_must_match_frozen_manifest"] is True
    assert external["historical_non_access_independently_proven_by_odsp"] is False
    assert external["development_data_disjointness_independently_proven_by_odsp"] is False
