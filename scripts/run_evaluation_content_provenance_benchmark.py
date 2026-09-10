#!/usr/bin/env python3
"""Run the frozen evaluation-content provenance benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.evaluation_content_provenance_benchmark import run_evaluation_content_provenance_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_evaluation_content_provenance_benchmark(seed=20260910)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
