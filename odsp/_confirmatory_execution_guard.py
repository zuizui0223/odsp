"""Internal execution guard for confirmatory untouched-external endpoints.

This module does not add a public method surface. It binds an executing endpoint
back to the already-frozen confirmatory router and its family-specific
qualification evidence. Unsupported route contexts fail closed before the
endpoint performs statistical certification.
"""
from __future__ import annotations

from .confirmatory_method_routing import route_confirmatory_method


def verify_confirmatory_execution_route(
    *,
    validation_design: str,
    information_structure: str,
    canonical_surface: str,
    contrast_count: int | None = None,
    information_block_count: int | None = None,
) -> dict[str, object]:
    """Verify that one untouched-external runtime is a qualified primary route."""

    route = route_confirmatory_method(
        alternative="greater",
        validation_design=validation_design,
        information_structure=information_structure,
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        contrast_count=contrast_count,
        information_block_count=information_block_count,
    )
    if route.role != "primary_confirmatory" or not route.primary_for_claim:
        raise ValueError(
            "external execution is not a qualified primary confirmatory route: "
            + route.reason
        )
    if route.canonical_surface != canonical_surface:
        raise ValueError(
            "confirmatory route canonical surface mismatch: "
            f"routed={route.canonical_surface!r}, runtime={canonical_surface!r}"
        )
    if not route.qualification_key or not route.qualification_evidence:
        raise ValueError(
            "qualified confirmatory execution route is missing frozen qualification evidence"
        )
    return {
        "verified": True,
        "role": route.role,
        "canonical_surface": route.canonical_surface,
        "qualification_key": route.qualification_key,
        "qualification_evidence": list(route.qualification_evidence),
        "requires_preoutcome_freeze": route.requires_preoutcome_freeze,
        "requires_exact_shared_block_support": route.requires_exact_shared_block_support,
        "refit_population_generalization_claimed": route.refit_population_generalization_claimed,
        "historical_endpoint_reclassification_allowed": route.historical_endpoint_reclassification_allowed,
        "edge_count": route.edge_count,
    }
