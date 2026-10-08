#!/usr/bin/env python3
"""Outcome-free structural eligibility audit of four *closed* ecological lanes.

Only pre-outcome CONTRACT files and terminal FILE EXISTENCE are inspected:
never open an outcome receipt or score file. A historical terminal endpoint
can be ecologically informative while remaining NOT a prospective validation
sample for the new future-refit success-probability route.

No source data are downloaded, no source result is rerun, no retuning occurs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _contract(root: Path, filename: str) -> tuple[dict, str]:
    path = root / filename
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"invalid contract object: {filename}")
    return data, hashlib.sha256(raw).hexdigest()


def _closed(root: Path, filename: str) -> bool:
    # Existence only; never read a post-outcome result.
    return (root / filename).is_file()


def audit_closed_ecological_lanes(root: Path = ROOT) -> dict[str, object]:
    se, sh = _contract(root, "N2_TEMPORAL_PARTITION_CONTRACT.json")
    bop, bh = _contract(root, "BOP_RODENT_STATE_PREDICTION_CONTRACT.json")
    bat, th = _contract(root, "N2_BAT_THICKNESS_CONTRACT.json")
    taw, tw = _contract(root, "GATE_D_TAWAKI_CONTRACT.json")

    if (
        se["frozen_preprocessing"]["site_fold_rule"] != "sha256(SiteID) integer modulo 3"
        or "log P_model(T|C)-log P_model(T)" not in
            se["primary_estimands"]["heldout_transferability"]
    ):
        raise ValueError("Serengeti frozen one-contrast/fold identity changed")
    if (
        bop["independence_and_admission"]["scoring_unit"]
            != "each held-out individual scored separately even when multiple individuals share a fold"
        or bop["independence_and_admission"]["cross_validation"]
            != "five deterministic individual-group folds"
        or bop["heldout_metrics"]["primary"]
            != "mean_log_score_gain_over_training_marginal_per_individual"
    ):
        raise ValueError("BOP_RODENT frozen individual-score contract changed")
    if (
        bat["whole_individual_split"]["expected_structural_counts"]["sealed"] != 2
        or "log P_model(z|x,y) - log P_model(z)" not in
            bat["sealed_answer_check"]["event_metric"]
    ):
        raise ValueError("Tadarida sealed identity/one-contrast contract changed")
    if (
        taw["weighting"]["unit"] != "bird-trip"
        or taw["sealed_answer_check"]["primary_metric"]
            != "mean held-out log-score difference"
    ):
        raise ValueError("Tawaki frozen event and scoring contract changed")

    # Do not treat folds, rows, events or timestamps as iid validation BLOCKS.
    # Their population sampling law was not frozen for this new route.
    records = [
        {
            "lane": "Snapshot_Serengeti_temporal_partition",
            "contract": "N2_TEMPORAL_PARTITION_CONTRACT.json",
            "contract_sha256": sh,
            "terminal_exists": _closed(root,"N2_SERENGETI_TEMPORAL_TERMINAL_DECISION.json"),
            "original_comparison_count": 1,
            "original_independent_unit": "camera_site",
            "heldout_fold_count": 3,
            "eligible_iid_blocks_per_group": None,
            "already_outcome_opened": True,
            "non_admission_reasons": [
                "historical_endpoint_already_opened",
                "one_original_comparison_not_two",
                "no_frozen_iid_training_refit_process",
                "iid_camera_site_sampling_not_established",
                "original_log_score_difference_not_process_wide_bounded",
            ],
        },
        {
            "lane": "BOP_RODENT_absolute_altitude_prediction",
            "contract": "BOP_RODENT_STATE_PREDICTION_CONTRACT.json",
            "contract_sha256": bh,
            "terminal_exists": _closed(root,"BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json"),
            "original_comparison_count": 1,
            "original_independent_unit": "tagged_individual",
            "heldout_fold_count": 5,
            "eligible_iid_blocks_per_group": None,
            "already_outcome_opened": True,
            "non_admission_reasons": [
                "historical_endpoint_already_opened",
                "one_original_comparison_not_two",
                "no_frozen_iid_training_refit_process",
                "repeated_hourly_locations_not_independent_individuals",
                "original_log_score_difference_not_process_wide_bounded",
            ],
        },
        {
            "lane": "Tadarida_teniotis_vertical_niche",
            "contract": "N2_BAT_THICKNESS_CONTRACT.json",
            "contract_sha256": th,
            "terminal_exists": _closed(root,"N2_BAT_THICKNESS_TERMINAL_DECISION.json"),
            "original_comparison_count": 1,
            "original_independent_unit": "tagged_bat",
            "sealed_individual_count": 2,
            "eligible_iid_blocks_per_group": None,
            "already_outcome_opened": True,
            "non_admission_reasons": [
                "historical_endpoint_already_opened",
                "one_original_comparison_not_two",
                "only_two_sealed_bats",
                "no_frozen_iid_training_refit_process",
                "original_log_score_difference_not_process_wide_bounded",
            ],
        },
        {
            "lane": "Tawaki_dive_depth",
            "contract": "GATE_D_TAWAKI_CONTRACT.json",
            "contract_sha256": tw,
            "terminal_exists": _closed(root,"GATE_D_TAWAKI_TERMINAL_RECEIPT.json"),
            "original_comparison_count": 1,
            "original_independent_unit": "bird_or_trip_depending_on_estimand",
            "eligible_iid_blocks_per_group": None,
            "already_outcome_opened": True,
            "non_admission_reasons": [
                "historical_endpoint_already_opened",
                "one_original_comparison_not_two",
                "historical_site_year_coverage_gate_failed",
                "no_frozen_iid_training_refit_process",
                "original_log_score_difference_not_process_wide_bounded",
            ],
        },
    ]
    if not all(row["terminal_exists"] for row in records):
        raise ValueError("expected closed terminal marker missing; no admission audit asserted")
    return {
        "schema_version": 0,
        "audit_kind": "outcome_free_contract_structure_only",
        "outcomes_read": False,
        "terminal_receipt_content_read": False,
        "raw_public_data_downloaded": False,
        "prior_empirical_terminal_categories_reclassified": False,
        "qualified_future_refit_ecological_endpoints": 0,
        "existing_lanes_audited": len(records),
        "route_tested": "future_refit_shared_validation_evalue_v0",
        "admission_status": "NO_EXISTING_CLOSED_ENDPOINT_ADMISSIBLE_AS_NEW_UNTOUCHED_VALIDATION",
        "records": records,
        "correct_next_step": (
            "Freeze a NEW outcome-blind three-level categorical prediction "
            "roster, full original training source frame, iid process refit "
            "schedule, validation independent-block sampling law, normalized "
            "Brier score scale, and managed model-to-score provenance before "
            "opening any NEW external outcomes."
        ),
    }


def main() -> int:
    print(json.dumps(audit_closed_ecological_lanes(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
