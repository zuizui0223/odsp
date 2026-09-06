from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.joint_robustness_radius_benchmark import run_joint_robustness_radius_benchmark


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    parser.add_argument("--seed",type=int,default=20260906)
    parser.add_argument("--bootstrap-draws",type=int,default=500)
    args=parser.parse_args()
    result=run_joint_robustness_radius_benchmark(
        seed=args.seed,bootstrap_draws=args.bootstrap_draws
    )
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if not result["passed"]:
        raise SystemExit("joint robustness radius benchmark failed")


if __name__=="__main__":
    main()
