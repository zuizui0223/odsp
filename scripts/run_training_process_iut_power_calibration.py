"""Run the frozen training-process IUT v2 power qualification."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odsp.training_process_positive_iut_power_calibration import (
    run_training_process_iut_power_calibration,
)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,default=20261014)
    p.add_argument("--simulations",type=int,default=1000)
    p.add_argument("--bootstrap-draws",type=int,default=500)
    args=p.parse_args()
    result=run_training_process_iut_power_calibration(
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
        "carryover_power":{
            row.scenario_id:row.carryover_terminal_power
            for row in result.scenarios
        },
        "strong_power":{
            row.scenario_id:row.strong_terminal_power
            for row in result.scenarios
        },
    },sort_keys=True))
    if not result.qualification_pass:
        raise SystemExit(1)

if __name__=="__main__":
    main()

# Workflow synchronization commit; inferential contract is unchanged.
