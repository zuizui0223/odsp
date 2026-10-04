"""Run the frozen training-process IUT v2 null qualification."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odsp.training_process_positive_iut_null_calibration import (
    run_training_process_iut_null_calibration,
)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,default=20261013)
    p.add_argument("--simulations",type=int,default=1000)
    p.add_argument("--bootstrap-draws",type=int,default=500)
    args=p.parse_args()
    result=run_training_process_iut_null_calibration(
        seed=args.seed,
        simulations_per_scenario=args.simulations,
        bootstrap_draws=args.bootstrap_draws,
    )
    payload=result.as_dict()
    args.output.write_text(
        json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "qualification_pass":result.qualification_pass,
        "sentinel_rates":{
            row.scenario_id:row.sentinel_component_false_positive_rate
            for row in result.scenarios
        },
        "maximum_component_rates":{
            row.scenario_id:row.maximum_component_false_positive_rate
            for row in result.scenarios
        },
    },sort_keys=True))
    if not result.qualification_pass:
        raise SystemExit(1)

if __name__=="__main__":
    main()

# Workflow synchronization commit; inferential contract is unchanged.
