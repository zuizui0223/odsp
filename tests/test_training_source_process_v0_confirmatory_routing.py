from __future__ import annotations

from odsp.confirmatory_method_routing import (
    classify_existing_surface,
    route_confirmatory_method,
)


SURFACE = (
    "odsp.training_source_process_managed_internal_v0."
    "run_managed_internal_training_source_process_v0"
)


def _route(**overrides):
    args = dict(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_source_process",
        external_validation="none",
        contrast_count=2,
    )
    args.update(overrides)
    return route_confirmatory_method(**args)


def test_source_process_v0_c2_internal_is_primary_and_distinct():
    route = _route()
    assert route.role == "primary_confirmatory"
    assert route.primary_for_claim is True
    assert route.canonical_surface == SURFACE
    assert route.refit_population_generalization_claimed is True
    assert route.training_source_process_generalization_claimed is True
    assert route.requires_preoutcome_freeze is True
    assert route.qualification_key == (
        "alternative=greater|validation_design=independent_groups|"
        "information_structure=filtration|"
        "upstream_refits=predeclared_training_source_process|"
        "external_validation=none|contrast_count=2"
    )
    assert len(route.qualification_evidence) == 15


def test_source_process_v0_unqualified_scopes_fail_closed():
    assert _route(contrast_count=4).role == "unqualified"
    assert _route(external_validation="untouched_frozen").role == "unqualified"
    assert _route(alternative="two_sided").role == "unqualified"

    paired = _route(validation_design="paired_shared_blocks")
    assert paired.role == "unqualified"

    lattice = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="predeclared_training_source_process",
        external_validation="none",
        information_block_count=2,
    )
    assert lattice.role == "unqualified"


def test_v5_training_process_route_keeps_source_process_flag_false():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="none",
        contrast_count=2,
    )
    assert route.role == "primary_confirmatory"
    assert route.refit_population_generalization_claimed is True
    assert route.training_source_process_generalization_claimed is False


def test_source_v0_surface_name_alone_does_not_grant_primary_claim():
    classification = classify_existing_surface(SURFACE)
    assert classification.role == "primary_confirmatory"
    assert classification.primary_for_claim is False
    assert "full routing context" in classification.reason.lower()
