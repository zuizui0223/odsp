#!/usr/bin/env python3
"""Deterministic error-probability bounds from pinned aggregate scores only.

The unit is an equally weighted model-record prediction, not an independent
animal. No source data, individual predictions, R execution or forest refits.
"""
from __future__ import annotations

import argparse
from decimal import (
    Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN,
    localcontext,
)
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = "research/BOP_SWISS_ERROR_PROBABILITY_BOUNDS_V1_CONTRACT.json"
CONTRACT_BLOB = "903ce8f1998a5a1e55b3bb4b891475602601197c"
SPECIFICATION_COMMIT = "ebb5931a687569299e0a353e9b856e485a03317d"


def _decimal(value: object, name: str) -> Decimal:
    try:
        if isinstance(value, bool):
            raise ValueError(name)
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"invalid {name}") from error
    if not result.is_finite():
        raise ValueError(f"nonfinite {name}")
    return result


def _display(value: Decimal, direction: str) -> str:
    """Serialize an inequality outward, without a binary-float conversion."""
    return format(value.quantize(Decimal("1e-12"), rounding=direction), "f")


def binary_error_bounds(
    accuracy: object,
    log_loss: object,
    n_predictions: int,
    *,
    rounding_radius: object = "0.000001000001",
    clip_floor: object = "0.000000999999",
    probability_threshold: object = "0.01",
) -> dict:
    """Bound errors for an equally weighted binary score with a .5 class cut.

    The accuracy interval must identify one integer number of correct
    predictions. `rounding_radius` bounds error in each supplied aggregate;
    `clip_floor` bounds every scored true-class probability from below and its
    complement from below. Both assumptions belong to the caller's scorer.
    Conditional error bounds are undefined (None) when there are no errors.
    All probability claims concern clipped probabilities and pooled errors.
    """
    if isinstance(n_predictions, bool) or not isinstance(n_predictions, int) or n_predictions <= 0:
        raise ValueError("n_predictions must be a positive integer")
    a = _decimal(accuracy, "accuracy")
    loss = _decimal(log_loss, "log_loss")
    radius = _decimal(rounding_radius, "rounding_radius")
    epsilon = _decimal(clip_floor, "clip_floor")
    tau = _decimal(probability_threshold, "probability_threshold")
    if not (0 <= a <= 1 and loss >= 0 and radius >= 0 and 0 < epsilon < tau <= Decimal("0.5")):
        raise ValueError("invalid binary score domain")

    with localcontext() as context:
        # Retain input decimals/counts exactly before directed arithmetic.
        input_digits = max(len(x.as_tuple().digits) for x in (a, loss, radius, epsilon, tau))
        context.prec = max(80, len(str(n_predictions)) + input_digits + 30, -epsilon.adjusted() + 40)
        n = Decimal(n_predictions)
        context.rounding = ROUND_FLOOR
        a_low, loss_low = max(Decimal(0), a - radius), max(Decimal(0), loss - radius)
        first_count = int((n * a_low).to_integral_value(rounding=ROUND_CEILING))
        context.rounding = ROUND_CEILING
        a_high, loss_high = min(Decimal(1), a + radius), loss + radius
        last_count = int((n * a_high).to_integral_value(rounding=ROUND_FLOOR))
        if first_count != last_count:
            raise ValueError("accuracy does not identify a unique integer_correct_count")
        k = Decimal(first_count)
        errors = n - k

        # Decimal ln/exp are correctly rounded. Adjacent representable values
        # enclose each transcendental result; subsequent arithmetic is directed.
        context.rounding = ROUND_HALF_EVEN
        b = Decimal(2).ln()
        b_low, b_high = b.next_minus(), b.next_plus()
        log_epsilon, log_tau = epsilon.ln(), tau.ln()
        cap_high = -log_epsilon.next_minus()
        threshold_low, threshold_high = -log_tau.next_plus(), -log_tau.next_minus()
        log_complement = (Decimal(1) - epsilon).ln()
        minimum_low = -log_complement.next_plus()

        context.rounding = ROUND_FLOOR
        feasible_low = (k * minimum_low + errors * b_low) / n
        context.rounding = ROUND_CEILING
        feasible_high = (k * b_high + errors * cap_high) / n
        if loss_high < feasible_low or loss_low > feasible_high:
            raise ValueError("log_loss incompatible with accuracy and probability clipping")

        result = {
            "n_predictions": n_predictions,
            "n_correct": first_count,
            "n_errors": int(errors),
            "error_predictions_exist": bool(errors),
            "input_accuracy": str(a),
            "input_log_loss": str(loss),
            "rounding_radius": str(radius),
            "clip_floor": str(epsilon),
            "probability_threshold": str(tau),
            "log_loss_interval": [_display(loss_low, ROUND_FLOOR), _display(loss_high, ROUND_CEILING)],
            "error_mean_log_loss_lower_bound": None,
            "error_geometric_mean_true_probability_upper_bound": None,
            "at_least_one_error_true_probability_upper_bound": None,
            "min_predictions_below_threshold": 0,
        }
        if not errors:
            return result

        context.rounding = ROUND_CEILING
        correct_loss_cap = k * b_high
        no_tail_loss_cap = correct_loss_cap + errors * threshold_high
        tail_extra_cap = cap_high - threshold_low
        context.rounding = ROUND_FLOOR
        mean_error_low = max(b_low, (n * loss_low - correct_loss_cap) / errors)
        tail_count_low = max(Decimal(0), (n * loss_low - no_tail_loss_cap) / tail_extra_cap)
        minimum_count = int(tail_count_low.to_integral_value(rounding=ROUND_CEILING))
        probability_high = min(Decimal("0.5"), (-mean_error_low).exp().next_plus())

        result.update({
            "error_mean_log_loss_lower_bound": _display(mean_error_low, ROUND_FLOOR),
            "error_geometric_mean_true_probability_upper_bound": _display(probability_high, ROUND_CEILING),
            "at_least_one_error_true_probability_upper_bound": _display(probability_high, ROUND_CEILING),
            "min_predictions_below_threshold": min(int(errors), minimum_count),
        })
        return result


