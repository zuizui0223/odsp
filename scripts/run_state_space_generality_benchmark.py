#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.state_space_generality_benchmark import run_state_space_generality_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/state_space_generality/N2_STATE_SPACE_GENERALITY_BENCHMARK_SUMMARY.json"),
    )
    args = parser.parse_args()
    result = run_state_space_generality_benchmark()
    if not result.passed:
        failed = [check.as_dict() for check in result.checks if not check.passed]
        raise SystemExit("state-space generality benchmark failed: " + json.dumps(failed, sort_keys=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result.as_dict(), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result.as_dict(), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
