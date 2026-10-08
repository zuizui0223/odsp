#!/usr/bin/env python3
"""Prospectively frozen shared-validation e-IUT v0 operating-characteristic panel.

This script reads the already-committed simulation plan, does not modify its
scenario/gate parameters, and emits a JSON receipt BEFORE its final exit code.
It does not authorize route registration or ecological generalization.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np

from odsp.future_refit_shared_validation_evalue_v0 import (
    COMPONENT_TEST_ALPHA,
    METHOD_VERSION,
    PROCESS_ALPHA,
    VALIDATION_MARKOV_DELTA,
    evaluate_future_refit_shared_validation_evalue_v0,
)

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "ODSP_FUTURE_REFIT_SHARED_EVALUE_V0_SIMULATION_PLAN.json"
SHA = "7" * 64


def _validation_noise(rng: np.random.Generator, kind: str, B: int) -> np.ndarray:
    if kind == "symmetric":
        return rng.choice(np.array([-1.0, 1.0]), size=(2, B, 2))
    if kind == "rare_negative":
        return np.where(rng.random((2, B, 2)) < 0.05, -1.0, 1.0/19.0)
    if kind == "perfect_block_correlation":
        sign = float(rng.choice(np.array([-1.0, 1.0])))
        return np.full((2, B, 2), sign)
    raise ValueError("unfrozen noise kind")


def _case_arrays(
    rng: np.random.Generator,
    *,
    p: float,
    R: int,
    B: int,
    mu: float,
    positive_amp: float,
    null_amp: float,
    noise_kind: str,
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...], tuple[str, ...]]:
    # Draw V ONCE; all R iid model-refit types are generated independently.
    env = _validation_noise(rng, noise_kind, B)
    success = rng.random(R) < p
    scores = mu + positive_amp * np.broadcast_to(env, (R, 2, B, 2))
    scores = scores.copy()
    scores[~success, 0, :, 0] = null_amp * env[0, :, 0]
    if not np.isfinite(scores).all() or np.min(scores) < -1.0-1e-12 or np.max(scores) > 1.0+1e-12:
        raise ValueError("synthetic score out of frozen [-1,1] range")
    gains = scores.reshape(R, 2*B, 2)
    groups = tuple(f"g{gi}" for gi in range(2) for _ in range(B))
    blocks = tuple(f"g{gi}-b{bi:04d}" for gi in range(2) for bi in range(B))
    return gains, success, groups, blocks


def _one_simulation(
    rng: np.random.Generator,
    *,
    p: float,
    R: int,
    B: int,
    mu: float,
    positive_amp: float,
    null_amp: float,
    noise_kind: str,
) -> tuple[float, int, bool]:
    gains, true_success, groups, blocks = _case_arrays(
        rng, p=p, R=R, B=B, mu=mu, positive_amp=positive_amp,
        null_amp=null_amp, noise_kind=noise_kind,
    )
    outcome = evaluate_future_refit_shared_validation_evalue_v0(
        gains, groups, blocks=blocks,
        refit_ids=tuple(f"r{i:03d}" for i in range(R)),
        training_process_id="frozen-known-p-statistical-simulation-only",
        training_process_manifest_sha256=SHA,
    )
    if outcome.qualification_status != "experimental_unqualified":
        raise AssertionError("statistical simulation must not grant primary status")
    false_certified = any(
        row.certified_success and not bool(truth)
        for row, truth in zip(outcome.refits, true_success)
    )
    return (
        outcome.true_future_refit_success_probability_lower,
        outcome.certified_success_count,
        false_certified,
    )


def _cases(plan: dict[str, object]) -> list[dict[str, object]]:
    cases = []
    for name, kind, p, B, mu, amp, null_amp in plan["coverage_cases"]:
        cases.append(dict(
            id=name, role="coverage", p=float(p), B=int(B), mu=float(mu),
            amp=float(amp), null_amp=float(null_amp), noise_kind=kind,
        ))
    for name, p, B, mu, amp in plan["power_cases"]:
        cases.append(dict(
            id=name, role="power_required", p=float(p), B=int(B),
            mu=float(mu), amp=float(amp), null_amp=0.9,
            noise_kind="symmetric",
        ))
    for name, p, B, mu, amp in plan["diagnostic_cases"]:
        cases.append(dict(
            id=name, role="power_diagnostic_only", p=float(p), B=int(B),
            mu=float(mu), amp=float(amp), null_amp=0.9,
            noise_kind="symmetric",
        ))
    assert plan["invalid_design_control"].startswith("same Rademacher shock")
    cases.append(dict(
        id="non_iid_blocks_shared_shock", role="invalid_design_sentinel",
        p=0.0, B=12, mu=0.9, amp=0.05, null_amp=0.9,
        noise_kind="perfect_block_correlation",
    ))
    return cases


def main() -> int:
    raw = PLAN.read_bytes()
    plan = json.loads(raw)
    if (plan["route"] != "shared_validation_evalue_v0"
        or plan["status"] != "experimental_preregistered_statistical_simulation"
        or plan["replicates_per_scenario"] != 1000
        or plan["refits"] != 20 or plan["validation_groups"] != 2
        or plan["contrasts"] != 2 or plan["score_range"] != [-1, 1]
        or plan["seed"] != 2026100802 or plan["success_threshold"] != 0.8
        or not plan["do_not_change_after_first_result"]
        or plan["qualified_primary"]
        or METHOD_VERSION != "future_refit_shared_validation_evalue_v0"
        or plan["test_alpha"] != COMPONENT_TEST_ALPHA
        or plan["validation_markov_delta"] != VALIDATION_MARKOV_DELTA
        or plan["process_alpha"] != PROCESS_ALPHA):
        raise ValueError("frozen panel design or implementation identity mismatch")

    rng = np.random.default_rng(int(plan["seed"]))
    total_worlds = int(plan["replicates_per_scenario"])
    outcomes = []
    gates = plan["gates"]
    for case in _cases(plan):
        overclaim = false_cert_panel = decision = all_certified = 0
        total_K = 0
        for _ in range(total_worlds):
            p_bound, K, any_false = _one_simulation(
                rng, p=case["p"], R=plan["refits"], B=case["B"],
                mu=case["mu"], positive_amp=case["amp"],
                null_amp=case["null_amp"], noise_kind=case["noise_kind"]
            )
            overclaim += p_bound > case["p"] + 1e-12
            false_cert_panel += any_false
            decision += p_bound > plan["success_threshold"]
            all_certified += K == plan["refits"]
            total_K += K
        ov = overclaim/total_worlds
        fp = false_cert_panel/total_worlds
        pow_ = decision/total_worlds
        if case["role"] == "coverage":
            passed = ov <= gates["coverage_overstatement_max"] and fp <= gates["any_false_certificate_panel_max"]
        elif case["role"] == "power_required":
            passed = pow_ >= gates["each_required_power_min"]
        elif case["role"] == "invalid_design_sentinel":
            # This deliberately violates iid validation-block assumptions.
            passed = ov >= gates["invalid_design_overstatement_min"]
        else:
            passed = True
        outcomes.append({
            "id": case["id"], "role": case["role"],
            "p_true": case["p"], "validation_blocks_per_group": case["B"],
            "positive_mean_gain": case["mu"], "noise_kind": case["noise_kind"],
            "n_worlds": total_worlds,
            "overclaim_rate": ov, "any_false_certificate_panel_rate": fp,
            "probability_lower_bound_above_0p8": pow_,
            "all_certified_rate": all_certified/total_worlds,
            "mean_certified_refits": total_K/total_worlds,
            "frozen_gate_passed": bool(passed),
        })
    is_pass = all(x["frozen_gate_passed"] for x in outcomes)
    receipt = {
        "schema_version": 1, "route": METHOD_VERSION,
        "status": "statistical_panel_pass" if is_pass else "statistical_panel_failed",
        "primary_qualified": False,
        "contract_path": str(PLAN.relative_to(ROOT)),
        "contract_sha256": hashlib.sha256(raw).hexdigest(),
        "method_head_sha": os.environ.get("GITHUB_SHA", "unknown"),
        "seed": plan["seed"],
        "world_repetitions": total_worlds,
        "frozen_alpha": {"test": COMPONENT_TEST_ALPHA, "delta": VALIDATION_MARKOV_DELTA, "process": PROCESS_ALPHA},
        "all_required_gates_passed": is_pass,
        "results": outcomes,
        "existing_routes_reclassified": False,
    }
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False), flush=True)
    return 0 if is_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
