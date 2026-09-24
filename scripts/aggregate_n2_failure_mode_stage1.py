#!/usr/bin/env python3
"""Aggregate all shards from the single frozen N2 stage-1 execution."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

from odsp.n2_failure_mode_stage1 import (
    FROZEN_CONTRACT_MERGE_SHA,
    Stage1Scenario,
    bop_oracle_check,
    load_stage1_contract,
    scenario_grid,
    summarize_replicates,
)


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _anchor_scenario(anchor: Mapping[str, object]) -> Stage1Scenario:
    return Stage1Scenario(
        layer_effect_scale=float(anchor["layer_effect_scale"]),
        within_layer_context_effect=float(anchor["within_layer_context_effect"]),
        group_count=int(anchor["group_count"]),
        events_per_group=int(anchor["events_per_group"]),
        layer_count=int(anchor["layer_count"]),
        context_layer_correlation=str(anchor["context_layer_correlation"]),
        focal_learner_layer_identity=str(anchor["focal_learner_layer_identity"]),
    )


def _metric_value(summary: Mapping[str, object], quantity: str) -> float:
    if quantity in {"false_positive_rate", "power"}:
        return float(summary["positive_declaration_rate"])
    if quantity == "availability_fraction":
        return float(summary["availability_fraction"])
    if quantity == "absolute_mean_bias_nats_per_event":
        return float(summary["absolute_mean_bias_nats_per_event"])
    raise ValueError(f"unknown success-rule quantity: {quantity}")


def _evaluate_rule(
    rule: Mapping[str, object],
    anchors: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    anchor_id = str(rule["anchor_id"])
    method_id = str(rule["method_id"])
    quantity = str(rule["quantity"])
    observed = _metric_value(anchors[anchor_id][method_id], quantity)
    acceptance = str(rule["acceptance"])
    threshold = float(rule["threshold"])
    if acceptance == "wilson_95_lower_bound_gt":
        observed_for_decision = float(
            anchors[anchor_id][method_id]["positive_declaration_wilson_95_lower"]
        )
        passed = observed_for_decision > threshold
    elif acceptance == "point_estimate_lte":
        observed_for_decision = observed
        passed = observed <= threshold
    elif acceptance == "point_estimate_gte":
        observed_for_decision = observed
        passed = observed >= threshold
    else:
        raise ValueError(f"unknown acceptance rule: {acceptance}")
    return {
        "anchor_id": anchor_id,
        "method_id": method_id,
        "quantity": quantity,
        "point_estimate": observed,
        "decision_value": observed_for_decision,
        "acceptance": acceptance,
        "threshold": threshold,
        "passed": bool(passed),
    }


def _decision_tree_matches(
    rule_groups: Mapping[str, list[dict[str, object]]],
    bop_passed: bool,
) -> dict[str, bool]:
    all_rules = [row for values in rule_groups.values() for row in values]
    failure = {
        (row["anchor_id"], row["method_id"]): bool(row["passed"])
        for row in rule_groups["false_positive_failure_mode"]
    }
    type1_ok = all(bool(row["passed"]) for row in rule_groups["correction_type_i_error"])
    availability_ok = all(
        bool(row["passed"]) for row in rule_groups["primary_method_availability"]
    )
    a_ok = failure.get(
        ("A_explicit_layer_pooled_reference", "group_cv_pooled_log_gain"), False
    )
    b_ok = failure.get(
        ("B_context_proxy_for_layer", "group_cv_pooled_log_gain"), False
    )
    power_ok = all(bool(row["passed"]) for row in rule_groups["correction_power"])
    return {
        "full_failure_mode_paper": bool(
            bop_passed and all(bool(row["passed"]) for row in all_rules)
        ),
        "narrow_explicit_layer_only_paper": bool(
            bop_passed and a_ok and type1_ok and availability_ok and not b_ok
        ),
        "diagnostic_only_rescope": bool(
            bop_passed and a_ok and type1_ok and availability_ok and not power_ok
        ),
        "central_claim_withdrawn": bool(
            (not bop_passed) or (not a_ok) or (not type1_ok) or (not availability_ok)
        ),
    }

def aggregate(input_dir: Path, contract_path: Path) -> dict[str, object]:
    contract = load_stage1_contract(contract_path)
    files = sorted(input_dir.rglob("*.json"))
    payloads = [_read(path) for path in files]
    payloads = [
        value
        for value in payloads
        if value.get("result_role")
        in {"descriptive_factorial_shard", "confirmatory_anchor_shard"}
    ]
    if not payloads:
        raise ValueError("no stage-1 shard JSON files found")

    for value in payloads:
        if value.get("contract_id") != contract["contract_id"]:
            raise ValueError("shard contract_id mismatch")
        if value.get("contract_merge_sha") != FROZEN_CONTRACT_MERGE_SHA:
            raise ValueError("shard contract merge SHA mismatch")

    expected_cells = len(scenario_grid(contract))
    factorial: dict[int, dict[str, object]] = {}
    anchor_worlds: dict[str, dict[int, dict[str, object]]] = {}
    for value in payloads:
        role = value["result_role"]
        if role == "descriptive_factorial_shard":
            for cell in value["cells"]:
                index = int(cell["cell_index"])
                if index in factorial:
                    raise ValueError(f"duplicate factorial cell {index}")
                factorial[index] = cell
        else:
            anchor_id = str(value["anchor_id"])
            target = anchor_worlds.setdefault(anchor_id, {})
            for replicate, world in zip(value["replicate_indices"], value["worlds"]):
                index = int(replicate)
                if index in target:
                    raise ValueError(f"duplicate anchor replicate {anchor_id}:{index}")
                target[index] = world

    if set(factorial) != set(range(expected_cells)):
        missing = sorted(set(range(expected_cells)) - set(factorial))
        extra = sorted(set(factorial) - set(range(expected_cells)))
        raise ValueError(f"factorial coverage mismatch: missing={missing[:10]}, extra={extra[:10]}")

    execution = contract["confirmatory_anchor_execution"]
    planned = int(execution["replicates_per_anchor"])
    anchor_summaries: dict[str, dict[str, object]] = {}
    for anchor in execution["anchors"]:
        anchor_id = str(anchor["anchor_id"])
        worlds = anchor_worlds.get(anchor_id, {})
        if set(worlds) != set(range(planned)):
            missing = sorted(set(range(planned)) - set(worlds))
            extra = sorted(set(worlds) - set(range(planned)))
            raise ValueError(
                f"anchor coverage mismatch for {anchor_id}: "
                f"missing={missing[:10]}, extra={extra[:10]}"
            )
        anchor_summaries[anchor_id] = summarize_replicates(
            _anchor_scenario(anchor),
            [worlds[index] for index in range(planned)],
            contract=contract,
        )

    rules = contract["success_rules"]
    groups: dict[str, list[dict[str, object]]] = {}
    for name in (
        "false_positive_failure_mode",
        "mechanism_negative_control",
        "correction_type_i_error",
        "correction_power",
        "high_information_bias",
        "primary_method_availability",
    ):
        groups[name] = [
            _evaluate_rule(rule, anchor_summaries) for rule in rules[name]
        ]

    bop = bop_oracle_check(contract)
    reality = rules["bop_reality_check"]
    lower = float(reality["lower"])
    upper = float(reality["upper"])
    bop["acceptance_interval"] = [lower, upper]
    bop["inside_frozen_window"] = bool(
        lower <= float(bop["observed_layer_gain"]) <= upper
    )
    bop_passed = bool(bop["passed"] and bop["inside_frozen_window"])

    decision_matches = _decision_tree_matches(groups, bop_passed)
    return {
        "schema_version": 1,
        "receipt_type": "n2_stratified_context_transfer_failure_mode_stage1_v1",
        "contract_id": contract["contract_id"],
        "contract_merge_sha": FROZEN_CONTRACT_MERGE_SHA,
        "one_shot_execution": True,
        "factorial": {
            "cell_count": expected_cells,
            "cells": [factorial[index] for index in range(expected_cells)],
        },
        "confirmatory_anchors": anchor_summaries,
        "success_rule_evaluation": groups,
        "bop_reality_check": bop,
        "decision_tree_matches": decision_matches,
        "full_claim_supported": bool(decision_matches["full_failure_mode_paper"]),
        "single_posthoc_decision_category_invented": False,
        "historical_v6_submission_reopened": False,
        "post_result_threshold_changes_permitted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = aggregate(args.input_dir, args.contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "decision_tree_matches": result["decision_tree_matches"],
                "full_claim_supported": result["full_claim_supported"],
                "factorial_cell_count": result["factorial"]["cell_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
