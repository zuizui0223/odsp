"""Run the frozen v3 centered-pigeonhole component null panel."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from odsp.training_process_positive_pigeonhole_iut_calibration import (
    run_training_process_positive_pigeonhole_iut_v3_null_calibration,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--simulations", type=int, default=1000)
    parser.add_argument("--bootstrap-draws", type=int, default=500)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    result = run_training_process_positive_pigeonhole_iut_v3_null_calibration(
        seed=args.seed,
        simulations_per_scenario=args.simulations,
        bootstrap_draws=args.bootstrap_draws,
    )
    payload = result.as_dict()
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "qualification_pass": result.qualification_pass,
                "max_component_rates": {
                    row.scenario_id: row.maximum_component_false_positive_rate
                    for row in result.scenarios
                },
            },
            sort_keys=True,
        )
    )
    if args.require_pass and not result.qualification_pass: raise SystemExit(1)


if __name__ == "__main__":
    main()
