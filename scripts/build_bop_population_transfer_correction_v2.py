#!/usr/bin/env python3
"""Build the corrected BOP few-cluster population-transfer amendment v2."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from odsp.information_transfer import (
    InformationLevelScore,
    decompose_information_transfer,
)
from odsp.population_transfer import summarize_population_transfer


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "BOP_RODENT_POPULATION_TRANSFER_CORRECTION_CONTRACT_V2.json"


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
    individual = [str(row["heldout_individual"]) for row in rows]
    if len(set(individual)) != len(individual):
        raise ValueError("heldout_individual identifiers must be unique")
    species = [str(row["species"]) for row in rows]
    species_component = [float(row["species_component"]) for row in rows]
    total_gain = [float(row["total_gain_frozen"]) for row in rows]

    levels = (
        InformationLevelScore("pooled", (), [0.0] * len(rows)),
        InformationLevelScore("species", ("species",), species_component),
        InformationLevelScore(
            "species_context",
            ("species", "context"),
            total_gain,
        ),
    )
    point = decompose_information_transfer(
        levels,
        individual,
        score_name="frozen_log_score_gain_reconstruction",
        gain_tolerance=float(contract["population_estimand"]["gain_tolerance"]),
    )
    clusters = {
        group: cluster for group, cluster in zip(individual, species)
    }
    population = summarize_population_transfer(
        point,
        group_clusters=clusters,
        confidence_level=float(contract["population_estimand"]["confidence_level"]),
        bootstrap_draws=int(contract["population_estimand"]["bootstrap_draws"]),
        seed=int(contract["population_estimand"]["seed"]),
        gain_tolerance=float(contract["population_estimand"]["gain_tolerance"]),
    )

    frozen = contract["frozen_primary_endpoint"]
    return {
        "schema_version": 1,
        "amendment_id": "bop-rodent-population-transfer-few-cluster-correction-result-v2",
        "contract_id": contract["contract_id"],
        "supersedes_inference_from_contract_id": contract[
            "supersedes_inference_from_contract_id"
        ],
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
        "population_result": population.as_dict(),
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
