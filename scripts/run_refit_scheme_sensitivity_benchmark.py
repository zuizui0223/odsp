#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from odsp.refit_scheme_sensitivity_benchmark import run_refit_scheme_sensitivity_benchmark


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    parser.add_argument("--seed",type=int,default=20260907)
    parser.add_argument("--nested-draws",type=int,default=2500)
    args=parser.parse_args()
    result=run_refit_scheme_sensitivity_benchmark(seed=args.seed,nested_draws=args.nested_draws)
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if not result["passed"]:
        raise SystemExit(1)


if __name__=="__main__":
    main()
