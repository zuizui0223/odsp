#!/usr/bin/env python3
"""Run the frozen aligned refit-scheme sensitivity benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.aligned_refit_scheme_sensitivity_benchmark import (
    run_aligned_refit_scheme_sensitivity_benchmark,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--nested-draws", type=int, default=1200)
    args = parser.parse_args()
    result = run_aligned_refit_scheme_sensitivity_benchmark(nested_draws=args.nested_draws)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
