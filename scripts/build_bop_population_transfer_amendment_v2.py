#!/usr/bin/env python3
"""Build the corrected post-outcome BOP population-transfer amendment v2."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from odsp.population_transfer import (
    PopulationTransferSummary,
    _summarize_gain_vector,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_CONTRACT_V2.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    if len(cluster_labels) != int(settings["observed_cluster_count"]):
        raise AssertionError("observed species cluster count drifted")
    confidence = float(settings["confidence_level"])
    draws = int(settings["bootstrap_draws_if_cluster_count_at_least_threshold"])
    seed = int(settings["seed"])
    tolerance = float(settings["gain_tolerance"])

    total = _summarize_gain_vector(
        [float(row["total_gain_frozen"]) for row in rows],
        lower_level="pooled",
        upper_level="species_context",
        cluster_labels=cluster_labels,
        cluster_indices=cluster_indices,
        cluster_variable_declared=True,
        confidence_level=confidence,
        bootstrap_draws=draws,
        seed=seed,
        gain_tolerance=tolerance,
    )
    species_step = _summarize_gain_vector(
        [float(row["species_component"]) for row in rows],
        lower_level="pooled",
        upper_level="species",
        cluster_labels=cluster_labels,
        cluster_indices=cluster_indices,
        cluster_variable_declared=True,
        confidence_level=confidence,
        bootstrap_draws=draws,
        seed=seed + 1,
        gain_tolerance=tolerance,
    )
    context_step = _summarize_gain_vector(
        [float(row["context_within_species_component"]) for row in rows],
        lower_level="species",
        upper_level="species_context",
        cluster_labels=cluster_labels,
        cluster_indices=cluster_indices,
        cluster_variable_declared=True,
        confidence_level=confidence,
        bootstrap_draws=draws,
        seed=seed + 2,
        gain_tolerance=tolerance,
    )
    steps = (species_step, context_step)
    ceiling = "pooled"
    for level, step in zip(("species", "species_context"), steps):
        if step.mean_gain_status == "positive":
            ceiling = level
        else:
            break

    summary = PopulationTransferSummary(
        estimand="equal_weight_mean_gain_across_groups",
        role="descriptive_population_level_secondary_summary",
        gain_tolerance=tolerance,
        confidence_level=confidence,
        bootstrap_draws=draws,
        seed=seed,
        group_count=len(rows),
        cluster_count=len(cluster_labels),
        cluster_variable_declared=True,
        resampling_unit="declared_population_cluster",
        total_gain=total,
        steps=steps,
        population_mean_supported_ceiling=ceiling,
    )

    frozen = contract["frozen_primary_endpoint"]
    return {
        "schema_version": 2,
        "amendment_id": "bop-rodent-population-transfer-descriptive-amendment-result-v2",
        "contract_id": contract["contract_id"],
        "post_outcome_amendment": True,
        "analysis_type": contract["analysis_type"],
        "supersedes": contract["supersedes"],
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
        "population_result": summary.as_dict(),
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
