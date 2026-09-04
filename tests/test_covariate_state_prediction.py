import numpy as np
import pytest

sklearn = pytest.importorskip("sklearn")

from odsp.covariate_state_prediction import (
    fit_covariate_state_model,
    make_state_classifier,
)


def _training_data():
    x = np.linspace(-3.0, 3.0, 240)
    X = np.column_stack([x, x ** 2])
    y = np.where(x < -0.8, "low", np.where(x > 0.8, "high", "middle"))
    return X, y


def test_multinomial_covariate_model_predicts_state_at_new_rows():
    X, y = _training_data()
    estimator = make_state_classifier("multinomial_logit", C=20.0)
    model = fit_covariate_state_model(estimator, X, y)

    new = np.array([
        [-2.4, (-2.4) ** 2],
        [0.0, 0.0],
        [2.4, 2.4 ** 2],
    ])
    summaries = model.summarize(new)
    assert [summary.dominant_state for summary in summaries] == ["low", "middle", "high"]
    assert all(summary.dominant_probability > 0.7 for summary in summaries)
    assert all(summary.effective_states >= 1.0 for summary in summaries)


def test_covariate_model_beats_training_marginal_on_independent_rows():
    X, y = _training_data()
    estimator = make_state_classifier("multinomial_logit", C=20.0)
    model = fit_covariate_state_model(estimator, X, y)

    x = np.linspace(-2.9, 2.9, 120) + 0.013
    X_test = np.column_stack([x, x ** 2])
    y_test = np.where(x < -0.8, "low", np.where(x > 0.8, "high", "middle"))
    score = model.score(X_test, y_test)

    assert score.mean_log_score_gain > 0.5
    assert score.brier_improvement > 0.3
    assert score.top1_accuracy > 0.95


def test_random_forest_reference_classifier_uses_same_scoring_interface():
    X, y = _training_data()
    estimator = make_state_classifier(
        "random_forest",
        n_estimators=120,
        min_samples_leaf=2,
    )
    model = fit_covariate_state_model(estimator, X, y)

    x = np.linspace(-2.95, 2.95, 100) + 0.017
    X_test = np.column_stack([x, x ** 2])
    y_test = np.where(x < -0.8, "low", np.where(x > 0.8, "high", "middle"))
    score = model.score(X_test, y_test)

    assert score.mean_log_score_gain > 0.5
    assert score.top1_accuracy > 0.95


def test_covariate_model_rejects_state_absent_from_training():
    X, y = _training_data()
    estimator = make_state_classifier("multinomial_logit", C=20.0)
    model = fit_covariate_state_model(estimator, X, y)

    with pytest.raises(ValueError, match="absent from training"):
        model.score(np.array([[0.0, 0.0]]), ["unknown-state"])
