from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("sklearn")

from odsp.covariate_state_prediction import fit_covariate_state_model, make_state_classifier
from odsp.prediction_novelty import fit_environmental_novelty_model
from odsp.prediction_trust import trusted_state_predictions
from odsp.prediction_uncertainty import fit_state_conformal_calibrator


def _make_data(seed: int = 20260905):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(1200, 3))
    score = 1.2 * X[:, 0] - 0.8 * X[:, 1] + 0.4 * X[:, 2]
    probability = 1.0 / (1.0 + np.exp(-score))
    y = np.where(rng.random(X.shape[0]) < probability, "high", "low")
    return X, y


def test_trusted_state_prediction_combines_probability_set_and_novelty_without_collapsing_them():
    X, y = _make_data()
    X_train, y_train = X[:700], y[:700]
    X_cal, y_cal = X[700:950], y[700:950]
    X_test = X[950:]

    estimator = make_state_classifier("multinomial_logit", random_state=20260905)
    model = fit_covariate_state_model(estimator, X_train, y_train)
    p_cal = model.predict_proba(X_cal)
    calibrator = fit_state_conformal_calibrator(
        p_cal,
        y_cal,
        classes=model.classes,
        miscoverage=0.1,
    )
    novelty = fit_environmental_novelty_model(X_train, reference_quantile=0.95)

    rows = trusted_state_predictions(model, calibrator, novelty, X_test[:20])
    assert len(rows) == 20
    for row in rows:
        assert abs(sum(row.state_probabilities) - 1.0) < 1e-10
        assert row.dominant_state in model.classes
        assert row.conformal_set_size >= 1
        assert set(row.conformal_states).issubset(set(model.classes))
        assert row.conformal_target_coverage == 0.9
        assert row.novelty_category in {"in_domain", "novel", "strict_extrapolation"}
        assert row.novelty_ratio >= 0


def test_trusted_state_prediction_rejects_class_order_mismatch():
    X, y = _make_data(seed=5)
    model = fit_covariate_state_model(
        make_state_classifier("multinomial_logit"), X[:700], y[:700]
    )
    p_cal = model.predict_proba(X[700:900])
    reversed_classes = tuple(reversed(model.classes))
    calibrator = fit_state_conformal_calibrator(
        p_cal[:, ::-1], y[700:900], classes=reversed_classes, miscoverage=0.1
    )
    novelty = fit_environmental_novelty_model(X[:700])
    with pytest.raises(ValueError, match="classes must match"):
        trusted_state_predictions(model, calibrator, novelty, X[900:905])
