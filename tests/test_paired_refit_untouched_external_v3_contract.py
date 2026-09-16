from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path("ODSP_PAIRED_REFIT_UNTOUCHED_EXTERNAL_V3_CONTRACT.json")


def test_paired_external_v3_contract_freezes_validation_design():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["contract_id"] == "odsp-paired-refit-untouched-external-v3"
    design = payload["validation_design"]
    assert design["validation_group_independence_assumed"] is False
    assert design["exact_positive_mass_shared_block_support_required"] is True
    assert design["same_block_draw_shared_across_all_groups_and_steps_within_refit"] is True
    assert design["shared_block_exchangeability_assumed"] is True
    assert design["missing_shared_blocks_imputed"] is False
    assert design["post_outcome_common_block_subset_allowed"] is False


def test_paired_external_v3_contract_uses_fixed_set_intersection_rule():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    refit = payload["refit_axis"]
    assert refit["fixed_supplied_set"] is True
    assert refit["composition_rule"] == "intersection_union_all_components_must_reject"
    assert refit["all_supplied_refits_must_pass_each_required_step"] is True
    assert refit["additional_refit_axis_multiplicity_correction_applied"] is False
    assert refit["refit_independence_assumed"] is False
    assert refit["refit_population_generalization_claimed"] is False
    assert refit["reference_refit_can_override_failure"] is False
    assert refit["refit_average_can_override_failure"] is False


def test_paired_external_v3_contract_requires_semantic_preoutcome_freeze():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    freeze = payload["pre_outcome_freeze"]
    assert freeze["manifest_schema_version"] == 2
    assert freeze["manifest_type"] == "odsp_pre_external_outcome_paired_freeze_v1"
    assert freeze["validation_design_kind"] == "paired_shared_blocks"
    assert freeze["external_row_roster_frozen"] is True
    assert freeze["refit_ids_frozen"] is True
    assert freeze["information_filtration_frozen"] is True
    assert freeze["score_semantics_frozen"] is True
    assert freeze["directional_alternative_frozen"] is True


def test_paired_external_v3_contract_keeps_claim_boundary_narrow():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    claim = payload["claim_scope"]
    assert claim["information_structure"] == "strict_nested_filtration"
    assert claim["directional_alternative"] == "greater"
    assert claim["non_skippable_transfer_ceiling"] is True
    assert claim["paired_lattice_claim_added_by_this_contract"] is False
    assert claim["arbitrary_cross_group_dependence_supported"] is False
    assert claim["upstream_models_fitted_by_odsp"] is False
