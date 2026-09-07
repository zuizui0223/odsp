#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.simultaneous_group_certification_benchmark import (
    run_simultaneous_group_certification_benchmark,
)


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    parser.add_argument("--seed",type=int,default=20260906)
    parser.add_argument("--bootstrap-draws",type=int,default=4000)
    args=parser.parse_args()
    result=run_simultaneous_group_certification_benchmark(
        seed=args.seed,bootstrap_draws=args.bootstrap_draws
    )
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if not result["passed"]:
        raise SystemExit("simultaneous group certification benchmark failed")


if __name__=="__main__":
    main()
