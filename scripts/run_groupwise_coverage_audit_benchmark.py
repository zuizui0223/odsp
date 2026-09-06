from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.groupwise_coverage_audit_benchmark import run_groupwise_coverage_audit_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("GROUPWISE_COVERAGE_AUDIT_BENCHMARK.json"))
    args = parser.parse_args()
    result = run_groupwise_coverage_audit_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not result["passed"]:
        raise SystemExit("group-wise coverage audit benchmark failed")


if __name__ == "__main__":
    main()
