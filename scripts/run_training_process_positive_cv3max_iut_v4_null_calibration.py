"""Run frozen CV3max IUT v4 null qualification."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odsp.training_process_positive_cv3max_iut_calibration import (
    run_training_process_positive_cv3max_iut_v4_null_calibration,
)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,default=20261011)
    p.add_argument("--simulations",type=int,default=1000)
    p.add_argument("--require-pass", action="store_true")
    a=p.parse_args()
    result=run_training_process_positive_cv3max_iut_v4_null_calibration(
        seed=a.seed, simulations_per_scenario=a.simulations
    )
    payload=result.as_dict()
    a.output.write_text(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"qualification_pass":result.qualification_pass,
        "max_component_rates":{r.scenario_id:r.maximum_component_false_positive_rate for r in result.scenarios}},sort_keys=True))
    if a.require_pass and not result.qualification_pass: raise SystemExit(1)

if __name__=="__main__":
    main()
