#!/usr/bin/env python3
"""Rebuild the historical BOP population-transfer v1 result exactly.

This script is intentionally a compatibility reproducer for the superseded v1
few-cluster percentile-bootstrap analysis.  New population inference must use the
corrected v2 builder instead.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_CONTRACT.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _legacy_step(
    gains: list[float],
    *,
    lower_level: str,
    upper_level: str,
    cluster_labels: tuple[str, ...],
    cluster_indices: dict[str, np.ndarray],
    confidence_level: float,
    bootstrap_draws: int,
    seed: int,
    gain_tolerance: float,
) -> dict[str, object]:
    values = np.asarray(gains, dtype=float)
    rng = np.random.default_rng(seed)
    alpha = 1.0 - confidence_level
    boot_means = np.empty(bootstrap_draws, dtype=float)
    boot_positive = np.empty(bootstrap_draws, dtype=float)
    for draw in range(bootstrap_draws):
        sampled_cluster_indices = rng.choice(
            cluster_labels, size=len(cluster_labels), replace=True
        )
        sampled = np.concatenate(
            [cluster_indices[cluster] for cluster in sampled_cluster_indices]
        )
        draw_gains = values[sampled]
        boot_means[draw] = float(np.mean(draw_gains))
        boot_positive[draw] = float(np.mean(draw_gains > gain_tolerance))

    mean_gain = float(np.mean(values))
    lower, upper = np.quantile(
        boot_means, [alpha / 2.0, 1.0 - alpha / 2.0]
    )
    positive_count = int(np.count_nonzero(values > gain_tolerance))
    positive_fraction = float(positive_count / values.size)
    positive_lower = float(np.quantile(boot_positive, alpha / 2.0))
    sd = float(np.std(values, ddof=1)) if values.size >= 2 else None
    if sd is not None:
        z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
        half_width = z * sd * math.sqrt(1.0 + 1.0 / values.size)
        prediction_lower = float(mean_gain - half_width)
        prediction_upper = float(mean_gain + half_width)
        prediction_method = "normal_theory"
        prediction_assumption = "approximately_normal_group_gain_distribution"
    else:
        prediction_lower = prediction_upper = None
        prediction_method = prediction_assumption = None
    p10, p50, p90 = np.quantile(values, [0.1, 0.5, 0.9])
    if lower > gain_tolerance:
        status = "positive"
    elif upper <= gain_tolerance:
        status = "nonpositive"
    else:
        status = "uncertain"
    return {
        "lower_level": lower_level,
        "upper_level": upper_level,
        "group_count": int(values.size),
        "cluster_count": len(cluster_labels),
        "bootstrap_seed": int(seed),
        "mean_gain": mean_gain,
        "mean_gain_lower": float(lower),
        "mean_gain_upper": float(upper),
        "mean_gain_status": status,
        "positive_group_count": positive_count,
        "positive_group_fraction": positive_fraction,
        "positive_fraction_lower": positive_lower,
        "positive_fraction_lower_method": "cluster_percentile_bootstrap",
        "group_gain_sd": sd,
        "prediction_lower": prediction_lower,
        "prediction_upper": prediction_upper,
        "prediction_method": prediction_method,
        "prediction_assumption": prediction_assumption,
        "empirical_p10": float(p10),
        "empirical_p50": float(p50),
        "empirical_p90": float(p90),
    }


def build(species_baseline_result_path: Path) -> dict[str, object]:
    contract = _read(CONTRACT_PATH)
    observed_sha = _sha256(species_baseline_result_path)
    expected_sha = str(contract["source_evidence"]["result_json_sha256"])
    if observed_sha != expected_sha:
        raise AssertionError(
            f"species-baseline result sha256 mismatch: expected {expected_sha}, observed {observed_sha}"
        )
    source = _read(species_baseline_result_path)
    if source.get("contract_id") != contract["source_evidence"]["species_baseline_amendment_contract_id"]:
        raise AssertionError("species-baseline amendment contract_id drifted")
    if source.get("post_outcome_amendment") is not True:
        raise AssertionError("source amendment lost post-outcome status")
    for key in ("model_refit_performed", "raw_source_data_reaccessed", "retuning_performed"):
        if source.get(key) is not False:
            raise AssertionError(f"forbidden source mutation flag changed: {key}")

    rows = source["decomposition"]["individual_rows"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("species-baseline amendment must contain individual_rows")
    group_labels = [str(row["heldout_individual"]) for row in rows]
    if len(set(group_labels)) != len(group_labels):
        raise ValueError("heldout_individual identifiers must be unique")
    species = [str(row["species"]) for row in rows]
    cluster_labels = tuple(dict.fromkeys(species))
    cluster_indices = {
        cluster: np.asarray(
            [index for index, value in enumerate(species) if value == cluster],
            dtype=int,
        )
        for cluster in cluster_labels
    }
    settings = contract["population_estimand"]
    confidence = float(settings["confidence_level"])
    draws = int(settings["bootstrap_draws"])
    seed = int(settings["seed"])
    tolerance = float(settings["gain_tolerance"])

    total = _legacy_step(
        [float(row["total_gain_frozen"]) for row in rows],
        lower_level="pooled",
        upper_level="species_context",
        cluster_labels=cluster_labels,
        cluster_indices=cluster_indices,
        confidence_level=confidence,
        bootstrap_draws=draws,
        seed=seed,
        gain_tolerance=tolerance,
    )
    species_step = _legacy_step(
        [float(row["species_component"]) for row in rows],
        lower_level="pooled",
        upper_level="species",
        cluster_labels=cluster_labels,
        cluster_indices=cluster_indices,
        confidence_level=confidence,
        bootstrap_draws=draws,
        seed=seed + 1,
        gain_tolerance=tolerance,
    )
    context_step = _legacy_step(
        [float(row["context_within_species_component"]) for row in rows],
        lower_level="species",
        upper_level="species_context",
        cluster_labels=cluster_labels,
        cluster_indices=cluster_indices,
        confidence_level=confidence,
        bootstrap_draws=draws,
        seed=seed + 2,
        gain_tolerance=tolerance,
    )
    steps = [species_step, context_step]
    ceiling = "pooled"
    for level, step in zip(("species", "species_context"), steps):
        if step["mean_gain_status"] == "positive":
            ceiling = level
        else:
            break

    population_result = {
        "estimand": "equal_weight_mean_gain_across_groups",
        "role": "descriptive_population_level_secondary_summary",
        "familywise_confirmatory_claim": False,
        "gain_tolerance": tolerance,
        "group_count": len(rows),
        "cluster_count": len(cluster_labels),
        "cluster_variable_declared": True,
        "uncertainty": {
            "mean_interval_method": "cluster_percentile_bootstrap",
            "confidence_level": confidence,
            "bootstrap_draws": draws,
            "seed": seed,
            "resampling_unit": "declared_population_cluster",
            "within_group_refit_uncertainty_propagated": False,
            "cluster_bootstrap_limitation": (
                "cluster-bootstrap uncertainty can be unstable with few declared population clusters"
            ),
        },
        "total_gain": total,
        "steps": steps,
        "population_mean_supported_ceiling": ceiling,
    }

    frozen = contract["frozen_primary_endpoint"]
    return {
        "schema_version": 1,
        "amendment_id": "bop-rodent-population-transfer-descriptive-amendment-result-v1",
        "contract_id": contract["contract_id"],
        "post_outcome_amendment": True,
        "analysis_type": contract["analysis_type"],
        "source_evidence": {
            "workflow_run_id": int(contract["source_evidence"]["workflow_run_id"]),
            "artifact_id": int(contract["source_evidence"]["artifact_id"]),
            "artifact_digest": contract["source_evidence"]["artifact_digest"],
            "result_json_sha256": observed_sha,
        },
        "frozen_primary_endpoint": {
            "terminal_category": frozen["terminal_category"],
            "positive_individual_count": int(frozen["positive_individual_count"]),
            "eligible_individual_count": int(frozen["eligible_individual_count"]),
            "mean_total_gain": float(frozen["mean_total_gain"]),
            "terminal_decision_recomputed": False,
            "terminal_decision_changed": False,
        },
        "population_result": population_result,
        "model_refit_performed": False,
        "raw_source_data_reaccessed": False,
        "retuning_performed": False,
        "claim_boundary": contract["claim_boundary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--species-baseline-result", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.species_baseline_result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["population_result"]["total_gain"], sort_keys=True))


if __name__ == "__main__":
    main()
