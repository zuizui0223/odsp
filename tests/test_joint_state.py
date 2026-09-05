from __future__ import annotations

import numpy as np

from odsp.joint_state import (
    fit_joint_continuous_circular_state_model,
    score_joint_log_density_gain,
    score_joint_state_groups,
)


def _sample(seed: int, n: int, *, coupling: float = 1.1, time_shift: float = 0.0):
    rng = np.random.default_rng(seed)
    X = rng.uniform(-1.0, 1.0, size=(n, 2))
    mean_angle = 1.0 + 0.55 * X[:, 0] - 0.35 * X[:, 1] + time_shift
    angle = rng.vonmises(mean_angle, 10.0)
    time_state = np.mod(angle, 2.0 * np.pi) * 24.0 / (2.0 * np.pi)
    height = (
        2.5
        + 0.9 * X[:, 0]
        - 0.6 * X[:, 1]
        + coupling * np.cos(angle - 0.4)
        + rng.normal(scale=0.45, size=n)
    )
    return X, height, time_state


def test_joint_model_improves_contextual_joint_and_coupling_density():
    X_train, z_train, t_train = _sample(10, 3000)
    X_test, z_test, t_test = _sample(11, 5000)
    model = fit_joint_continuous_circular_state_model(
        X_train, z_train, t_train, period=24.0
    )
    score = model.score(X_test, z_test, t_test)
    assert score.mean_joint_log_density_gain > 0.1
    assert score.mean_coupling_log_density_gain > 0.05


def test_joint_summary_and_sampling_return_state_rich_output():
    X_train, z_train, t_train = _sample(20, 2500)
    model = fit_joint_continuous_circular_state_model(X_train, z_train, t_train)
    X_new = np.array([[0.0, 0.0], [0.7, -0.2]])
    summaries = model.summarize(X_new)
    assert len(summaries) == 2
    assert all(0.0 <= row.time_mean_state < 24.0 for row in summaries)
    assert all(row.height_upper_at_time_mode > row.height_lower_at_time_mode for row in summaries)

    height, time = model.sample_joint(X_new, draws_per_row=50, random_state=77)
    assert height.shape == (2, 50)
    assert time.shape == (2, 50)
    assert np.all((time >= 0.0) & (time < 24.0))
    assert np.isfinite(height).all()


def test_external_joint_density_interface_separates_context_and_coupling_gain():
    score = score_joint_log_density_gain(
        conditional_joint_log_density=[-1.0, -1.2, -1.1],
        marginal_joint_log_density=[-2.0, -2.1, -2.2],
        factorized_contextual_log_density=[-1.5, -1.6, -1.4],
    )
    assert score.mean_joint_log_density_gain > 0.0
    assert score.mean_coupling_log_density_gain > 0.0


def test_grouped_joint_scoring_keeps_joint_and_coupling_categories_separate():
    X_train, z_train, t_train = _sample(30, 3500)
    X_test, z_test, t_test = _sample(31, 4000)
    model = fit_joint_continuous_circular_state_model(X_train, z_train, t_train)
    groups = np.repeat(["a", "b", "c", "d"], 1000)
    grouped = score_joint_state_groups(model, X_test, z_test, t_test, groups)
    assert len(grouped.groups) == 4
    assert grouped.joint_gain_category == "generalizing"
    assert grouped.coupling_gain_category == "generalizing"
