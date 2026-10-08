"""Exploratory post-failure diagnosis: NEVER a v1 qualification rerun.

Inspect why the frozen future-refit probability v1 validation max-t stage has
zero all-refit power under 8-oracle-SE positive shifts. Do not alter v1
statistical methods, thresholds, random seeds, or frozen qualification status.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odsp.training_process_future_refit_success_probability_calibration import (
    _known_probability_world,
    _run_world,
)

def _scenario(refit_count: int, block_count: int, repetitions: int, seed: int) -> dict:
    rng = np.random.default_rng(seed + 1000 * refit_count + block_count)
    critical = []
    counts = []
    worst_lower = []
    positive_cells = []
    for sim in range(repetitions):
        world, truth, _ = _known_probability_world(
            rng,
            refit_count=refit_count,
            blocks_per_group=block_count,
            group_count=6,
            contrast_count=2,
            p_success=1.0,
            positive_shift_oracle_se=8.0,
            training_cross_refit_validation_noise_correlation=0.35,
            contrast_correlation=0.5,
            distribution="normal",
        )
        assert bool(np.all(truth))
        result = _run_world(
            world,
            seed=seed + sim * 10007 + refit_count * 1000003,
            bootstrap_draws=500,
            validation_alpha=0.025,
            process_alpha=0.025,
        )
        critical.append(float(result.validation_bootstrap_t_critical_value))
        counts.append(int(result.certified_success_count))
        positive_cells.append(sum(cell.status == "robust_positive" for cell in result.cells))
        finite_lowers = [
            float(cell.lower_bound)
            for cell in result.cells
            if cell.lower_bound is not None and math.isfinite(cell.lower_bound)
        ]
        worst_lower.append(min(finite_lowers) if finite_lowers else None)
    finite_c = [c for c in critical if math.isfinite(c)]
    return {
        "refit_count":refit_count,
        "blocks_per_group":block_count,
        "repetitions":repetitions,
        "8_oracle_se_shift":True,
        "infinite_max_t_critical_fraction":sum(not math.isfinite(c) for c in critical)/repetitions,
        "finite_max_t_critical_values":finite_c,
        "certified_success_counts":counts,
        "positive_cell_counts":positive_cells,
        "all_refits_certified_fraction":sum(c==refit_count for c in counts)/repetitions,
        "worst_finite_lower_bounds":worst_lower,
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions",type=int,default=20)
    parser.add_argument("--seed",type=int,default=20261016)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.repetitions<1 or args.repetitions>100:
        raise ValueError("exploratory repetitions must be in 1..100")
    output={
        "diagnostic_only":True,
        "v1_prospective_failure_not_reclassified":True,
        "frozen_method_unchanged":True,
        "scenarios":[_scenario(8,8,args.repetitions,args.seed),_scenario(20,8,args.repetitions,args.seed)]
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    for row in output["scenarios"]:
        values=row["finite_max_t_critical_values"]
        print(json.dumps({
          "R":row["refit_count"],
          "B":row["blocks_per_group"],
          "infinite_critical_fraction":row["infinite_max_t_critical_fraction"],
          "median_finite_critical":float(np.median(values)) if values else None,
          "mean_certified_refits":float(np.mean(row["certified_success_counts"])),
          "mean_positive_cell_count":float(np.mean(row["positive_cell_counts"])),
          "all_certified_fraction":row["all_refits_certified_fraction"],
        },sort_keys=True))

if __name__=="__main__":
    main()
