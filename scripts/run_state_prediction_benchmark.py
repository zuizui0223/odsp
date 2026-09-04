#!/usr/bin/env python3
"""Run and serialize the ODSP finite-sample state-prediction benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.state_prediction_benchmark import run_state_prediction_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/state_prediction_benchmark.json"),
    )
    parser.add_argument("--seed", type=int, default=20260904)
    parser.add_argument("--replicates", type=int, default=128)
    args = parser.parse_args()

    result = run_state_prediction_benchmark(
        seed=args.seed,
        replicates=args.replicates,
    )
    payload = result.as_dict()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
