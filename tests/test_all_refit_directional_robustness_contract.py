from __future__ import annotations

import json
from pathlib import Path

from odsp.refit_positive_robustness import (
    certify_all_refit_positive_information_transfer_v2,
    certify_all_refit_shared_block_positive_information_transfer_v2,
)


CONTRACT = Path("ODSP_ALL_REFIT_DIRECTIONAL_ROBUSTNESS_CONTRACT.json")


def test_all_refit_contract_freezes_intersection_union_boundaries():
    payload = json.loads(CONTRACT.read_text())

    assert payload["schema_version"] == 1
    assert payload["global_claim"]["composition_rule"] == (
        "intersection_union_all_components_must_reject"
    )
    assert payload["global_claim"]["all_supplied_refits_must_pass"] is True
    assert payload["global_claim"]["reference_refit_can_override_failure"] is False
    assert payload["global_claim"]["refit_average_can_override_failure"] is False
    assert payload["global_claim"]["best_refit_can_override_failure"] is False

    refit_axis = payload["refit_axis"]
    assert refit_axis["fixed_supplied_set"] is True
    assert refit_axis["additional_refit_axis_multiplicity_correction_applied"] is False
    assert refit_axis["refit_independence_assumed"] is False
    assert refit_axis["refit_sampling_distribution_assumed"] is False
    assert refit_axis["refit_population_generalization_claimed"] is False
    assert refit_axis["minimum_refits_default"] == 2


def test_contract_routes_to_qualified_directional_component_methods():
    payload = json.loads(CONTRACT.read_text())
    component = payload["component_inference"]
    assert component["independent_group_route"] == "certify_positive_information_transfer_v2"
    assert component["shared_block_route"] == (
        "certify_shared_block_positive_information_transfer_v2"
    )
    assert component["alternative"] == "greater"
    assert component["validation_familywise_control_applied_within_each_refit"] is True
    assert component["replicate_specific_bootstrap_t"] is True

    assert callable(certify_all_refit_positive_information_transfer_v2)
    assert callable(certify_all_refit_shared_block_positive_information_transfer_v2)


def test_contract_keeps_legacy_nested_refit_layer_sensitivity_only():
    payload = json.loads(CONTRACT.read_text())
    boundary = payload["legacy_refit_layer_boundary"]
    assert boundary["nested_refit_monte_carlo_retained"] is True
    assert boundary["role"] == "sensitivity diagnostic"
    assert boundary["used_as_primary_refit_population_confidence_claim"] is False
    assert boundary["supplied_refits_treated_as_independent_probability_sample"] is False


def test_contract_preserves_external_model_boundary_and_empirical_freeze():
    payload = json.loads(CONTRACT.read_text())
    external = payload["external_model_boundary"]
    assert external["upstream_models_fitted_by_odsp"] is False
    assert external["refit_scheme_inferred_by_odsp"] is False
    assert external["refit_set_selected_by_odsp"] is False

    empirical = payload["empirical_boundary"]
    assert empirical["historical_empirical_endpoint_rerun"] is False
    assert empirical["historical_terminal_category_reclassified"] is False
