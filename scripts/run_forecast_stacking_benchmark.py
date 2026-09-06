from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.forecast_stacking_benchmark import run_forecast_stacking_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("FORECAST_STACKING_BENCHMARK.json"),
    )
    args = parser.parse_args()
    result = run_forecast_stacking_benchmark()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not result["passed"]:
        raise SystemExit("forecast stacking benchmark failed")


if __name__ == "__main__":
    main()
