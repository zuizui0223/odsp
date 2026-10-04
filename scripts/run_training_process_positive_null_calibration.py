"""Run the frozen training-process positive-transfer null calibration."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from odsp.training_process_positive_calibration import (
    run_training_process_positive_null_calibration,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261005)
    parser.add_argument("--simulations", type=int, default=1000)
    parser.add_argument("--bootstrap-draws", type=int, default=500)
    args = parser.parse_args()

    result = run_training_process_positive_null_calibration(
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
                "scenario_count": len(result.scenarios),
                "rates": {
                    row.scenario_id: row.one_sided_familywise_false_positive_rate
                    for row in result.scenarios
                },
            },
            sort_keys=True,
        )
    )
    if not result.qualification_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
