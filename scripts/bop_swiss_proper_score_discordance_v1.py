#!/usr/bin/env python3
"""Offline Brier-versus-log-score audit of 12 pinned Swiss ranger aggregates.

No biological source RDS, individual rows, bird IDs, model scores, R, or network.
This is an exploratory post-result diagnostic, NOT a new external validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/BOP_SWISS_PROPER_SCORE_DISCORDANCE_V1_CONTRACT.json"
SOURCE = ROOT / "BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_FIRST_RECEIPT.json"
RANK = ROOT / "BOP_SWISS_2022_RANK_RESOLUTION_V1_FIRST_RECEIPT.json"
CONTRACT_BLOB = "0b89080c589faed62c599d7d6877fd5bf639bf12"
SOURCE_BLOB = "82c328cc5bd5b88afa2faf8f0121d607af1a4e72"
RANK_BLOB = "9896eb070a208b06b7d763b5a6e806a797e0fb37"


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def load_locked() -> tuple[dict, dict, dict]:
    """Fail closed if prior receipts or the frozen exploratory replay contract change."""
    paths = (CONTRACT, SOURCE, RANK)
    expected = (CONTRACT_BLOB, SOURCE_BLOB, RANK_BLOB)
    raw = [p.read_bytes() for p in paths]
    if any(git_blob_sha1(data) != digest for data, digest in zip(raw, expected)):
        raise ValueError("PINNED_AGGREGATE_OR_CONTRACT_BLOB_DRIFT")
    c, s, r = (json.loads(x) for x in raw)
    src = c["source"]
    if (
        c.get("contract_id") != "bop-swiss-fixed-aggregate-proper-score-discordance-v1"
        or c.get("freeze_date") != "2026-11-20"
        or src["expected_source_receipt_git_blob_sha1"] != SOURCE_BLOB
        or src["expected_rank_receipt_git_blob_sha1"] != RANK_BLOB
        or src["original_first_actions_run"] != 44746545177
        or src["original_first_artifact_id"] != 14633317139
        or not all(src[x] is True for x in (
            "no_original_prepared_RDS_or_GPS_access",
            "no_source_HR_or_nest_labels_reaccess",
            "no_animal_ID_or_individual_probabilities",
            "no_forest_refit_or_hyperparameter_selection"
        ))
        or s.get("receipt_id") != "bop-swiss-temporal-bird-purge-original-first-v1"
        or s["first_actions"]["run_id"] != 44746545177
        or s["first_actions"]["artifact_id"] != 14633317139
        or r.get("receipt_id") != "bop-swiss-2022-four-negative-exact-rank-reference-first-v1"
        or r["original_source_unchanged"]["original_receipt_git_blob_sha1"] != SOURCE_BLOB
    ):
        raise ValueError("SOURCE_FREE_ORIGINAL_RECEIPT_GATE_FAILED")
    return c, s, r


def signed(x: float, atol: float = 0.000001) -> int:
    return (x > atol) - (x < -atol)


def analyze(c: dict, source: dict, rank: dict) -> dict:
    spec, claims = c["analysis"], c["claims"]
    cutoffs, targets, modes = (
        spec["all_fixed_cutoffs"],
        spec["all_fixed_targets"],
        spec["all_fixed_training_modes"],
    )
    if (
        cutoffs != [2020, 2021, 2022]
        or targets != ["HR", "nest"]
        or modes != ["full_forward", "bird_purged_forward"]
        or spec["n_required_aggregate_cells"] != 12
        or not all(spec[x] is True for x in (
            "compare_binary_signs_for_each_cell",
            "use_training_only_reference_probability_q",
            "test_label_aggregate_prevalence_only_for_offline_scoring",
            "report_all_cells_no_posthoc_subsetting",
            "preknown_anomaly_is_exploratory_not_confirmatory",
        ))
        or claims["historical_BOP"] != "empirical_state_prediction_mixed"
        or claims["redkite_external"] != "HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or claims["original_Dryad"] != "NOT_ADMITTED"
        or not all(claims[x] is True for x in (
            "point_estimates_only", "no_calibration_or_probability_tail_mechanism_identified_from_aggregate_means",
            "no_per_seed_or_between_year_independent_replication_claim",
            "no_ecological_2022_regime_shift_claim",
            "no_future_animal_exchangeability_or_coverage_certificate",
        ))
        or source["first_models"]["original_models_scored"] != 96
        or source["first_models"]["held_panels"] != 0
        or source["first_models"]["predeclared_cutoffs"] != cutoffs
        or source["scientific_ceiling"]["source_HR_nest_outcomes_previously_accessed_not_untouched_validation"] is not True
        or source["scientific_ceiling"]["bird_purged_train_test_bird_ID_overlap_zero_at_all_cutoffs"] is not True
    ):
        raise ValueError("CLAIM_SCOPE_OR_INPUT_DESIGN_DRIFT")

    raw = source["first_models"]["all_twelve_cell_means"]
    if len(raw) != 12:
        raise ValueError("EXPECTED_ALL_TWELVE_CELLS")
    rank_rows = rank["fixed_reference"]["all_twelve_original_accuracy_vs_test_majority_oracle"]
    indexed_rank = {(row[0], row[1], row[2]): row for row in rank_rows}
    if len(indexed_rank) != 12 or len(rank_rows) != 12:
        raise ValueError("ORIGINAL_RANK_AUDIT_CELLS_DRIFT")
    expected_keys = {(year, target, mode) for year in cutoffs for target in targets for mode in modes}
    seen = set()
    out = []
    prevalence_by_cutoff_target = {}
    eps = spec["max_log_identity_disagreement_due_to_rounding"]
    if not (0 < eps <= 0.00001):
        raise ValueError("ROUNDING_TOLERANCE_DRIFT")

    for row in raw:
        if len(row) != 12:
            raise ValueError("ORIGINAL_METRIC_COLUMNS_DRIFT")
        year, target, mode, acc, brier, loss, log_gain, auc, amin, amax, pi, q = row
        key = (year, target, mode)
        if key not in expected_keys or key in seen:
            raise ValueError("DUPLICATE_OR_UNEXPECTED_CELL")
        seen.add(key)
        numbers = (acc, brier, loss, log_gain, auc, amin, amax, pi, q)
        if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in numbers):
            raise ValueError("NONFINITE_SOURCE_AGGREGATE")
        if not (0 < pi < 1 and 0 < q < 1 and 0 <= acc <= 1 and 0 <= brier <= 1
                and loss >= 0 and 0 <= amin <= auc <= amax <= 1):
            raise ValueError("INVALID_PROBABILITY_OR_SCORE")
        previous = indexed_rank[key]
        if abs(previous[3] - acc) > 0.0000001:
            raise ValueError("RANK_RECEIPT_ACCURACY_DISAGREEMENT")
        if abs(previous[4] - max(pi, 1 - pi)) > 0.000002:
            raise ValueError("TEST_MAJORITY_ORACLE_INCONSISTENT")
        pt = (year, target)
        if pt in prevalence_by_cutoff_target and abs(prevalence_by_cutoff_target[pt] - pi) > 0.000002:
            raise ValueError("DIFFERENT_TEST_ROWS_ACROSS_TRAINING_MODES")
        prevalence_by_cutoff_target[pt] = pi

        # q is the original train-only prevalence; pi is the already published
        # test prevalence used only to evaluate that fixed constant forecast.
        ref_brier = pi * (1.0 - q) ** 2 + (1.0 - pi) * q**2
        ref_logloss = -(pi * math.log(q) + (1.0 - pi) * math.log1p(-q))
        reconstructed_log_gain = ref_logloss - loss
        if abs(reconstructed_log_gain - log_gain) > eps:
            raise ValueError("LOG_SCORE_GAIN_IDENTITY_FAILED")
        brier_gain = ref_brier - brier
        sign_brier = signed(brier_gain)
        sign_log = signed(log_gain)
        out.append({
            "cutoff": year,
            "target": target,
            "mode": mode,
            "test_positive_fraction": round(pi, 6),
            "train_only_reference_positive_fraction": round(q, 6),
            "source_test_accuracy_mean": round(acc, 6),
            "source_test_auc_mean": round(auc, 6),
            "model_brier": round(brier, 6),
            "training_prevalence_reference_brier": round(ref_brier, 6),
            "brier_gain_vs_training_reference": round(brier_gain, 6),
            "source_model_log_loss": round(loss, 6),
            "training_prevalence_reference_log_loss": round(ref_logloss, 6),
            "source_log_score_gain_vs_training_reference": round(log_gain, 6),
            "recomputed_log_gain_rounding_difference": round(reconstructed_log_gain - log_gain, 8),
            "proper_score_sign_disagreement": sign_brier * sign_log == -1,
        })
    if seen != expected_keys:
        raise ValueError("MISSING_FROZEN_CELLS")
    disagreements = [{k: z[k] for k in ("cutoff", "target", "mode", "brier_gain_vs_training_reference", "source_log_score_gain_vs_training_reference")}
                     for z in out if z["proper_score_sign_disagreement"]]
    return {
        "status": "EXPLORATORY_FIXED_AGGREGATE_PROPER_SCORE_AUDIT",
        "contract_freeze_commit": "b4e5cc679abd026a6748c62940efabd17defea5b",
        "locked_source_first_actions_run": 44746545177,
        "locked_source_first_artifact_id": 14633317139,
        "locked_source_receipt_git_blob_sha1": SOURCE_BLOB,
        "locked_rank_receipt_git_blob_sha1": RANK_BLOB,
        "n_source_models": 96,
        "n_frozen_cells": len(out),
        "n_opposite_sign_cells": len(disagreements),
        "opposite_sign_cells": disagreements,
        "all_frozen_cells": out,
        "interpretation": "Both scores are proper; the numerical Brier-versus-log sign disagreement is not proof of any specific per-row probability-tail mechanism, ecological shift or new future-animal transfer.",
        "no_source_RDS_labels_IDs_probabilities_or_model_refit": True,
        "original_BOP": "empirical_state_prediction_mixed",
        "redkite_external": "HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "original_Dryad": "NOT_ADMITTED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Optional source-free aggregate-only JSON output")
    args = parser.parse_args()
    if args.out:
        output = args.out.resolve()
        if any(output == path.resolve() or (output.exists() and output.samefile(path))
               for path in (CONTRACT, SOURCE, RANK)):
            raise ValueError("cannot overwrite immutable contract or source receipts")
    report = analyze(*load_locked())
    report_text = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(report_text, encoding="utf-8")
    else:
        print(report_text, end="")


if __name__ == "__main__":
    main()
