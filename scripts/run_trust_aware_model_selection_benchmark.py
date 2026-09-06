from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.trust_aware_model_selection_benchmark import run_trust_aware_model_selection_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("TRUST_AWARE_MODEL_SELECTION_BENCHMARK.json"))
    args = parser.parse_args()
    result = run_trust_aware_model_selection_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not result["passed"]:
        raise SystemExit("trust-aware model selection benchmark failed")


if __name__ == "__main__":
    main()
