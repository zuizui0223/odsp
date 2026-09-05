#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.circular_state_benchmark import run_circular_state_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/CIRCULAR_STATE_BENCHMARK.json"))
    parser.add_argument("--seed", type=int, default=20260905)
    parser.add_argument("--replicates", type=int, default=128)
    parser.add_argument("--training-rows", type=int, default=800)
    parser.add_argument("--heldout-rows", type=int, default=1600)
    parser.add_argument("--period", type=float, default=24.0)
    args = parser.parse_args()

    result = run_circular_state_benchmark(
        seed=args.seed,
        replicates=args.replicates,
        training_rows=args.training_rows,
        heldout_rows=args.heldout_rows,
        period=args.period,
    ).as_dict()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