def _read_pinned(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if actual != expected:
        raise ValueError(f"PINNED_INPUT_DRIFT: {path.name}")
    return raw


def _contract() -> dict:
    return json.loads(_read_pinned(ROOT / CONTRACT_PATH, CONTRACT_BLOB))


def protected_paths() -> tuple[Path, ...]:
    contract = _contract()
    return tuple(ROOT / path for path in contract["input_git_blob_sha1"]) + (
        ROOT / CONTRACT_PATH, Path(__file__).resolve(),
    )


def replay() -> dict:
    """Apply the proof to every already-inspected, hash-locked source cell."""
    contract = _contract()
    raw = {path: _read_pinned(ROOT / path, digest)
           for path, digest in contract["input_git_blob_sha1"].items()}
    source = json.loads(raw["BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_FIRST_RECEIPT.json"])
    rank = json.loads(raw["BOP_SWISS_2022_RANK_RESOLUTION_V1_FIRST_RECEIPT.json"])
    previous_contract = json.loads(raw["research/BOP_SWISS_PROPER_SCORE_DISCORDANCE_V1_CONTRACT.json"])
    design = json.loads(raw["research/BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_CONTRACT.json"])
    # Import only after its exact bytes, and all data it will consume, are checked.
    from scripts import bop_swiss_proper_score_discordance_v1 as previous

    previous.analyze(previous_contract, source, rank)
    spec = contract["analysis"]
    cohorts = {row["cutoff"]: row for row in source["cohort_by_fixed_cutoff"]}
    seeds = source["first_models"]["frozen_model_seeds"]
    if (
        len(source["cohort_by_fixed_cutoff"]) != 3
        or set(cohorts) != set(spec["cutoffs"])
        or seeds != spec["seeds"]
        or len(seeds) != 8 or len(set(seeds)) != 8
        or design["model"]["random_model_seeds"] != seeds
        or design["model"]["all_original_realized_test_row_sets_same_across_model_seeds_per_cutoff"] is not True
        or source["scientific_ceiling"]["same_8_model_seeds_and_test_rows_not_8_independent_populations"] is not True
        or source["scientific_ceiling"]["identical_test_rows_purged_and_full_train_per_cutoff"] is not True
        or any(row["test_rows"] != spec["test_rows_by_cutoff"][str(year)]
               or row["test_birds"] != spec["test_source_bird_ID_strings_by_cutoff"][str(year)]
               for year, row in cohorts.items())
    ):
        raise ValueError("POOLED_PREDICTION_DENOMINATOR_NOT_IDENTIFIED")

    cells = []
    for row in source["first_models"]["all_twelve_cell_means"]:
        cutoff, target, mode = row[:3]
        cohort = cohorts[cutoff]
        bounds = binary_error_bounds(
            row[3], row[5], cohort["test_rows"] * len(seeds),
            rounding_radius=spec["rounding_radius"],
            clip_floor=spec["conservative_true_class_probability_floor"],
            probability_threshold=spec["probability_threshold"],
        )
        cells.append({
            "cutoff": cutoff, "target": target, "mode": mode,
            "test_season_rows": cohort["test_rows"],
            "source_bird_ID_strings": cohort["test_birds"],
            "seed_models": len(seeds), **bounds,
        })
    if len(cells) != spec["n_cells"]:
        raise ValueError("MISSING_FROZEN_CELLS")
    return {
        "schema_version": 1,
        "status": "EXPLORATORY_AGGREGATE_ERROR_PROBABILITY_BOUNDS",
        "specification_commit": SPECIFICATION_COMMIT,
        "contract_git_blob_sha1": CONTRACT_BLOB,
        "input_git_blob_sha1": contract["input_git_blob_sha1"],
        "scoring_unit": spec["unit"],
        "n_cells": len(cells), "all_cells": cells,
        "errors_are_not_independent_animals": True,
        "no_individual_probability_values_accessed": True,
        "no_per_seed_or_error_identity_claim": True,
        "original_BOP": contract["claims"]["original_BOP"],
        "redkite_external": contract["claims"]["redkite_external"],
        "original_Dryad": contract["claims"]["original_Dryad"],
        "interpretation": "Deterministic implications of rounded, already inspected aggregate metrics; no calibration mechanism, ecological cause, independent replication or future-animal coverage established.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Optional aggregate-only JSON output")
    args = parser.parse_args()
    if args.out:
        output = args.out.resolve()
        if any(output == path.resolve() or (output.exists() and output.samefile(path))
               for path in protected_paths()):
            raise ValueError("cannot overwrite immutable input or executable")
    content = json.dumps(replay(), sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.write_text(content, encoding="utf-8")
    else:
        print(content, end="")


if __name__ == "__main__":
    main()
