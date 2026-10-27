from __future__ import annotations

import math

import pytest

from odsp.new_group_gain_envelope import fit_new_group_gain_lower_envelope


def _fit(values, alpha=0.1, **kwargs):
    ids = [f"animal_{i}" for i in range(len(values))]
    return fit_new_group_gain_lower_envelope(
        values, ids, miscoverage=alpha, **kwargs
    )


def test_exact_leave_one_group_out_rank_coverage_for_distinct_exchangeable_scores():
    """Enumerating every possible new-group rank gives exact coverage."""
    all_scores = [float(i) / 7.0 for i in range(20)]
    covered = []
    for withheld in range(20):
        calibration = [
            value for position, value in enumerate(all_scores)
            if position != withheld
        ]
        envelope = _fit(
            calibration,
            0.1,
            source_design="fixed_predictor_groups",
        )
        covered.append(
            envelope.covers_new_group("prospectively_new", all_scores[withheld])
        )
        assert envelope.finite_sample_rank == 2
        assert envelope.conservative_coverage_if_exchangeable == 0.9
        assert envelope.inference_status.startswith("conditional_rank_")
        assert not envelope.as_dict()["exchangeability_verified_by_software"]
    assert sum(covered) == 18


def test_vacuous_small_sample_bound_cannot_be_called_a_positive_certificate():
    envelope = _fit([0.9] * 8)
    assert envelope.finite_sample_rank == 0
    assert envelope.bound_is_vacuous
    assert envelope.lower_gain_bound == -math.inf
    assert envelope.covers_new_group("future", -1000.0)
    exported = envelope.as_dict()
    assert exported["lower_gain_bound"] is None
    assert exported["bound_above_threshold"] is False
    assert exported["conservative_coverage_if_exchangeable"] == 1.0
    assert "descriptive_only" in exported["inference_status"]


def test_nine_groups_have_one_rank_at_ten_percent_miscoverage():
    envelope = _fit([2.0, 1.5, 1.0, 0.3, 0.2, 4.0, 5.0, 1.1, 8.0])
    assert envelope.finite_sample_rank == 1
    assert envelope.lower_gain_bound == 0.2
    assert envelope.as_dict()["bound_above_threshold"] is True
    assert envelope.as_dict()["not_a_mean_gain_confidence_interval"]


def test_rank_cannot_be_increased_by_many_within_animal_fixes():
    # There are two animals, not 10_001 exchangeable GPS observations.
    small = _fit([-1.0, 0.5])
    assert small.calibration_group_count == 2
    assert small.finite_sample_rank == 0
    with pytest.raises(ValueError, match="duplicate group IDs"):
        fit_new_group_gain_lower_envelope(
            [-1.0, *([0.5] * 10000)],
            ["animal_1", *("animal_2" for _ in range(10000))],
        )


def test_ties_are_conservative_and_group_ids_are_private_in_export():
    envelope = _fit([0.3] * 19)
    assert envelope.finite_sample_rank == 2
    assert envelope.covers_new_group("unseen", 0.3)
    assert envelope.covers_new_group("unseen", 0.31)
    assert not envelope.covers_new_group("unseen", 0.29)
    assert "animal_1" not in str(envelope.as_dict())
    with pytest.raises(ValueError, match="overlaps"):
        envelope.covers_new_group("animal_1", 0.3)


@pytest.mark.parametrize(
    "values, ids, expected",
    [
        ([], [], "one independent group"),
        ([0.1], [], "one independent group"),
        ([0.1, 0.2], ["a", "a"], "duplicate group IDs"),
        ([0.1], [""], "non-empty"),
        ([math.nan], ["a"], "finite"),
        ([math.inf], ["a"], "finite"),
        ([True], ["a"], "finite"),
        (["bad"], ["a"], "finite"),
    ],
)
def test_bad_calibration_data_fail_closed(values, ids, expected):
    with pytest.raises(ValueError, match=expected):
        fit_new_group_gain_lower_envelope(values, ids)


@pytest.mark.parametrize("alpha", [0.0, 1.0, -0.1, math.nan, math.inf])
def test_invalid_miscoverage_is_rejected(alpha):
    with pytest.raises(ValueError, match="miscoverage"):
        _fit([0.1, 0.2, 0.3], alpha)


def test_undeclared_evidence_mode_is_rejected():
    with pytest.raises(ValueError, match="source_design"):
        _fit([0.2, 0.3], source_design="automatically_certified")


def test_new_group_must_have_distinct_id_and_finite_gain():
    result = _fit([0.1] * 30)
    with pytest.raises(ValueError, match="new group_id"):
        result.covers_new_group(" ", 0.1)
    with pytest.raises(ValueError, match="finite"):
        result.covers_new_group("future", float("nan"))


def test_nonaligned_input_and_threshold_fail_closed():
    with pytest.raises(ValueError, match="one independent group"):
        fit_new_group_gain_lower_envelope([0.1, 0.2], ["a"])
    with pytest.raises(ValueError, match="gain_threshold"):
        _fit([0.1], gain_threshold=float("inf"))


def test_known_truth_unequal_within_animal_fix_counts_cannot_fake_coverage():
    """Exchangeable animals, but positive-gain animals contribute many more fixes.

    Each animal has one latent gain. Its telemetry fixes are perfectly
    correlated copies of that gain; positive animals have 200 fixes and
    negative animals only two. Using *fixes* as calibration units violates
    the future-animal rank guarantee even though group gains are exchangeable.
    """
    import numpy as np

    rng = np.random.default_rng(20261026)
    group_covered = 0
    naive_fix_covered = 0
    trials = 800
    for scores in rng.normal(size=(trials, 20)):
        calibration = scores[:19]
        future = float(scores[19])
        envelope = _fit(calibration.tolist(), 0.1)
        group_covered += envelope.covers_new_group("future", future)

        # Intentionally INVALID naive comparator: treat clustered fixes as
        # independent group calibrators. This is only a known-truth control.
        per_animal_fix_count = np.where(calibration > 0, 200, 2)
        pseudo_rows = np.sort(np.repeat(calibration, per_animal_fix_count))
        naive_rank = math.floor((len(pseudo_rows) + 1) * 0.1)
        naive_lower = (
            float(pseudo_rows[naive_rank - 1])
            if naive_rank > 0 else float("-inf")
        )
        naive_fix_covered += future >= naive_lower

    group_rate = group_covered / trials
    naive_fix_rate = naive_fix_covered / trials
    assert 0.87 <= group_rate <= 0.94
    assert naive_fix_rate < 0.75
    assert group_rate - naive_fix_rate > 0.12
