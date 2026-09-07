"""Synthetic training-only refits scored on one untouched validation set.

This is a runnable usage example, NOT a new empirical ecological demonstration.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odsp.model_refit_transfer_uncertainty import audit_model_refit_transfer_uncertainty


def _fit_on_training_rows(x, y):
    design = np.column_stack([np.ones(x.size), x])
    coef = np.linalg.lstsq(design, y, rcond=None)[0]
    sd = max(float(np.sqrt(np.mean((y-design@coef)**2))), 1e-6)
    return coef, sd, float(y.mean()), max(float(y.std()), 1e-6)


def _log_normal(y, mean, sd):
    return -0.5*np.log(2*np.pi)-np.log(sd)-0.5*((y-mean)/sd)**2


def run_demo(seed=20260907):
    training_rng, validation_rng, resampling_rng = [
        np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(3)
    ]
    train_x = training_rng.normal(size=800)
    train_y = 2*train_x + training_rng.normal(scale=0.5, size=800)
    test_x = validation_rng.normal(size=600)
    test_y = 2*test_x + validation_rng.normal(scale=0.5, size=600)
    validation_groups = tuple(f'individual-{i}' for i in range(6) for _ in range(100))
    validation_blocks = tuple(f'day-{b:02d}' for _ in range(6) for b in range(20) for _ in range(5))
    train_blocks = np.arange(800).reshape(40, 20)
    rows = []
    # These fits never receive test_x or test_y. Both comparators are trained
    # on the same resampled training rows as their corresponding conditional fit.
    for _ in range(20):
        index = train_blocks[resampling_rng.integers(0, 40, 40)].reshape(-1)
        coef, sd, marginal_mean, marginal_sd = _fit_on_training_rows(train_x[index], train_y[index])
        mean = coef[0]+coef[1]*test_x
        rows.append(_log_normal(test_y, mean, sd)-_log_normal(test_y, marginal_mean, marginal_sd))
    audit = audit_model_refit_transfer_uncertainty(
        np.asarray(rows), validation_groups, blocks=validation_blocks,
        refit_ids=tuple(f'training-refit-{i:02d}' for i in range(20)),
        nested_draws=4000, seed=seed,
    )
    return {
        'data_kind': 'synthetic_usage_example',
        'training_rows': 800, 'training_blocks': 40, 'refits': 20,
        'validation_rows': 600, 'validation_groups': 6,
        'heldout_rows_used_to_fit_or_select_models': False,
        'population_coverage_validated': False,
        'audit': audit.as_dict(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run_demo()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'reference': result['audit']['reference_fit_category'],
                      'refit_aware': result['audit']['refit_aware_category']}))


if __name__ == '__main__':
    main()
