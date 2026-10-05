"""Run frozen training-process IUT v2 power qualification."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odsp.training_process_positive_iut_power_calibration import run_training_process_positive_iut_power_calibration

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,default=20261008)
    p.add_argument("--simulations",type=int,default=1000)
    p.add_argument("--bootstrap-draws",type=int,default=500)
    p.add_argument("--require-pass", action="store_true")
    a=p.parse_args()
    r=run_training_process_positive_iut_power_calibration(
        seed=a.seed,simulations_per_scenario=a.simulations,bootstrap_draws=a.bootstrap_draws
    )
    a.output.write_text(json.dumps(r.as_dict(),indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "qualification_pass":r.qualification_pass,
        "moderate_terminal_power":{x.scenario_id:x.moderate_terminal_power for x in r.scenarios},
        "strong_terminal_power":{x.scenario_id:x.strong_terminal_power for x in r.scenarios}
    },sort_keys=True))
    if a.require_pass and not r.qualification_pass: raise SystemExit(1)
if __name__=="__main__": main()
