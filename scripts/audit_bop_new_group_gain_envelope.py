#!/usr/bin/env python3
"""Read-only group-gain rank audit of the *closed* BOP_RODENT terminal receipt.

No GPS re-download, no model refit, no change of the frozen RF comparator or
the empirical_state_prediction_mixed terminal result. The archive's five-fold
scores are not claimed to be exchangeable with a future deployed predictor.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from odsp.new_group_gain_envelope import fit_new_group_gain_lower_envelope


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json"
EXPECTED_RESULT_SHA256 = "9e681852d1982e03d9a0696ce5b78c8f367bbffcc401bc54e9b62368a211499d"


def _checked_roster(receipt: dict) -> tuple[list[float], dict[str, list[float]]]:
    primary = receipt["primary_random_forest"]
    provenance = receipt["prospective_provenance"]
    if (
        receipt["contract_id"] != "bop-rodent-state-prediction-v1"
        or primary["terminal_category"] != "empirical_state_prediction_mixed"
        or provenance["result_json_sha256"] != EXPECTED_RESULT_SHA256
        or receipt["data_flow"]["eligible_individual_count"] != 30
        or primary["eligible_individual_count"] != 30
    ):
        raise ValueError("frozen BOP source provenance/admission/terminal mismatch")
    gains = [float(x) for x in primary["individual_gains"]]
    if len(gains) != 30 or not all(math.isfinite(x) for x in gains):
        raise ValueError("frozen BOP individual gain roster is incomplete")
    if (
        sum(x > 0.0 for x in gains) != 27
        or primary["positive_individual_count"] != 27
        or not math.isclose(
            math.fsum(gains) / 30,
            float(primary["mean_gain_descriptive"]),
            abs_tol=1e-12,
            rel_tol=0,
        )
    ):
        raise ValueError("frozen BOP primary RF summary mismatch")
    species_rows = primary["species_categories"]
    species = {
        name: [float(x) for x in row["gains"]]
        for name, row in species_rows.items()
    }
    if len(species) != 4 or sum(len(x) for x in species.values()) != 30:
        raise ValueError("frozen BOP species roster mismatch")
    if (
        sorted(x for subset in species.values() for x in subset) != sorted(gains)
        or sorted(species) != sorted(receipt["data_flow"]["admitted_species"])
    ):
        raise ValueError("frozen BOP species gains do not match the primary roster")
    for name, subset in species.items():
        if (
            len(subset) != species_rows[name]["individual_count"]
            or sum(x > 0 for x in subset) != species_rows[name]["positive_count"]
        ):
            raise ValueError("frozen BOP per-species summary mismatch")
    return gains, species


def _envelope(gains: list[float], *, alpha: float) -> dict[str, object]:
    # Receipt indices are ONLY de-identified unique position labels: the
    # frozen receipt does not expose individual IDs.
    ids = [f"receipt_group_position_{i:02d}" for i in range(len(gains))]
    result = fit_new_group_gain_lower_envelope(
        gains,
        ids,
        miscoverage=alpha,
        source_design="historical_crossfit_descriptive",
    )
    return result.as_dict()


def build_report(receipt_path: Path = RECEIPT) -> dict[str, object]:
    bytes_read = receipt_path.read_bytes()
    receipt = json.loads(bytes_read)
    gains, species = _checked_roster(receipt)
    return {
        "schema_version": 1,
        "method": "one_sided_independent_group_rank_lower_envelope",
        "evidence_role": "post_outcome_read_only_descriptive_method_demo",
        "source_receipt_path": RECEIPT.name,
        "source_receipt_sha256": hashlib.sha256(bytes_read).hexdigest(),
        "source_archived_result_sha256": EXPECTED_RESULT_SHA256,
        "frozen_terminal_category": "empirical_state_prediction_mixed",
        "frozen_positive_group_count": 27,
        "frozen_scored_group_count": 30,
        "model_refit_performed": False,
        "raw_gps_accessed": False,
        "original_terminal_reclassified": False,
        "score_role_warning": (
            "Original BOP groups were scored under different overlapping CV "
            "training folds, and the four species are heterogeneous; exchangeability "
            "with a future frozen deployed predictor is not established. All rank "
            "bounds below are DESCRIPTIVE, not 90%/95% coverage claims for BOP."
        ),
        "pooled_cross_species_descriptive": {
            "alpha_0_10": _envelope(gains, alpha=0.10),
            "alpha_0_05": _envelope(gains, alpha=0.05),
        },
        "within_species_descriptive": {
            name: {
                "alpha_0_10": _envelope(subset, alpha=0.10),
                "alpha_0_05": _envelope(subset, alpha=0.05),
            }
            for name, subset in sorted(species.items())
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, default=RECEIPT)
    parser.add_argument("--out", type=Path, help="Optional NEW report path")
    args = parser.parse_args()
    report = build_report(args.receipt)
    payload = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.out:
        if args.out.resolve() == RECEIPT.resolve():
            raise ValueError("cannot overwrite the frozen BOP receipt")
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
