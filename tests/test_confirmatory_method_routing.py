from __future__ import annotations

import pytest

from odsp.confirmatory_method_routing import (
    classify_existing_surface,
    route_confirmatory_method,
)


def test_independent_directional_filtration_routes_to_primary_v2():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="none",
        external_validation="none",
        contrast_count=2,
    )
    assert route.role == "primary_confirmatory"
    assert route.primary_for_claim is True
    assert route.canonical_surface == (
        "odsp.information_transfer_positive_v2.certify_positive_information_transfer_v2"
    )
    assert route.requires_preoutcome_freeze is False
    assert route.historical_endpoint_reclassification_allowed is False


def test_independent_directional_filtration_rejects_unqualified_family_size():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="none",
        external_validation="none",
        contrast_count=3,
    )
    assert route.role == "unqualified"
    assert route.primary_for_claim is False
    assert route.canonical_surface is None
    assert "2 or 4" in route.reason


def test_paired_directional_filtration_requires_qualified_two_contrast_family():
    qualified = route_confirmatory_method(
        alternative="greater",
        validation_design="paired_shared_blocks",
        information_structure="filtration",
        upstream_refits="none",
        external_validation="none",
        contrast_count=2,
    )
    assert qualified.role == "primary_confirmatory"
    assert qualified.canonical_surface == (
        "odsp.shared_block_positive_information.certify_shared_block_positive_information_transfer_v2"
    )
    assert qualified.requires_exact_shared_block_support is True

    unqualified = route_confirmatory_method(
        alternative="greater",
        validation_design="paired_shared_blocks",
        information_structure="filtration",
        upstream_refits="none",
        external_validation="none",
        contrast_count=4,
    )
    assert unqualified.role == "unqualified"
    assert "2 contrasts" in unqualified.reason


def test_paired_fixed_set_untouched_external_filtration_routes_to_v3_cli():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="paired_shared_blocks",
        information_structure="filtration",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        contrast_count=2,
    )
    assert route.role == "primary_confirmatory"
    assert route.requires_preoutcome_freeze is True
    assert route.refit_population_generalization_claimed is False
    assert route.cli_sequence == (
        "odsp freeze-refits-external-paired",
        "odsp transfer-refits-external-paired",
    )
    assert route.canonical_surface == (
        "odsp.untouched_external_refit_shared_block_positive_contract_v3."
        "run_untouched_external_refit_shared_block_positive_contract_v3"
    )


def test_independent_fixed_set_untouched_external_filtration_routes_to_v2_cli():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        contrast_count=4,
    )
    assert route.role == "primary_confirmatory"
    assert route.cli_sequence == (
        "odsp freeze-refits-external",
        "odsp transfer-refits-external",
    )
    assert route.canonical_surface == (
        "odsp.untouched_external_refit_positive_contract_v2."
        "run_untouched_external_refit_positive_contract_v2"
    )


def test_paired_three_block_lattice_fixed_set_external_routes_to_v4():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=3,
    )
    assert route.role == "primary_confirmatory"
    assert route.edge_count == 12
    assert route.cli_sequence == (
        "odsp freeze-refits-external-paired-lattice",
        "odsp transfer-refits-external-paired-lattice",
    )
    assert route.canonical_surface == (
        "odsp.untouched_external_refit_shared_block_positive_lattice_contract_v4."
        "run_untouched_external_paired_all_refit_lattice_contract_v4"
    )


def test_paired_four_block_lattice_is_unqualified():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="paired_shared_blocks",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=4,
    )
    assert route.role == "unqualified"
    assert route.edge_count == 32
    assert route.canonical_surface is None
    assert "2 or 3 information blocks" in route.reason


def test_unfrozen_external_validation_is_never_confirmatory():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="fixed_set",
        external_validation="untouched_unfrozen",
        contrast_count=2,
    )
    assert route.role == "unqualified"
    assert route.primary_for_claim is False
    assert "pre-outcome semantic freeze" in route.reason


def test_stochastic_refit_population_claim_is_unqualified():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="stochastic_population",
        external_validation="none",
        contrast_count=2,
    )
    assert route.role == "unqualified"
    assert route.refit_population_generalization_claimed is False
    assert "refit population" in route.reason


def test_two_sided_v2_is_retained_for_bidirectional_not_primary_positive_claims():
    route = route_confirmatory_method(
        alternative="two_sided",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="none",
        external_validation="none",
        contrast_count=2,
    )
    assert route.role == "bidirectional_confirmatory"
    assert route.primary_for_claim is False
    assert route.canonical_surface == (
        "odsp.information_transfer_v2.certify_information_transfer_v2"
    )


def test_independent_two_sided_complete_lattice_routes_to_v2():
    route = route_confirmatory_method(
        alternative="two_sided",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="none",
        external_validation="none",
        information_block_count=3,
    )
    assert route.role == "bidirectional_confirmatory"
    assert route.primary_for_claim is False
    assert route.canonical_surface == "odsp.information_lattice_v2.certify_information_lattice_v2"


def test_surface_name_alone_cannot_establish_primary_claim_eligibility():
    classification = classify_existing_surface(
        "odsp.information_transfer_positive_v2.certify_positive_information_transfer_v2"
    )
    assert classification.role == "primary_confirmatory"
    assert classification.primary_for_claim is False
    assert "full routing context" in classification.reason


def test_legacy_fixed_scale_v1_surface_is_sensitivity_only():
    classification = classify_existing_surface(
        "odsp.simultaneous_group_certification.audit_simultaneous_group_certification"
    )
    assert classification.role == "sensitivity_only"
    assert classification.primary_for_claim is False
    assert "fixed-scale" in classification.reason


def test_old_refit_mixture_surface_is_sensitivity_only():
    classification = classify_existing_surface(
        "odsp.refit_information_transfer.certify_refit_information_transfer"
    )
    assert classification.role == "sensitivity_only"
    assert classification.primary_for_claim is False
    assert "fixed supplied refits" in classification.reason


def test_declared_sensitivity_surfaces_can_never_be_primary():
    for surface in (
        "odsp.refit_scheme_sensitivity.audit_refit_scheme_sensitivity",
        "odsp.sampling_weight_sensitivity.audit_sampling_weight_sensitivity",
        "odsp.block_definition_sensitivity.audit_block_definition_sensitivity",
    ):
        classification = classify_existing_surface(surface)
        assert classification.role == "sensitivity_only"
        assert classification.primary_for_claim is False


def test_unknown_surface_fails_closed():
    classification = classify_existing_surface("odsp.some_future_method.run")
    assert classification.role == "unqualified"
    assert classification.primary_for_claim is False


def test_invalid_routing_values_raise_instead_of_guessing():
    with pytest.raises(ValueError, match="alternative"):
        route_confirmatory_method(
            alternative="positive-ish",
            validation_design="independent_groups",
            information_structure="filtration",
            upstream_refits="none",
            external_validation="none",
            contrast_count=2,
        )
