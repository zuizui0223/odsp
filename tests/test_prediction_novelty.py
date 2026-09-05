from __future__ import annotations

import numpy as np

from odsp.prediction_novelty import fit_environmental_novelty_model


def test_training_rows_are_in_domain_and_far_shift_is_strict_extrapolation():
    rng = np.random.default_rng(20260905)
    train = rng.normal(size=(600, 4))
    model = fit_environmental_novelty_model(train, reference_quantile=0.95)

    training_summaries = model.summarize(train[:50])
    assert all(item.category == "in_domain" for item in training_summaries)
    assert all(item.nearest_scaled_distance <= 1e-12 for item in training_summaries)

    shifted = rng.normal(loc=7.0, scale=0.3, size=(30, 4))
    shifted_summaries = model.summarize(shifted)
    assert all(item.category == "strict_extrapolation" for item in shifted_summaries)
    assert all(item.outside_feature_count >= 1 for item in shifted_summaries)


def test_multivariate_corner_can_be_novel_without_univariate_extrapolation():
    rng = np.random.default_rng(9)
    train = rng.normal(size=(1000, 3))
    model = fit_environmental_novelty_model(train, reference_quantile=0.9)
    query = (model.feature_max - 1e-8).reshape(1, -1)
    summary = model.summarize(query)[0]
    assert summary.outside_feature_count == 0
    assert summary.category == "novel"
    assert summary.novelty_ratio > 1.0


def test_novelty_is_affine_invariant_under_positive_feature_rescaling():
    rng = np.random.default_rng(31)
    train = rng.normal(size=(400, 3))
    query = rng.normal(size=(40, 3))
    scale = np.array([2.5, 0.3, 8.0])
    offset = np.array([10.0, -7.0, 2.0])

    original = fit_environmental_novelty_model(train, reference_quantile=0.95)
    transformed = fit_environmental_novelty_model(
        train * scale + offset, reference_quantile=0.95
    )
    a = original.summarize(query)
    b = transformed.summarize(query * scale + offset)

    np.testing.assert_allclose(
        [item.novelty_ratio for item in a],
        [item.novelty_ratio for item in b],
        rtol=0.0,
        atol=1e-10,
    )
    assert [item.category for item in a] == [item.category for item in b]
