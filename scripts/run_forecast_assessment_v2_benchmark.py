#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from odsp.forecast_assessment_v2_benchmark import run_forecast_assessment_v2_benchmark


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=20260907)
    args=parser.parse_args()
    result=run_forecast_assessment_v2_benchmark(seed=args.seed)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'obligations':len(result['checks'])}))
    if not result['passed']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
