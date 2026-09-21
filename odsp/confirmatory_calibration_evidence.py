"""Frozen qualification-evidence registry for prospective ODSP routing.

The registry is deliberately descriptive. It does not recompute calibration and it
does not turn simulation receipts into biological evidence. CI compares routing
scope against the frozen receipt contents so method routing cannot silently widen
beyond the prospectively qualified family sizes.
"""
from __future__ import annotations


CONFIRMATORY_EVIDENCE_BY_SURFACE: dict[str, tuple[str, ...]] = {
    "odsp.information_transfer_positive_v2.certify_positive_information_transfer_v2": (
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
    ),
    "odsp.refit_positive_robustness.certify_all_refit_positive_information_transfer_v2": (
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
        "ODSP_ALL_REFIT_DIRECTIONAL_ROBUSTNESS_CONTRACT.json",
    ),
    "odsp.untouched_external_refit_positive_contract_v2.run_untouched_external_refit_positive_contract_v2": (
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
        "ODSP_ALL_REFIT_DIRECTIONAL_ROBUSTNESS_CONTRACT.json",
        "ODSP_UNTOUCHED_EXTERNAL_FREEZE_SEMANTIC_LOCK_V2.json",
    ),
    "odsp.shared_block_positive_information.certify_shared_block_positive_information_transfer_v2": (
        "PAIRED_ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
    ),
    "odsp.refit_positive_robustness.certify_all_refit_shared_block_positive_information_transfer_v2": (
        "PAIRED_ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
        "ODSP_ALL_REFIT_DIRECTIONAL_ROBUSTNESS_CONTRACT.json",
    ),
    "odsp.untouched_external_refit_shared_block_positive_contract_v3.run_untouched_external_refit_shared_block_positive_contract_v3": (
        "PAIRED_ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
        "ODSP_ALL_REFIT_DIRECTIONAL_ROBUSTNESS_CONTRACT.json",
        "ODSP_PAIRED_REFIT_UNTOUCHED_EXTERNAL_V3_CONTRACT.json",
    ),
    "odsp.information_lattice_positive_v2.certify_positive_information_lattice_v2": (
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
        "ODSP_INDEPENDENT_DIRECTIONAL_LATTICE_4EDGE_CONTRACT.json",
    ),
    "odsp.refit_positive_independent_lattice_robustness.certify_all_refit_independent_positive_information_lattice_v2": (
        "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json",
        "ODSP_INDEPENDENT_DIRECTIONAL_LATTICE_4EDGE_CONTRACT.json",
        "ODSP_ALL_REFIT_INDEPENDENT_DIRECTIONAL_LATTICE_4EDGE_CONTRACT.json",
    ),
    "odsp.shared_block_positive_information.certify_shared_block_positive_information_lattice_v2": (
        "PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json",
    ),
    "odsp.refit_positive_lattice_robustness.certify_all_refit_shared_block_positive_information_lattice_v2": (
        "PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json",
        "ODSP_ALL_REFIT_PAIRED_POSITIVE_LATTICE_CONTRACT.json",
    ),
    "odsp.untouched_external_refit_shared_block_positive_lattice_contract_v4.run_untouched_external_paired_all_refit_lattice_contract_v4": (
        "PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json",
        "ODSP_ALL_REFIT_PAIRED_POSITIVE_LATTICE_CONTRACT.json",
        "ODSP_UNTOUCHED_EXTERNAL_PAIRED_ALL_REFIT_LATTICE_V4_CONTRACT.json",
    ),
    "odsp.information_transfer_v2.certify_information_transfer_v2": (
        "MULTICONTRAST_BOOTSTRAP_T_V2_OPERATING_CHARACTERISTICS_RECEIPT.json",
    ),
    "odsp.information_lattice_v2.certify_information_lattice_v2": (
        "MULTICONTRAST_BOOTSTRAP_T_V2_OPERATING_CHARACTERISTICS_RECEIPT.json",
        "ODSP_INFORMATION_TRANSFER_BOOTSTRAP_T_V2_CONTRACT.json",
    ),
}


def qualification_evidence_for_surface(surface: str) -> tuple[str, ...]:
    """Return frozen files supporting a canonical confirmatory method surface."""

    value = str(surface).strip()
    if not value:
        return ()
    return CONFIRMATORY_EVIDENCE_BY_SURFACE.get(value, ())
