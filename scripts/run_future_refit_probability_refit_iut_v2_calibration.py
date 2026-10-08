"""Run frozen first-1000 refit-level IUT v2 probability qualification."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from odsp.training_process_future_refit_probability_iut_v2_calibration import (
    run_future_refit_probability_refit_iut_v2_calibration,
)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,default=20261019)
    p.add_argument("--simulations",type=int,default=1000)
    a=p.parse_args()
    result=run_future_refit_probability_refit_iut_v2_calibration(
        seed=a.seed, simulations_per_scenario=a.simulations,
    )
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result.as_dict(),indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "qualification_pass":result.qualification_pass,
        "coverage":{r.scenario_id:{"overclaim":r.overall_overclaim_rate,"overcertification":r.validation_overcertification_rate,"mean_certified_count":r.mean_certified_success_count,"pass":r.acceptance_pass} for r in result.coverage_rows},
        "power":{r.scenario_id:{"all_certified_power":r.all_refits_certified_power,"mean_certified_count":r.mean_certified_success_count,"pass":r.acceptance_pass} for r in result.power_rows}
    },sort_keys=True))
    if not result.qualification_pass:
        raise SystemExit(1)

if __name__=="__main__":main()
