#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.prediction_trust_benchmark import run_prediction_trust_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/PREDICTION_TRUST_BENCHMARK.json"))
    parser.add_argument("--seed", type=int, default=20260905)
    args = parser.parse_args()
    result = run_prediction_trust_benchmark(seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result.as_dict(), sort_keys=True))
    if not result.passed:
        raise SystemExit("prediction trust benchmark failed")


if __name__ == "__main__":
    main()
