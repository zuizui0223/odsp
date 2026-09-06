#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.forecast_assessment_benchmark import run_forecast_assessment_benchmark


def main() -> int:
    parser=argparse.ArgumentParser(description="Run the frozen one-call forecast assessment benchmark")
    parser.add_argument("--output",required=True)
    parser.add_argument("--seed",type=int,default=20260906)
    parser.add_argument("--bootstrap-draws",type=int,default=500)
    args=parser.parse_args()
    result=run_forecast_assessment_benchmark(seed=args.seed,bootstrap_draws=args.bootstrap_draws)
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
    return 0 if result["passed"] else 1


if __name__=="__main__":
    raise SystemExit(main())
