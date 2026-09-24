#!/usr/bin/env python3
"""Aggregate frozen N2 stage-2 real-data triangulation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_POOLED_REFERENCE_FAILURE_MODE_STAGE2_REAL_DATA_CONTRACT.json"
BOP_V2 = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT_V2.json"
BOP_SPECIES = ROOT / "BOP_RODENT_SPECIES_BASELINE_AMENDMENT_RECEIPT.json"
SERENGETI = ROOT / "N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json"


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _system_flags(
    naive_mean: float,
    naive_status: str,
    corrected_mean: float,
    corrected_status: str,
) -> dict[str, object]:
    point_sign_reversal = bool(naive_mean > 0.0 and corrected_mean <= 0.0)
    inferential_downgrade = bool(
        naive_status == "positive" and corrected_status != "positive"
    )
    strong_attenuation = bool(
        naive_mean > 0.0
        and abs(corrected_mean) <= 0.5 * abs(naive_mean)
    )
    return {
        "point_sign_reversal": point_sign_reversal,
        "inferential_downgrade": inferential_downgrade,
        "strong_attenuation": strong_attenuation,
    }


def aggregate(penguins_result_path: Path) -> dict[str, object]:
    contract = _read(CONTRACT)
    penguins = _read(penguins_result_path)
    bop = _read(BOP_V2)
    bop_species = _read(BOP_SPECIES)
    serengeti = _read(SERENGETI)

    if penguins["contract_id"] != contract["contract_id"]:
        raise ValueError("Penguins result contract_id mismatch")
    if penguins["contract_merge_sha"] != (
        "8a83079f395b7e22bf82d87a430d8169247bf996"
    ):
        raise ValueError("Penguins result contract merge SHA mismatch")
    if bop["contract_id"] != "bop-rodent-population-transfer-descriptive-amendment-v2":
        raise ValueError("BOP v2 receipt mismatch")
    if serengeti["terminal_category"] != "temporal_partition_generalizing":
        raise ValueError("frozen Serengeti semantic control drifted")

    bop_total = bop["population_result"]["total_gain"]
    bop_context = bop["population_result"]["steps"][1]
    bop_flags = _system_flags(
        float(bop_total["mean_gain"]),
        str(bop_total["mean_gain_status"]),
        float(bop_context["mean_gain"]),
        str(bop_context["mean_gain_status"]),
    )

    penguins_naive = penguins["naive_pooled_gain"]
    penguins_context = penguins["audit_context_gain"]
    penguins_flags = _system_flags(
        float(penguins_naive["mean_gain"]),
        str(penguins_naive["mean_gain_status"]),
        float(penguins_context["mean_gain"]),
        str(penguins_context["mean_gain_status"]),
    )
    if penguins_flags != penguins["decision_components"]:
        raise ValueError("Penguins frozen decision components are inconsistent")

    systems = {
        "BOP_RODENT": {
            "role": "frozen_explicit_layer_motivating_example",
            "naive_pooled_mean_gain": float(bop_total["mean_gain"]),
            "naive_pooled_status": str(bop_total["mean_gain_status"]),
            "corrected_context_mean_gain": float(bop_context["mean_gain"]),
            "corrected_context_status": str(bop_context["mean_gain_status"]),
            **bop_flags,
            "fresh_outcome": False,
        },
        "PALMER_PENGUINS": {
            "role": "fresh_proxy_layer_test",
            "naive_pooled_mean_gain": float(penguins_naive["mean_gain"]),
            "naive_pooled_status": str(penguins_naive["mean_gain_status"]),
            "corrected_context_mean_gain": float(penguins_context["mean_gain"]),
            "corrected_context_status": str(penguins_context["mean_gain_status"]),
            **penguins_flags,
            "fresh_outcome": True,
            "fresh_decision": penguins["decision"],
        },
    }

    denominator = contract["primary_reporting"]["system_flip_denominator"]
    if denominator != ["BOP_RODENT", "PALMER_PENGUINS"]:
        raise ValueError("stage-2 system denominator drifted")

    counts = {
        "system_count": len(denominator),
        "point_sign_reversal_count": sum(
            int(bool(systems[system]["point_sign_reversal"]))
            for system in denominator
        ),
        "inferential_downgrade_count": sum(
            int(bool(systems[system]["inferential_downgrade"]))
            for system in denominator
        ),
        "strong_attenuation_count": sum(
            int(bool(systems[system]["strong_attenuation"]))
            for system in denominator
        ),
    }

    buteo = bop_species["species_summary"]["Buteo buteo"]
    sentinel = {
        "species": "Buteo buteo",
        "mean_total_gain": float(buteo["mean_total_gain"]),
        "mean_species_component": float(buteo["mean_species_component"]),
        "mean_context_within_species_component": float(
            buteo["mean_context_within_species_component"]
        ),
        "descriptive_point_sign_reversal": bool(
            float(buteo["mean_total_gain"]) > 0.0
            and float(buteo["mean_context_within_species_component"]) <= 0.0
        ),
        "included_in_system_flip_denominator": False,
    }

    semantic_control = {
        "system_id": "SNAPSHOT_SERENGETI",
        "terminal_category": serengeti["terminal_category"],
        "transfer_category": serengeti["transfer_category"],
        "heldout_gains": serengeti["heldout_gains"],
        "claimed_information": "species identity",
        "pooled_reference_scientifically_appropriate": True,
        "reason": (
            "species identity itself is the transferred information being claimed; "
            "conditioning species away would answer a different question"
        ),
        "included_in_system_flip_denominator": False,
    }

    return {
        "schema_version": 1,
        "result_id": "n2-pooled-reference-failure-mode-stage2-real-data-result-v1",
        "contract_id": contract["contract_id"],
        "contract_merge_sha": "8a83079f395b7e22bf82d87a430d8169247bf996",
        "few_cluster_fix_merge_sha": contract["prerequisites"][
            "few_cluster_fix_merge_sha"
        ],
        "systems": systems,
        "counts": counts,
        "buteo_motivating_sentinel": sentinel,
        "semantic_negative_control": semantic_control,
        "fresh_penguins_result": {
            "result_id": penguins["result_id"],
            "source": penguins["source"],
            "decision": penguins["decision"],
        },
        "scientific_interpretation_boundary": {
            "stage1_remains_primary_mechanistic_evidence": True,
            "stage2_estimates_literature_prevalence": False,
            "two_system_denominator_is_descriptive_only": True,
            "pooled_reference_is_not_intrinsically_wrong": True,
            "reference_must_match_claimed_information": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--penguins-result", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = aggregate(args.penguins_result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
