from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.block_aware_transfer_uncertainty_benchmark import (
    run_block_aware_transfer_uncertainty_benchmark,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=20260906)
    parser.add_argument("--bootstrap-draws", type=int, default=2000)
    parser.add_argument("--confidence-level", type=float, default=0.95)
    args = parser.parse_args()

    result = run_block_aware_transfer_uncertainty_benchmark(
        seed=args.seed,
        bootstrap_draws=args.bootstrap_draws,
        confidence_level=args.confidence_level,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not result["passed"]:
        raise SystemExit("block-aware transfer uncertainty benchmark failed")


if __name__ == "__main__":
    main()
