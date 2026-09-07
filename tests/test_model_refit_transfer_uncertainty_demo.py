"""The runnable example must actually fit, and must fit training rows only."""
import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_demo_refits_never_receive_validation_rows(monkeypatch):
    spec = importlib.util.spec_from_file_location(
        'odsp_refit_training_demo', ROOT / 'examples' / 'model_refit_transfer_demo.py'
    )
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    seed = 20260907
    training_stream = np.random.SeedSequence(seed).spawn(3)[0]
    rng = np.random.default_rng(training_stream)
    x = rng.normal(size=800)
    y = 2*x + rng.normal(scale=0.5, size=800)
    training_pairs = set(zip(x.tolist(), y.tolist()))
    original_fit = demo._fit_on_training_rows
    calls = []

    def training_only_fit(observed_x, observed_y):
        assert observed_x.shape == observed_y.shape == (800,)
        assert all(pair in training_pairs for pair in zip(observed_x.tolist(), observed_y.tolist()))
        calls.append(1)
        return original_fit(observed_x, observed_y)

    monkeypatch.setattr(demo, '_fit_on_training_rows', training_only_fit)
    result = demo.run_demo(seed=seed)
    assert len(calls) == result['refits'] == 20
    assert result['validation_rows'] == 600
    assert result['validation_groups'] == 6
    assert result['data_kind'] == 'synthetic_usage_example'
    assert result['heldout_rows_used_to_fit_or_select_models'] is False
    assert result['population_coverage_validated'] is False
    assert result['audit']['refit_count'] == 20
    assert result['audit']['row_count'] == 600
    json.dumps(result, allow_nan=False)
