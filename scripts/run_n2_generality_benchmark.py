#!/usr/bin/env python3
"""Run the deterministic N2 generality benchmark and emit an audit receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.generality_benchmark import run_n2_generality_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260904)
    parser.add_argument("--randomized-cases", type=int, default=128)
    args = parser.parse_args()

    result = run_n2_generality_benchmark(
        seed=args.seed,
        randomized_cases=args.randomized_cases,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result.as_dict(), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "passed": result.passed,
                "check_count": result.check_count,
                "failed_count": result.failed_count,
                "maximum_absolute_error": result.maximum_absolute_error,
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    if not result.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
