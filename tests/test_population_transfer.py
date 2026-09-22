from __future__ import annotations

import pytest

from odsp.information_transfer import InformationLevelScore, decompose_information_transfer
from odsp.population_transfer import summarize_population_transfer


def test_population_transfer_separates_total_gain_from_stepwise_ceiling():
    species_step = [-0.2, -0.2, 0.3, 0.3, 0.3, 0.3]
    context_step = [0.6] * 6
    full = [a + b for a, b in zip(species_step, context_step)]
    point = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), [0.0] * 6),
            InformationLevelScore("species", ("species",), species_step),
            InformationLevelScore(
                "species_context", ("species", "context"), full
            ),
        ),
        [f"g{i}" for i in range(6)],
    )
    summary = summarize_population_transfer(point, bootstrap_draws=1000, seed=31)

    assert summary.total_gain.mean_gain_status == "positive"
    assert summary.steps[0].mean_gain_status == "uncertain"
    assert summary.population_mean_supported_ceiling == "pooled"


def test_population_transfer_reports_positive_fraction_without_unanimity():
    gains = [0.5] * 27 + [-0.1] * 3
    point = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), [0.0] * 30),
            InformationLevelScore("richer", ("x",), gains),
        ),
        [f"g{i}" for i in range(30)],
    )
    summary = summarize_population_transfer(point, bootstrap_draws=500, seed=7)
    step = summary.steps[0]

    assert step.positive_group_fraction == pytest.approx(0.9)
    assert step.positive_fraction_lower == pytest.approx(0.743789, abs=1e-6)
    assert step.positive_fraction_lower_method == "wilson_score"


def test_population_transfer_cluster_bootstrap_is_declared_and_deterministic():
    gains = [0.2, 0.4, 0.6, 0.8]
    point = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), [0.0] * 4),
            InformationLevelScore("richer", ("x",), gains),
        ),
        ["g1", "g2", "g3", "g4"],
    )
    clusters = {"g1": "sp1", "g2": "sp1", "g3": "sp2", "g4": "sp2"}
    first = summarize_population_transfer(
        point, group_clusters=clusters, bootstrap_draws=500, seed=23
    )
    second = summarize_population_transfer(
        point, group_clusters=clusters, bootstrap_draws=500, seed=23
    )

    assert first.as_dict() == second.as_dict()
    assert first.cluster_count == 2
    assert (
        first.as_dict()["uncertainty"]["mean_interval_method"]
        == "cluster_percentile_bootstrap"
    )
