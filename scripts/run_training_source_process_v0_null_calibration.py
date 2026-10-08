"""Run the frozen training-source process v0 null calibration."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from odsp.training_source_process_v0_calibration import (
    run_training_source_v0_null_calibration,
)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,default=20261016)
    p.add_argument("--simulations",type=int,default=1000)
    a=p.parse_args()
    result=run_training_source_v0_null_calibration(
        seed=a.seed,
        simulations_per_scenario=a.simulations,
    )
    a.output.write_text(
        json.dumps(result.as_dict(),indent=2,sort_keys=True,allow_nan=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "qualification_pass":result.qualification_pass,
        "max_component_rates":{
            row.scenario_id:row.maximum_component_false_positive_rate
            for row in result.scenarios
        },
    },sort_keys=True))
    if not result.qualification_pass:
        raise SystemExit(1)


if __name__=="__main__":
    main()
