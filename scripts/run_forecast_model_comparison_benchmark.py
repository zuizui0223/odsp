from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.forecast_model_comparison_benchmark import (
    run_forecast_model_comparison_benchmark,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=20260905)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_forecast_model_comparison_benchmark(seed=args.seed)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not result.passed:
        raise SystemExit("forecast model comparison benchmark failed")


if __name__ == "__main__":
    main()
