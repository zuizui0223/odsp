from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.bounded_reweighting_robustness_benchmark import (
    run_bounded_reweighting_robustness_benchmark,
)


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    parser.add_argument("--gamma",type=float,default=2.0)
    args=parser.parse_args()
    result=run_bounded_reweighting_robustness_benchmark(gamma=args.gamma)
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
    if not result["passed"]:
        raise SystemExit("bounded reweighting robustness benchmark failed")


if __name__=="__main__":
    main()
