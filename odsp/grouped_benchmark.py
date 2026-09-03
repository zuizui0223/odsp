"""Known-truth benchmark for independent-group transferability decisions."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .grouped_transferability import score_independent_groups
from .synthetic_benchmark import (
    shifted_organization_transferability_pair,
    stable_organization_transferability_pair,
)


@dataclass(frozen=True)
class GroupedTransferabilityBenchmarkCheck:
    family: str
    observed: str
    expected: str
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def run_grouped_transferability_benchmark() -> tuple[GroupedTransferabilityBenchmarkCheck, ...]:
    """Recover the three frozen independent-group sign-pattern categories."""

    model, stable = stable_organization_transferability_pair()
    _, shifted = shifted_organization_transferability_pair()

    all_stable = score_independent_groups(
        model,
        {"group-a": stable, "group-b": stable * 7.0},
        base_axes=(0, 1),
        added_axes=(2,),
    )
    conflicting = score_independent_groups(
        model,
        {"stable": stable, "shifted": shifted * 25.0},
        base_axes=(0, 1),
        added_axes=(2,),
    )
    all_shifted = score_independent_groups(
        model,
        {"group-a": shifted, "group-b": shifted * 100.0},
        base_axes=(0, 1),
        added_axes=(2,),
    )

    observed_expected = (
        ("all_stable", all_stable.classification, "generalizing"),
        ("stable_plus_shifted", conflicting.classification, "mixed"),
        ("all_shifted", all_shifted.classification, "non_generalizing"),
    )
    return tuple(
        GroupedTransferabilityBenchmarkCheck(
            family=family,
            observed=observed,
            expected=expected,
            passed=observed == expected,
        )
        for family, observed, expected in observed_expected
    )


def grouped_transferability_benchmark_passes() -> bool:
    return all(check.passed for check in run_grouped_transferability_benchmark())
