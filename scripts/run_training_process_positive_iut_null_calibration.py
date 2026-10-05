"""Run frozen training-process IUT v2 null qualification."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odsp.training_process_positive_iut_calibration import run_training_process_positive_iut_null_calibration

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,default=20261007)
    p.add_argument("--simulations",type=int,default=1000)
    p.add_argument("--bootstrap-draws",type=int,default=500)
    p.add_argument("--require-pass", action="store_true")
    a=p.parse_args()
    r=run_training_process_positive_iut_null_calibration(
        seed=a.seed,simulations_per_scenario=a.simulations,bootstrap_draws=a.bootstrap_draws
    )
    a.output.write_text(json.dumps(r.as_dict(),indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "qualification_pass":r.qualification_pass,
        "max_component_rates":{x.scenario_id:x.maximum_component_false_positive_rate for x in r.scenarios}
    },sort_keys=True))
    if a.require_pass and not r.qualification_pass: raise SystemExit(1)
if __name__=="__main__": main()
