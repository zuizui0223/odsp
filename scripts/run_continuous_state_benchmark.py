#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.continuous_state_benchmark import run_continuous_state_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/CONTINUOUS_STATE_BENCHMARK.json"))
    parser.add_argument("--seed", type=int, default=20260905)
    parser.add_argument("--replicates", type=int, default=128)
    args = parser.parse_args()
    result = run_continuous_state_benchmark(
        seed=args.seed,
        replicates=args.replicates,
        training_rows=800,
        heldout_rows=1600,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result.as_dict(), sort_keys=True))
    if not result.passed:
        raise SystemExit("continuous state benchmark failed")


if __name__ == "__main__":
    main()
