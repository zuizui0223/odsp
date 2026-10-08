"""Run the frozen future-refit success-probability v1 qualification panel."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from odsp.training_process_future_refit_success_probability_calibration import (
    run_future_refit_success_probability_v1_calibration,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261016)
    parser.add_argument("--simulations", type=int, default=1000)
    parser.add_argument("--bootstrap-draws", type=int, default=500)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    result = run_future_refit_success_probability_v1_calibration(
        seed=args.seed,
        simulations_per_scenario=args.simulations,
        bootstrap_draws=args.bootstrap_draws,
    )
    payload = result.as_dict()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "qualification_pass": result.qualification_pass,
                "coverage": {
                    row.scenario_id: {
                        "overall_overclaim_rate": row.overall_overclaim_rate,
                        "validation_overcertification_rate": (
                            row.validation_overcertification_rate
                        ),
                        "acceptance_pass": row.acceptance_pass,
                    }
                    for row in result.coverage_scenarios
                },
                "power": {
                    row.scenario_id: {
                        "all_refits_certified_power": (
                            row.all_refits_certified_power
                        ),
                        "acceptance_pass": row.acceptance_pass,
                    }
                    for row in result.power_scenarios
                },
            },
            sort_keys=True,
        )
    )
    if args.require_pass and not result.qualification_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
