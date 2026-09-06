from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.bias_robust_model_selection_benchmark import run_bias_robust_model_selection_benchmark


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    result=run_bias_robust_model_selection_benchmark()
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
