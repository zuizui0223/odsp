"""Stable pre-outcome confirmatory-route declarations for external validation."""
from __future__ import annotations

from typing import Mapping

from .confirmatory_method_routing import route_confirmatory_method


ROUTER_CONTRACT_ID = "odsp-confirmatory-method-routing-v1"
_ROUTE_FIELDS = {
    "router_contract_id",
    "role",
    "canonical_surface",
    "alternative",
    "validation_design",
    "information_structure",
    "upstream_refits",
    "external_validation",
    "contrast_count",
    "information_block_count",
    "edge_count",
    "qualification_key",
    "qualification_evidence",
}


def build_frozen_confirmatory_route(
    *,
    validation_design: str,
    information_structure: str,
    contrast_count: int | None = None,
    information_block_count: int | None = None,
) -> dict[str, object]:
    """Build the stable semantic route tuple for a new untouched-external freeze."""

    decision = route_confirmatory_method(
        alternative="greater",
        validation_design=validation_design,
        information_structure=information_structure,
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        contrast_count=contrast_count,
        information_block_count=information_block_count,
    )
    if decision.role != "primary_confirmatory" or not decision.primary_for_claim:
        raise ValueError(
            "declared external analysis route is not primary_confirmatory: "
            f"{decision.reason}"
        )
    if decision.canonical_surface is None:
        raise ValueError("primary_confirmatory route has no canonical surface")
    if not decision.qualification_key or not decision.qualification_evidence:
        raise ValueError(
            "primary_confirmatory route is missing registered qualification evidence"
        )

    return {
        "router_contract_id": ROUTER_CONTRACT_ID,
        "role": decision.role,
        "canonical_surface": decision.canonical_surface,
        "alternative": "greater",
        "validation_design": validation_design,
        "information_structure": information_structure,
        "upstream_refits": "fixed_set",
        "external_validation": "untouched_frozen",
        "contrast_count": contrast_count,
        "information_block_count": information_block_count,
        "edge_count": decision.edge_count,
        "qualification_key": decision.qualification_key,
        "qualification_evidence": list(decision.qualification_evidence),
    }


def normalize_frozen_confirmatory_route(raw: object) -> dict[str, object]:
    """Validate the stable frozen route object without trusting its contents."""

    if not isinstance(raw, Mapping):
        raise ValueError("freeze manifest confirmatory_route must be a JSON object")
    unknown = sorted(set(raw) - _ROUTE_FIELDS)
    missing = sorted(_ROUTE_FIELDS - set(raw))
    if unknown or missing:
        raise ValueError(
            "freeze manifest confirmatory_route fields mismatch: "
            f"missing={missing!r}, unknown={unknown!r}"
        )

    def _text(name: str) -> str:
        value = raw[name]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"freeze manifest confirmatory_route.{name} must be non-empty text")
        return value.strip()

    def _optional_int(name: str) -> int | None:
        value = raw[name]
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(
                f"freeze manifest confirmatory_route.{name} must be null or a positive integer"
            )
        return int(value)

    evidence_raw = raw["qualification_evidence"]
    if not isinstance(evidence_raw, list) or not evidence_raw:
        raise ValueError(
            "freeze manifest confirmatory_route.qualification_evidence must be a non-empty JSON array"
        )
    evidence: list[str] = []
    for index, item in enumerate(evidence_raw):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                "freeze manifest confirmatory_route.qualification_evidence"
                f"[{index}] must be non-empty text"
            )
        evidence.append(item.strip())
    if len(evidence) != len(set(evidence)):
        raise ValueError(
            "freeze manifest confirmatory_route.qualification_evidence must not contain duplicates"
        )

    return {
        "router_contract_id": _text("router_contract_id"),
        "role": _text("role"),
        "canonical_surface": _text("canonical_surface"),
        "alternative": _text("alternative"),
        "validation_design": _text("validation_design"),
        "information_structure": _text("information_structure"),
        "upstream_refits": _text("upstream_refits"),
        "external_validation": _text("external_validation"),
        "contrast_count": _optional_int("contrast_count"),
        "information_block_count": _optional_int("information_block_count"),
        "edge_count": _optional_int("edge_count"),
        "qualification_key": _text("qualification_key"),
        "qualification_evidence": evidence,
    }


def verify_frozen_confirmatory_route(
    frozen: object,
    *,
    validation_design: str,
    information_structure: str,
    contrast_count: int | None = None,
    information_block_count: int | None = None,
) -> dict[str, object]:
    """Require the frozen route to equal the route recomputed from runtime semantics."""

    actual = normalize_frozen_confirmatory_route(frozen)
    expected = build_frozen_confirmatory_route(
        validation_design=validation_design,
        information_structure=information_structure,
        contrast_count=contrast_count,
        information_block_count=information_block_count,
    )
    if actual != expected:
        raise ValueError(
            "freeze manifest semantic mismatch for confirmatory_route: "
            f"frozen={actual!r}, runtime={expected!r}"
        )
    return expected
