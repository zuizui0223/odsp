"""Run the frozen refit sensitivity benchmark without opening empirical data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odsp.model_refit_transfer_uncertainty_benchmark import run_model_refit_transfer_uncertainty_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=20260906)
    parser.add_argument('--nested-draws', type=int, default=4000)
    args = parser.parse_args()
    result = run_model_refit_transfer_uncertainty_benchmark(seed=args.seed, nested_draws=args.nested_draws)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'obligations': len(result['checks']),
                      'fragile_category': result['refit_fragile']['refit_aware_category'],
                      'identical_refits_bound_error': result['identical_refits_bound_error']}))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
