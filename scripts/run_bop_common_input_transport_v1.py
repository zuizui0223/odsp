#!/usr/bin/env python3
"""Preregistered known-truth BOP-to-Dryad *common-input* method benchmark.

Synthetic source-specific schemas only: no actual BOP or Dryad telemetry,
timestamp rows, animal IDs or altitude outcomes are accessed. Reuses the
executable training-only categorical learner plus one independent group
score per target individual. The original temperature/latitude RF is never
run, adapted or retrospectively scored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from odsp.common_input_transport import (
    CLASSES,
    calibrate_common_input_transport,
    freeze_common_input_transport,
    validate_common_input_transport,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/BOP_COMMON_INPUT_TRANSPORT_V1_CONTRACT.json"
_TRAIN_HEIGHT = (25.0, 120.0, 340.0, 700.0)


def load_frozen_contract(path: Path = CONTRACT) -> dict:
    c = json.loads(path.read_text(encoding="utf-8"))
    f = c.get("source_schema", {})
    gen = c.get("synthetic_generator", {})
    if (
        c.get("id") != "bop-common-input-transport-new-individual-v1"
        or c.get("role") != "prospective_known_truth_method_validation_only_not_real_BOP_or_Dryad_results"
        or c.get("predecessors",{}).get("closed_BOP_terminal") != "empirical_state_prediction_mixed"
        or c.get("predecessors",{}).get("Dryad_external_source_gate") != "NOT_ADMITTED"
        or c.get("predecessors",{}).get("Dryad_original_RF_gate") != "ORIGINAL_RF_PREDICTOR_INCOMPATIBLE"
        or gen.get("seed") != 20261028
        or gen.get("worlds") != 24
        or gen.get("group_counts_per_stratum") != {
            "BOP_training":20, "DRYAD_calibration":39,"DRYAD_validation":30
        }
        or gen.get("BOP_context_amplitude") != 1.4
        or gen.get("DRYAD_context_amplitude") != 1.1
        or gen.get("pseudocount") != 0.1
        or gen.get("miscoverage") != 0.1
        or gen.get("rank_39_cal_groups") != 4
        or gen.get("external_source_identity_verified_in_synthetic_only") is not True
        or f.get("altitude_class_labels") != list(CLASSES)
        or f.get("boundary_exclusion_hours") != 0.05/15
        or c.get("acceptance",{}).get("expected_validation_groups_each_condition") != 2880
    ):
        raise ValueError("pre-outcome common-input benchmark contract changed")
    return c


def _probabilities(base: list[float], context: int, amplitude: float) -> np.ndarray:
    p = np.asarray(base, dtype=float).copy()
    sign = +1 if context == 1 else -1
    p[0] *= math.exp(sign * amplitude)
    p[-1] *= math.exp(-sign * amplitude)
    return p / p.sum()


def _source(
    rng: np.random.Generator, world: int, stratum: str, role: str,
    number: int, min_events: int, max_events: int,
    *,
    training_prob: tuple[np.ndarray, np.ndarray] | None = None,
) -> tuple[list[dict[str, object]], dict[str, int]]:
    rows: list[dict[str, object]] = []
    feature_context: dict[str, int] = {}
    training = (role == "BOP_training")
    for group_i in range(number):
        group = f"world{world}_{stratum.replace(' ','_')}_{role}_{group_i:03d}"
        n = int(rng.integers(min_events, max_events + 1))
        q = float(rng.uniform(0.2, 0.8))
        for event in range(n):
            context = int(rng.random() < q)
            minute = int(rng.integers(0, 60))
            hour = "11" if context else "23"
            rid = f"{group}_event{event:03d}"
            timestamp = f"2025-06-08T{hour}:{minute:02d}:00Z"
            feature_context[rid] = context
            if training:
                if training_prob is None:
                    raise ValueError("training truth required only for BOP source")
                state = int(rng.choice(len(CLASSES), p=training_prob[context]))
                rows.append({
                    "row_id": rid,
                    "individual-local-identifier": group,
                    "individual-taxon-canonical-name": stratum,
                    "timestamp": timestamp, "location-long": 4.35,
                    "height-above-msl": _TRAIN_HEIGHT[state],
                })
            else:
                rows.append({
                    "row_id": rid,
                    "individual.global.identifier": group,
                    "individual.taxon.canonical.name": stratum,
                    "timestamp": timestamp, "location.long.rnd": 4.3,
                })
    return rows, feature_context


def _draw_outcomes(
    rng: np.random.Generator,
    context: dict[str, int],
    per_species: dict[str, tuple[np.ndarray, np.ndarray]],
    rows: list[dict[str, object]],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        name = str(row["row_id"])
        species = str(row["individual.taxon.canonical.name"])
        idx = int(rng.choice(4, p=per_species[species][context[name]]))
        result[name] = CLASSES[idx]
    return result


def run_world(contract: dict, world: int) -> dict[str, object]:
    settings = contract["synthetic_generator"]
    rng = np.random.default_rng(int(settings["seed"]) + world)
    species = tuple(contract["source_schema"]["allowed_strata"])
    groups = settings["group_counts_per_stratum"]
    min_events = settings["events_per_group"]["min"]
    max_events = settings["events_per_group"]["max"]
    base = settings["four_stratum_base_probabilities"]
    bop_truth = {
        name: tuple(_probabilities(base[i],ctx,float(settings["BOP_context_amplitude"]))
                    for ctx in (0,1))
        for i,name in enumerate(species)
    }
    target_truth = {
        name: tuple(_probabilities(base[i],ctx,float(settings["DRYAD_context_amplitude"]))
                    for ctx in (0,1))
        for i,name in enumerate(species)
    }
    train=[]
    cal=[]
    val=[]
    cal_context:dict[str,int]={}
    val_context:dict[str,int]={}
    for name in species:
        t,_ = _source(rng,world,name,"BOP_training",groups["BOP_training"],
                      min_events,max_events,training_prob=bop_truth[name])
        c,ci = _source(rng,world,name,"DRYAD_calibration",
                       groups["DRYAD_calibration"],min_events,max_events)
        v,vi = _source(rng,world,name,"DRYAD_validation",
                       groups["DRYAD_validation"],min_events,max_events)
        train.extend(t)
        cal.extend(c)
        val.extend(v)
        cal_context.update(ci)
        val_context.update(vi)

    # Freeze source-trained predictor, baseline, feature roster and both
    # calibration/validation forecasts *before* drawing target outcomes.
    fixed=freeze_common_input_transport(
        evidence_role="known_truth_synthetic_only",
        training_BOP_rows=train,
        calibration_Dryad_features=cal,
        validation_Dryad_features=val,
        pseudocount=float(settings["pseudocount"]),
        miscoverage=float(settings["miscoverage"]),
    )
    previous_plan=fixed.forecast.plan.digest
    frozen_manifest=fixed.public_manifest()
    if (
        frozen_manifest["original_RF_direct_transfer_admissible"] is not False
        or frozen_manifest["Dryad_external_candidate_admitted"] is not False
        or frozen_manifest["real_cross_source_individual_nonoverlap_verified"] is not False
        or frozen_manifest["original_BOP_terminal"] != "empirical_state_prediction_mixed"
    ):
        raise ValueError("common-input transport incorrectly promotes real data")

    calibration_state = _draw_outcomes(rng,cal_context,target_truth,cal)
    calibrated=calibrate_common_input_transport(fixed,calibration_state)
    # Held-out target truth generated for test ONLY after calibrator fixed.
    validation_state = _draw_outcomes(rng,val_context,target_truth,val)
    shifted = {
        row_id:CLASSES[(CLASSES.index(outcome)+2)%4]
        for row_id,outcome in validation_state.items()
    }
    same = validate_common_input_transport(fixed,calibrated,validation_state)
    adversarial = validate_common_input_transport(fixed,calibrated,shifted)
    if (
        fixed.forecast.plan.digest != previous_plan
        or same.plan_sha256 != adversarial.plan_sha256
        or same.calibration_sha256 != adversarial.calibration_sha256
        or same.validation_group_count != len(species)*groups["DRYAD_validation"]
        or any(s.finite_rank != 4 or s.vacuous for s in same.strata)
    ):
        raise ValueError("frozen per-animal rank model, group count or execution changed")
    return {
        "world": world,
        "training_individuals": frozen_manifest["training_group_count"],
        "calibration_individuals": frozen_manifest["calibration_group_count"],
        "validation_individuals": same.validation_group_count,
        "covered_same": same.covered_validation_group_count,
        "covered_validation_shift": adversarial.covered_validation_group_count,
        "calibration_sha256": calibrated.calibration_sha256,
        "frozen_forecast_plan_sha256": previous_plan,
        "model_sha256": frozen_manifest["model_sha256"],
        "reference_sha256": frozen_manifest["reference_sha256"],
        "group_sampling_target_source_stable_within_calibration_validation": True,
        "source_shift_from_BOP_training_to_Dryad_target": True,
        "training_model_refitted_after_target_outcome": False,
        "target_identity_crosswalk_real_world_verified": False,
        "original_bop_terminal_changed": False,
    }


def run_all() -> dict[str, object]:
    c=load_frozen_contract()
    g=c["synthetic_generator"]
    results=[run_world(c,i) for i in range(int(g["worlds"]))]
    n=sum(x["validation_individuals"] for x in results)
    same=sum(x["covered_same"] for x in results)/n
    drift=sum(x["covered_validation_shift"] for x in results)/n
    a=c["acceptance"]
    tests={
        "correct_independent_individual_count":n==a["expected_validation_groups_each_condition"]
            and all(x["training_individuals"]==80 and x["calibration_individuals"]==156
                    and x["validation_individuals"]==120 for x in results),
        "target_group_coverage_in_range":a["target_source_same_process_coverage_range"][0]<=same<=a["target_source_same_process_coverage_range"][1],
        "validation_only_shift_detected":drift<=a["target_validation_label_shift_coverage_max"],
        "training_fit_and_external_forecast_frozen":all(
            x["training_model_refitted_after_target_outcome"] is False
            and x["group_sampling_target_source_stable_within_calibration_validation"]
            and len(x["model_sha256"])==64
            and len(x["reference_sha256"])==64
            and len(x["calibration_sha256"])==64
            for x in results
        ),
        "no_original_RF_or_empirical_BOP_reclassification":all(
            x["original_bop_terminal_changed"] is False
            and x["target_identity_crosswalk_real_world_verified"] is False
            for x in results
        ),
    }
    return {
        "contract_id":c["id"],
        "contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "role":c["role"],"worlds":len(results),
        "validation_individual_groups_each_condition":n,
        "same_target_source_group_coverage":same,
        "shifted_validation_only_group_coverage":drift,
        "checks":tests,"passed":all(tests.values()),
        "original_BOP_terminal":"empirical_state_prediction_mixed",
        "original_RF_direct_external_transfer_admissible":False,
        "external_Dryad_candidate_admitted":False,
        "real_GPS_or_altitude_data_accessed":False,
        "full_world_audit":results,
    }


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    result=run_all()
    if args.out:
        if args.out.resolve()==CONTRACT.resolve():
            raise ValueError("cannot overwrite frozen contract")
        args.out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "passed":result["passed"],"worlds":result["worlds"],
        "groups":result["validation_individual_groups_each_condition"],
        "stable_coverage":result["same_target_source_group_coverage"],
        "validation_only_shift_coverage":result["shifted_validation_only_group_coverage"],
        "checks":result["checks"],
    },sort_keys=True))
    if not result["passed"]:
        raise SystemExit("Frozen common-feature transport benchmark NOT qualified")


if __name__=="__main__":
    main()
