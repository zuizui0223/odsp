#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.evaluation_access_checkpoints_benchmark import run_evaluation_access_checkpoints_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=20260911)
    args = parser.parse_args()

    result = run_evaluation_access_checkpoints_benchmark(seed=args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
