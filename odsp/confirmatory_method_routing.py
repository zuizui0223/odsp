"""Fail-closed governance for prospective ODSP inference routing.

This module does not run statistical inference and does not reclassify historical
empirical endpoints.  It maps a prospective scientific question and validation
design onto the ODSP method surface whose operating-characteristic and provenance
boundaries actually match that request.  Unknown or unsupported combinations are
reported as unqualified rather than guessed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from .confirmatory_calibration_evidence import qualification_evidence_for_surface


_ROLES = {
    "primary_confirmatory",
    "bidirectional_confirmatory",
    "sensitivity_only",
    "unqualified",
}
_ALTERNATIVES = {"greater", "two_sided"}
_VALIDATION_DESIGNS = {"independent_groups", "paired_shared_blocks"}
_INFORMATION_STRUCTURES = {"filtration", "complete_lattice"}
_REFIT_MODES = {"none", "fixed_set", "stochastic_population"}
_EXTERNAL_MODES = {"none", "untouched_frozen", "untouched_unfrozen"}


@dataclass(frozen=True)
class MethodRoute:
    role: str
    primary_for_claim: bool
    canonical_surface: str | None
    cli_sequence: tuple[str, ...]
    reason: str
    requires_preoutcome_freeze: bool
    requires_exact_shared_block_support: bool
    refit_population_generalization_claimed: bool
    historical_endpoint_reclassification_allowed: bool
    qualification_evidence: tuple[str, ...] = ()
    edge_count: int | None = None

    def __post_init__(self) -> None:
        if self.role not in _ROLES:
            raise ValueError(f"unknown route role: {self.role}")

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["cli_sequence"] = list(self.cli_sequence)
        payload["qualification_evidence"] = list(self.qualification_evidence)
        return payload


@dataclass(frozen=True)
class SurfaceClassification:
    surface: str
    role: str
    primary_for_claim: bool
    reason: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _route(
    role: str,
    reason: str,
    *,
    canonical_surface: str | None = None,
    cli_sequence: Sequence[str] = (),
    requires_preoutcome_freeze: bool = False,
    requires_exact_shared_block_support: bool = False,
    edge_count: int | None = None,
) -> MethodRoute:
    qualification_evidence: tuple[str, ...] = ()
    if role in {"primary_confirmatory", "bidirectional_confirmatory"}:
        if canonical_surface is None:
            raise ValueError("confirmatory route requires a canonical method surface")
        qualification_evidence = qualification_evidence_for_surface(canonical_surface)
        if not qualification_evidence:
            raise ValueError(
                "confirmatory route lacks registered frozen qualification evidence: "
                + canonical_surface
            )

    return MethodRoute(
        role=role,
        primary_for_claim=role == "primary_confirmatory",
        canonical_surface=canonical_surface,
        cli_sequence=tuple(cli_sequence),
        reason=reason,
        requires_preoutcome_freeze=requires_preoutcome_freeze,
        requires_exact_shared_block_support=requires_exact_shared_block_support,
        refit_population_generalization_claimed=False,
        historical_endpoint_reclassification_allowed=False,
        qualification_evidence=qualification_evidence,
        edge_count=edge_count,
    )


def _choice(value: str, allowed: set[str], *, name: str) -> str:
    value = str(value).strip()
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)!r}")
    return value


def _positive_integer(value: int | None, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def route_confirmatory_method(
    *,
    alternative: str,
    validation_design: str,
    information_structure: str,
    upstream_refits: str,
    external_validation: str,
    contrast_count: int | None = None,
    information_block_count: int | None = None,
) -> MethodRoute:
    """Return the canonical prospective role for one declared analysis design."""

    alternative = _choice(alternative, _ALTERNATIVES, name="alternative")
    validation_design = _choice(
        validation_design, _VALIDATION_DESIGNS, name="validation_design"
    )
    information_structure = _choice(
        information_structure, _INFORMATION_STRUCTURES, name="information_structure"
    )
    upstream_refits = _choice(upstream_refits, _REFIT_MODES, name="upstream_refits")
    external_validation = _choice(
        external_validation, _EXTERNAL_MODES, name="external_validation"
    )

    if upstream_refits == "stochastic_population":
        return _route(
            "unqualified",
            "ODSP has no fit-sampling model that supports confidence statements about a refit population; use a fixed supplied refit set only as an intersection robustness claim.",
        )
    if external_validation == "untouched_unfrozen":
        return _route(
            "unqualified",
            "Untouched external confirmatory inference requires a pre-outcome semantic freeze; an unfrozen external analysis is not a confirmatory ODSP route.",
        )

    if information_structure == "filtration":
        contrasts = _positive_integer(contrast_count, name="contrast_count")
    else:
        blocks = _positive_integer(information_block_count, name="information_block_count")
        edge_count = blocks * 2 ** (blocks - 1)

    if alternative == "two_sided":
        # No semantically frozen untouched-external two-sided endpoint is qualified.
        # This hard stop must precede the historical refit sensitivity branch.
        if external_validation != "none":
            return _route(
                "unqualified",
                "No canonical two-sided semantically frozen untouched-external endpoint is qualified; external confirmatory routes are currently predeclared directional one-sided routes.",
                requires_preoutcome_freeze=True,
                requires_exact_shared_block_support=validation_design == "paired_shared_blocks",
                edge_count=None if information_structure == "filtration" else edge_count,
            )

        # High-level paired two-sided information/refit wrappers are not qualified
        # as prospective endpoints. Do not infer them from lower-level gain cores.
        if validation_design != "independent_groups":
            return _route(
                "unqualified",
                "No canonical high-level paired two-sided information endpoint is qualified for prospective routing; do not promote a lower-level shared-block gain core or historical refit wrapper by implication.",
                requires_exact_shared_block_support=True,
                edge_count=None if information_structure == "filtration" else edge_count,
            )

        # The prospective independent-group v2 operating-characteristic panel
        # qualifies only 2- and 4-contrast simultaneous families.
        if information_structure == "filtration" and contrasts not in {2, 4}:
            return _route(
                "unqualified",
                "The prospectively qualified independent two-sided v2 null panel covers 2 or 4 simultaneous contrasts; other family sizes are not promoted to bidirectional confirmatory status.",
            )

        # A complete two-block lattice has four directed edges. The independent
        # two-sided prospective panel does not qualify the 12-edge three-block
        # lattice or larger families.
        if information_structure == "complete_lattice" and edge_count != 4:
            return _route(
                "unqualified",
                "Independent two-sided complete-lattice routing is prospectively qualified only for the 4-edge two-block family; no 12-edge or larger lattice calibration is frozen for this route.",
                edge_count=edge_count,
            )

        if upstream_refits == "fixed_set":
            return _route(
                "sensitivity_only",
                "Two-sided refit-aware mixture inference remains a sensitivity analysis because the supplied refits are not a probability sample from a defined fit population.",
                canonical_surface=(
                    "odsp.refit_information_transfer.certify_refit_information_transfer"
                    if information_structure == "filtration"
                    else "odsp.refit_information_lattice.certify_refit_information_lattice"
                ),
                edge_count=None if information_structure == "filtration" else edge_count,
            )

        if information_structure == "filtration":
            return _route(
                "bidirectional_confirmatory",
                "Genuine replicate-studentized two-sided v2 is retained for predeclared bidirectional independent-group questions inside the prospectively calibrated 2/4-contrast family-size scope; it is not the primary route for a positive-only claim.",
                canonical_surface="odsp.information_transfer_v2.certify_information_transfer_v2",
            )
        return _route(
            "bidirectional_confirmatory",
            "Genuine replicate-studentized two-sided v2 complete-lattice inference is retained only for the prospectively calibrated independent 4-edge two-block family.",
            canonical_surface="odsp.information_lattice_v2.certify_information_lattice_v2",
            edge_count=edge_count,
        )

    # Predeclared directional positive-transfer route.
    if information_structure == "filtration":
        if validation_design == "independent_groups":
            if contrasts not in {2, 4}:
                return _route(
                    "unqualified",
                    "The prospectively qualified independent one-sided null panel covers 2 or 4 simultaneous contrasts; other family sizes are not promoted to primary confirmatory status.",
                )
            if upstream_refits == "none" and external_validation == "none":
                return _route(
                    "primary_confirmatory",
                    "Predeclared positive transfer in independent validation groups uses the qualified one-sided v2 familywise lower bootstrap-t route.",
                    canonical_surface="odsp.information_transfer_positive_v2.certify_positive_information_transfer_v2",
                )
            if upstream_refits == "fixed_set" and external_validation == "none":
                return _route(
                    "primary_confirmatory",
                    "Each supplied refit is certified separately and the same step must pass in every refit; the refit axis is a fixed-set intersection, not a population confidence distribution.",
                    canonical_surface="odsp.refit_positive_robustness.certify_all_refit_positive_information_transfer_v2",
                )
            if upstream_refits == "fixed_set" and external_validation == "untouched_frozen":
                return _route(
                    "primary_confirmatory",
                    "Semantically frozen untouched external validation with a fixed refit set uses the independent all-refit one-sided external endpoint.",
                    canonical_surface=(
                        "odsp.untouched_external_refit_positive_contract_v2."
                        "run_untouched_external_refit_positive_contract_v2"
                    ),
                    cli_sequence=(
                        "odsp freeze-refits-external",
                        "odsp transfer-refits-external",
                    ),
                    requires_preoutcome_freeze=True,
                )
            return _route(
                "unqualified",
                "There is no canonical semantically frozen independent external one-sided endpoint without the fixed supplied refit-set contract.",
                requires_preoutcome_freeze=external_validation != "none",
            )

        # paired shared-block filtration
        if contrasts != 2:
            return _route(
                "unqualified",
                "The paired directional filtration null qualification is prospective for exactly 2 contrasts; larger families must not borrow the separate 4/12-edge lattice calibration.",
                requires_exact_shared_block_support=True,
            )
        if upstream_refits == "none" and external_validation == "none":
            return _route(
                "primary_confirmatory",
                "Predeclared positive transfer in paired validation groups uses the qualified shared-block one-sided v2 route with exact common positive-mass support.",
                canonical_surface=(
                    "odsp.shared_block_positive_information."
                    "certify_shared_block_positive_information_transfer_v2"
                ),
                requires_exact_shared_block_support=True,
            )
        if upstream_refits == "fixed_set" and external_validation == "none":
            return _route(
                "primary_confirmatory",
                "The same paired directional step must pass in every supplied refit; different refits cannot rescue one another.",
                canonical_surface=(
                    "odsp.refit_positive_robustness."
                    "certify_all_refit_shared_block_positive_information_transfer_v2"
                ),
                requires_exact_shared_block_support=True,
            )
        if upstream_refits == "fixed_set" and external_validation == "untouched_frozen":
            return _route(
                "primary_confirmatory",
                "The paired all-refit directional filtration is confirmatory externally only through its pre-outcome semantic freeze endpoint.",
                canonical_surface=(
                    "odsp.untouched_external_refit_shared_block_positive_contract_v3."
                    "run_untouched_external_refit_shared_block_positive_contract_v3"
                ),
                cli_sequence=(
                    "odsp freeze-refits-external-paired",
                    "odsp transfer-refits-external-paired",
                ),
                requires_preoutcome_freeze=True,
                requires_exact_shared_block_support=True,
            )
        return _route(
            "unqualified",
            "There is no canonical semantically frozen paired external directional endpoint without the fixed supplied refit-set contract.",
            requires_preoutcome_freeze=external_validation != "none",
            requires_exact_shared_block_support=True,
        )

    # Directional complete lattice.
    assert information_structure == "complete_lattice"
    if validation_design == "independent_groups":
        if blocks != 2:
            return _route(
                "unqualified",
                "The independent directional complete lattice is prospectively qualified only for 2 information blocks = 4 directed edges; 3-block / 12-edge and larger families remain unqualified.",
                edge_count=edge_count,
            )
        if upstream_refits == "none" and external_validation == "none":
            return _route(
                "primary_confirmatory",
                "The complete two-block independent lattice maps its four directed edges onto the already prospectively qualified four-contrast one-sided bootstrap-t family.",
                canonical_surface=(
                    "odsp.information_lattice_positive_v2."
                    "certify_positive_information_lattice_v2"
                ),
                edge_count=edge_count,
            )
        if upstream_refits == "fixed_set" and external_validation == "none":
            return _route(
                "primary_confirmatory",
                "Each supplied refit is certified with the qualified independent four-edge lattice, and global paths are reconstructed only from edges robust in every supplied refit.",
                canonical_surface=(
                    "odsp.refit_positive_independent_lattice_robustness."
                    "certify_all_refit_independent_positive_information_lattice_v2"
                ),
                edge_count=edge_count,
            )
        return _route(
            "unqualified",
            "No semantically frozen untouched-external independent directional lattice endpoint is qualified yet; the fixed-score and fixed-set internal four-edge routes must not be promoted beyond their current scope.",
            requires_preoutcome_freeze=external_validation != "none",
            edge_count=edge_count,
        )
    if validation_design != "paired_shared_blocks":
        return _route(
            "unqualified",
            "Unknown directional lattice validation design.",
            edge_count=edge_count,
        )
    if blocks not in {2, 3}:
        return _route(
            "unqualified",
            "The paired directional complete lattice is qualified only for 2 or 3 information blocks, corresponding to 4 or 12 directed edges.",
            requires_exact_shared_block_support=True,
            edge_count=edge_count,
        )
    if upstream_refits == "none" and external_validation == "none":
        return _route(
            "primary_confirmatory",
            "Every edge of the calibrated paired directional lattice is certified in one family; failed edges cannot be rescued by a best path or Shapley summary.",
            canonical_surface=(
                "odsp.shared_block_positive_information."
                "certify_shared_block_positive_information_lattice_v2"
            ),
            requires_exact_shared_block_support=True,
            edge_count=edge_count,
        )
    if upstream_refits == "fixed_set" and external_validation == "none":
        return _route(
            "primary_confirmatory",
            "Each paired lattice is certified separately in every supplied refit, then global paths are recomputed from the same-edge intersection across refits.",
            canonical_surface=(
                "odsp.refit_positive_lattice_robustness."
                "certify_all_refit_shared_block_positive_information_lattice_v2"
            ),
            requires_exact_shared_block_support=True,
            edge_count=edge_count,
        )
    if upstream_refits == "fixed_set" and external_validation == "untouched_frozen":
        return _route(
            "primary_confirmatory",
            "The complete paired lattice, refit IDs, row pairing metadata and inferential settings must all be frozen before untouched external outcomes are opened.",
            canonical_surface=(
                "odsp.untouched_external_refit_shared_block_positive_lattice_contract_v4."
                "run_untouched_external_paired_all_refit_lattice_contract_v4"
            ),
            cli_sequence=(
                "odsp freeze-refits-external-paired-lattice",
                "odsp transfer-refits-external-paired-lattice",
            ),
            requires_preoutcome_freeze=True,
            requires_exact_shared_block_support=True,
            edge_count=edge_count,
        )
    return _route(
        "unqualified",
        "There is no canonical semantically frozen paired lattice external endpoint without the fixed supplied refit-set contract.",
        requires_preoutcome_freeze=external_validation != "none",
        requires_exact_shared_block_support=True,
        edge_count=edge_count,
    )


_PRIMARY_SURFACES = {
    "odsp.information_transfer_positive_v2.certify_positive_information_transfer_v2",
    "odsp.shared_block_positive_information.certify_shared_block_positive_information_transfer_v2",
    "odsp.information_lattice_positive_v2.certify_positive_information_lattice_v2",
    "odsp.refit_positive_independent_lattice_robustness.certify_all_refit_independent_positive_information_lattice_v2",
    "odsp.shared_block_positive_information.certify_shared_block_positive_information_lattice_v2",
    "odsp.refit_positive_robustness.certify_all_refit_positive_information_transfer_v2",
    "odsp.refit_positive_robustness.certify_all_refit_shared_block_positive_information_transfer_v2",
    "odsp.refit_positive_lattice_robustness.certify_all_refit_shared_block_positive_information_lattice_v2",
    "odsp.untouched_external_refit_positive_contract_v2.run_untouched_external_refit_positive_contract_v2",
    "odsp.untouched_external_refit_shared_block_positive_contract_v3.run_untouched_external_refit_shared_block_positive_contract_v3",
    "odsp.untouched_external_refit_shared_block_positive_lattice_contract_v4.run_untouched_external_paired_all_refit_lattice_contract_v4",
}
_BIDIRECTIONAL_SURFACES = {
    "odsp.information_transfer_v2.certify_information_transfer_v2",
    "odsp.information_lattice_v2.certify_information_lattice_v2",
    "odsp.simultaneous_group_certification_v2.audit_simultaneous_group_certification_v2",
    "odsp.shared_block_certification_v2.certify_shared_block_gains_v2",
}
_SENSITIVITY_SURFACES = {
    "odsp.simultaneous_group_certification.audit_simultaneous_group_certification": (
        "Legacy v1 uses a fixed-scale standardized max-deviation bootstrap and is retained only as provenance/sensitivity, not as new primary inference."
    ),
    "odsp.shared_block_certification.certify_shared_block_gains": (
        "Legacy shared-block v1 is a fixed-scale sensitivity/provenance surface and is superseded for new confirmatory endpoints by genuine replicate-studentized v2."
    ),
    "odsp.shared_block_information.certify_shared_block_information_transfer": (
        "The historical paired information wrapper is tied to legacy v1 certification and remains sensitivity/provenance only."
    ),
    "odsp.refit_information_transfer.certify_refit_information_transfer": (
        "The old refit-mixture route summarizes fixed supplied refits without a defensible refit sampling distribution; it is sensitivity-only for refit uncertainty claims."
    ),
    "odsp.refit_information_lattice.certify_refit_information_lattice": (
        "The old refit-aware lattice treats fixed supplied refits as an empirical sensitivity ensemble and does not support population-level refit inference."
    ),
    "odsp.refit_scheme_sensitivity.audit_refit_scheme_sensitivity": "This API is explicitly a refit-scheme sensitivity analysis.",
    "odsp.sampling_weight_sensitivity.audit_sampling_weight_sensitivity": "This API is explicitly a sampling-weight sensitivity analysis.",
    "odsp.block_definition_sensitivity.audit_block_definition_sensitivity": "This API is explicitly a block-definition sensitivity analysis.",
}


def classify_existing_surface(surface: str) -> SurfaceClassification:
    """Classify an existing ODSP API by prospective inferential role."""

    value = str(surface).strip()
    if not value:
        raise ValueError("surface must be a non-empty string")
    if value in _PRIMARY_SURFACES:
        return SurfaceClassification(
            surface=value,
            role="primary_confirmatory",
            primary_for_claim=False,
            reason="Canonical directional positive-transfer method family; the surface name alone cannot establish primary claim eligibility. Full routing context must satisfy its declared design, family-size calibration and provenance boundaries.",
        )
    if value in _BIDIRECTIONAL_SURFACES:
        return SurfaceClassification(
            surface=value,
            role="bidirectional_confirmatory",
            primary_for_claim=False,
            reason="Genuine two-sided v2 surface retained for predeclared bidirectional inference, not as the primary method for a positive-only claim.",
        )
    if value in _SENSITIVITY_SURFACES:
        return SurfaceClassification(
            surface=value,
            role="sensitivity_only",
            primary_for_claim=False,
            reason=_SENSITIVITY_SURFACES[value],
        )
    return SurfaceClassification(
        surface=value,
        role="unqualified",
        primary_for_claim=False,
        reason="Surface is not present in the frozen confirmatory routing registry; fail closed rather than infer a role from its name or implementation.",
    )
