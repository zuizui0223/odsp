#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.trusted_joint_forecast_benchmark import run_trusted_joint_forecast_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/TRUSTED_JOINT_FORECAST_BENCHMARK.json"),
    )
    parser.add_argument("--seed", type=int, default=20260905)
    parser.add_argument("--training-rows", type=int, default=1200)
    parser.add_argument("--calibration-rows", type=int, default=1200)
    parser.add_argument("--test-rows", type=int, default=3000)
    args = parser.parse_args()

    result = run_trusted_joint_forecast_benchmark(
        seed=args.seed,
        training_rows=args.training_rows,
        calibration_rows=args.calibration_rows,
        test_rows=args.test_rows,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result.as_dict(), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result.as_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
