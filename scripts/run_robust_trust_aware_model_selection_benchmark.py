from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.robust_trust_aware_model_selection_benchmark import (
    run_robust_trust_aware_model_selection_benchmark,
)


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    parser.add_argument("--seed",type=int,default=20260906)
    parser.add_argument("--bootstrap-draws",type=int,default=2000)
    args=parser.parse_args()
    result=run_robust_trust_aware_model_selection_benchmark(
        seed=args.seed,bootstrap_draws=args.bootstrap_draws
    )
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if not result["passed"]:
        raise SystemExit("robust trust-aware selection benchmark failed")


if __name__=="__main__":
    main()
