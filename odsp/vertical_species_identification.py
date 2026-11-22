"""Exact source-free counterexample: biological species-height information is not
identified from horizontal occurrence and unlinked multi-detector height counts.

One common site X, species S, strata Z. Observed mean = true intensity * q.
This uses existing ODSP information/overlap estimators for both true worlds.
It does not estimate detection in real data or claim a new ecological result.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .projection_loss import schoener_overlap
from .transferability import base_added_mutual_information


def conditional_species_height_information(
    support_xsz: np.ndarray, *, site_weights: np.ndarray | None = None
) -> dict[str, Any]:
    """Return I(S;Z|X), for a true (NOT uncorrected observed) support field.

    Shape: sites × species × strata. By default, sites are weighted by their
    share of declared source intensity; alternative fixed site weights must be
    supplied explicitly. Empty sites receive 0 weight. No pseudocount is added.
    """
    v = np.asarray(support_xsz, dtype=float)
    if v.ndim != 3 or min(v.shape) < 1 or v.shape[1] < 2 or v.shape[2] < 2:
        raise ValueError("support_xsz must be nonempty sites × >=2 species × >=2 strata")
    if not np.all(np.isfinite(v)) or np.any(v < 0) or not v.sum() > 0:
        raise ValueError("support_xsz must be finite, nonnegative, positive total")
    site_mass = v.sum(axis=(1, 2))
    if site_weights is None:
        w = site_mass / site_mass.sum()
        weighting = "source_intensity_share"
    else:
        w = np.asarray(site_weights, dtype=float)
        if w.shape != site_mass.shape or not np.all(np.isfinite(w)) or np.any(w < 0):
            raise ValueError("site_weights must be finite nonnegative, one per site")
        if np.any((site_mass == 0) & (w > 0)):
            raise ValueError("positive weight assigned to site without support")
        if w.sum() <= 0:
            raise ValueError("site_weights must have positive total")
        w = w / w.sum()
        weighting = "explicit_caller_site_weights"
    site_mi = np.array([
        base_added_mutual_information(v[i], base_axes=(0,), added_axes=(1,))
        if mass > 0 else float("nan")
        for i, mass in enumerate(site_mass)
    ], dtype=float)
    mi = float(np.dot(w, np.nan_to_num(site_mi, nan=0.0)))
    return {
        "information_nats": mi, "information_bits": mi / math.log(2.0),
        "site_weighting": weighting,
        "site_weights": w.tolist(),
        "per_site_information_nats": [float(a) if np.isfinite(a) else None for a in site_mi],
        "interpretation": "latent_species_height_information_only_if_support_is_observation_calibrated",
    }


def observed_poisson_means(latent_xsz: np.ndarray, detection_mxsz: np.ndarray) -> np.ndarray:
    """Independent unlinked method counts with unit known effort.

    All methods have a fully free species/height-specific detection probability,
    so the methods do not supply the missing population-level reference.
    """
    intensity = np.asarray(latent_xsz, dtype=float)
    detection = np.asarray(detection_mxsz, dtype=float)
    if intensity.ndim != 3 or detection.ndim != 4 or detection.shape[1:] != intensity.shape:
        raise ValueError("expected intensity X×S×Z and detection M×X×S×Z")
    if (np.any(~np.isfinite(intensity)) or np.any(intensity < 0) or
        np.any(~np.isfinite(detection)) or np.any((detection < 0) | (detection > 1))):
        raise ValueError("intensity must be nonnegative; detection probabilities within [0,1]")
    return intensity[None, :, :, :] * detection


def two_world_witness() -> dict[str, Any]:
    """Two ecological worlds with identical 2D intensity AND all observed means."""
    partition = np.array([[[90., 10.], [10., 90.]]])
    flat = np.array([[[50., 50.], [50., 50.]]])

    q_partition = np.stack([
        np.full_like(partition, .10), np.full_like(partition, .05)
    ])
    q_flat_first = np.array([[[.18, .02], [.02, .18]]])
    q_flat = np.stack([q_flat_first, q_flat_first / 2.0])

    y_partition = observed_poisson_means(partition, q_partition)
    y_flat = observed_poisson_means(flat, q_flat)
    if not np.array_equal(partition.sum(axis=-1), flat.sum(axis=-1)):
        raise AssertionError("invalid witness: planar intensity differs")
    if not np.allclose(y_partition, y_flat, atol=1e-12, rtol=0):
        raise AssertionError("invalid witness: observational distribution differs")

    ia = conditional_species_height_information(partition)
    ib = conditional_species_height_information(flat)
    observed_info = conditional_species_height_information(y_partition[0])
    overlap_2d = schoener_overlap(partition[0, 0:1], partition[0, 1:2], keep_axes=(0,))
    overlap_a = schoener_overlap(partition[0, 0:1], partition[0, 1:2])
    overlap_b = schoener_overlap(flat[0, 0:1], flat[0, 1:2])

    return {
        "kind": "synthetic_exact_observational_nonidentifiability",
        "not_real_animal_data": True,
        "method_count": 2,
        "biological_horizontal_intensity_same": True,
        "unlinked_observed_method_poisson_likelihood_same": True,
        "latent_intensity_world_A_xsz": partition.tolist(),
        "latent_intensity_world_B_xsz": flat.tolist(),
        "detection_world_A_mxsz": q_partition.tolist(),
        "detection_world_B_mxsz": q_flat.tolist(),
        "observed_method_means_both_worlds_mxsz": y_partition.tolist(),
        "true_world_A_I_species_height_given_site": ia,
        "true_world_B_I_species_height_given_site": ib,
        "naive_detected_method1_I_species_height_given_site": observed_info,
        "horizontal_schoener_overlap_both_worlds": overlap_2d,
        "full_schoener_overlap_world_A": overlap_a,
        "full_schoener_overlap_world_B": overlap_b,
        "projected_overlap_inflation_world_A": overlap_2d - overlap_a,
        "projected_overlap_inflation_world_B": overlap_2d - overlap_b,
        "inference": "ecological_I_not_point_identified_without_detector_calibration_or_additional_assumptions",
    }


def main() -> int:
    result = two_world_witness()
    dst = Path("results/vertical_species_identifiability_sourcefree_v1.json")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "exact_nonidentifiability_witness",
        "world_A_I_nats": result["true_world_A_I_species_height_given_site"]["information_nats"],
        "world_B_I_nats": result["true_world_B_I_species_height_given_site"]["information_nats"],
        "observed_I_nats": result["naive_detected_method1_I_species_height_given_site"]["information_nats"],
        "worlds_have_identical_2D_and_method_means": True,
        "data_type": "synthetic_only",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
