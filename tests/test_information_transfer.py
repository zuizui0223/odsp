from __future__ import annotations

import pytest

from odsp.information_transfer import (
    InformationLevelScore,
    certify_information_transfer,
    decompose_information_transfer,
    validate_information_filtration,
)


def test_strict_information_filtration_records_added_variables():
    levels = (
        InformationLevelScore("pooled", (), [0.0, 0.0]),
        InformationLevelScore("species", ("species",), [0.2, 0.2]),
        InformationLevelScore(
            "species+site",
            ("species", "site"),
            [0.4, 0.4],
        ),
        InformationLevelScore(
            "species+site+season",
            ("species", "site", "season"),
            [0.5, 0.5],
        ),
    )

    steps = validate_information_filtration(levels)
    assert [step.added_information for step in steps] == [
        ("species",),
        ("site",),
        ("season",),
    ]


def test_equal_information_sets_are_model_comparisons_not_information_steps():
    levels = (
        InformationLevelScore("rf", ("species", "site"), [0.0, 0.0]),
        InformationLevelScore("neural_net", ("species", "site"), [0.1, 0.1]),
    )
    with pytest.raises(ValueError, match="adds no information"):
        validate_information_filtration(levels)


def test_non_nested_levels_fail_closed_and_report_lost_information():
    levels = (
        InformationLevelScore("species", ("species",), [0.0, 0.0]),
        InformationLevelScore("site", ("site",), [0.1, 0.1]),
    )
    with pytest.raises(ValueError, match="not nested.*lost=.*species.*gained=.*site"):
        validate_information_filtration(levels)


def test_information_transfer_wraps_point_ladder_without_changing_estimand():
    levels = (
        InformationLevelScore("pooled", (), [-1.0, -1.0, -1.0, -1.0]),
        InformationLevelScore("species", ("species",), [-0.6, -0.6, -0.6, -0.6]),
        InformationLevelScore(
            "species+context",
            ("species", "context"),
            [-0.7, -0.7, -0.5, -0.5],
        ),
    )
    result = decompose_information_transfer(
        levels,
        ["a", "a", "b", "b"],
        score_name="log",
    )

    assert result.filtration_validated is True
    assert result.score_name == "log"
    assert result.steps[1].added_information == ("context",)
    assert result.predictive_result.total_gain_category == "generalizing"
    assert result.predictive_result.all_group_point_transfer_ceiling == "species"


def test_nonlog_score_keeps_filtration_but_not_log_label():
    levels = (
        InformationLevelScore("pooled", (), [-0.25, -0.25]),
        InformationLevelScore("species", ("species",), [-0.16, -0.20]),
    )
    result = decompose_information_transfer(
        levels,
        ["a", "b"],
        score_name="negative_brier",
    )
    assert result.score_name == "negative_brier"
    assert result.filtration_validated is True


def test_familywise_certification_requires_same_validated_filtration():
    n = 10
    groups = ["a"] * n + ["b"] * n
    blocks = [f"a-{i}" for i in range(n)] + [f"b-{i}" for i in range(n)]
    levels = (
        InformationLevelScore("pooled", (), [0.0] * (2 * n)),
        InformationLevelScore("species", ("species",), [0.3] * (2 * n)),
        InformationLevelScore(
            "species+context",
            ("species", "context"),
            [0.5] * (2 * n),
        ),
    )

    result = certify_information_transfer(
        levels,
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=29,
    )

    assert result.filtration_validated is True
    assert result.certification.point_transfer_ceiling == "species+context"
    assert result.certification.certified_transfer_ceiling == "species+context"
    assert [step.added_information for step in result.steps] == [
        ("species",),
        ("context",),
    ]


def test_level_validation_rejects_blank_or_duplicate_information_labels():
    with pytest.raises(ValueError, match="name must be non-empty"):
        InformationLevelScore("  ", (), [0.0, 0.0])
    with pytest.raises(ValueError, match="information labels must be unique"):
        InformationLevelScore("bad", ("species", "species"), [0.0, 0.0])
