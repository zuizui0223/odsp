"""Fail-closed information-filtration layer for predictive transfer ladders.

The low-level predictive score ladder is algebraically valid for any ordered set
of commensurate held-out score vectors.  Interpreting adjacent steps as added
*information*, however, requires a stronger scientific condition: the declared
information sets must form a nested filtration

    C_0 \subset C_1 \subset ... \subset C_K.

This module makes that condition executable.  It attaches explicit conditioning
variables to every predictive level, rejects equal or non-nested information
sets, and then delegates scoring and familywise uncertainty to the existing
model-agnostic ODSP cores.

The nesting contract is about information available to the predictor, not about
software features or model complexity.  Two different algorithms fitted to the
same covariates do not constitute a new information level.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from .predictive_resolution import (
    PredictiveResolutionResult,
    decompose_predictive_resolution,
)
from .predictive_resolution_certification import (
    PredictiveResolutionCertification,
    certify_predictive_resolution,
)


@dataclass(frozen=True)
class InformationLevelScore:
    """One predictive level and the information explicitly available to it."""

    name: str
    information: tuple[str, ...]
    score: Sequence[float]

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("information-level name must be non-empty")
        variables = tuple(str(value).strip() for value in self.information)
        if any(not value for value in variables):
            raise ValueError("information labels must be non-empty")
        if len(set(variables)) != len(variables):
            raise ValueError(f"information labels must be unique within level {name!r}")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "information", variables)

    @property
    def information_set(self) -> frozenset[str]:
        return frozenset(self.information)


@dataclass(frozen=True)
class InformationTransferStep:
    """Declared information added by one adjacent predictive level."""

    lower_level: str
    upper_level: str
    lower_information: tuple[str, ...]
    upper_information: tuple[str, ...]
    added_information: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class InformationTransferResult:
    """Point transfer result whose information nesting has been validated."""

    score_name: str
    filtration_validated: bool
    levels: tuple[InformationLevelScore, ...]
    steps: tuple[InformationTransferStep, ...]
    predictive_result: PredictiveResolutionResult

    def as_dict(self) -> dict[str, object]:
        return {
            "score_name": self.score_name,
            "filtration_validated": self.filtration_validated,
            "levels": [
                {
                    "name": level.name,
                    "information": list(level.information),
                }
                for level in self.levels
            ],
            "steps": [step.as_dict() for step in self.steps],
            "predictive_result": self.predictive_result.as_dict(),
        }


@dataclass(frozen=True)
class InformationTransferCertification:
    """Familywise transfer ceiling under a validated information filtration."""

    score_name: str
    filtration_validated: bool
    levels: tuple[InformationLevelScore, ...]
    steps: tuple[InformationTransferStep, ...]
    certification: PredictiveResolutionCertification

    def as_dict(self) -> dict[str, object]:
        return {
            "score_name": self.score_name,
            "filtration_validated": self.filtration_validated,
            "levels": [
                {
                    "name": level.name,
                    "information": list(level.information),
                }
                for level in self.levels
            ],
            "steps": [step.as_dict() for step in self.steps],
            "certification": self.certification.as_dict(),
        }


def _normalized_score_name(score_name: str) -> str:
    value = str(score_name).strip()
    if not value:
        raise ValueError("score_name must be non-empty")
    return value


def validate_information_filtration(
    levels: Sequence[InformationLevelScore],
) -> tuple[InformationTransferStep, ...]:
    """Validate strict nesting and return the declared information increments.

    The first information set may be empty, representing a pooled or unconditional
    predictor. Every subsequent level must be a *strict* superset of the previous
    level. Equality is rejected because changing an algorithm without adding
    information is a model comparison, not an information-resolution step.
    """

    rows = tuple(levels)
    if len(rows) < 2:
        raise ValueError("information filtration must contain at least two levels")
    names = [row.name for row in rows]
    if len(set(names)) != len(names):
        raise ValueError("information-level names must be unique")

    result: list[InformationTransferStep] = []
    for lower, upper in zip(rows[:-1], rows[1:]):
        lower_set = lower.information_set
        upper_set = upper.information_set
        if lower_set == upper_set:
            raise ValueError(
                f"information level {upper.name!r} adds no information relative to "
                f"{lower.name!r}; equal information sets are model comparisons, not "
                "information-transfer steps"
            )
        if not lower_set < upper_set:
            lost = tuple(sorted(lower_set - upper_set))
            gained = tuple(sorted(upper_set - lower_set))
            raise ValueError(
                f"information levels are not nested from {lower.name!r} to {upper.name!r}; "
                f"lost={lost!r}, gained={gained!r}"
            )
        added = tuple(value for value in upper.information if value not in lower_set)
        result.append(
            InformationTransferStep(
                lower_level=lower.name,
                upper_level=upper.name,
                lower_information=lower.information,
                upper_information=upper.information,
                added_information=added,
            )
        )
    return tuple(result)


def decompose_information_transfer(
    levels: Sequence[InformationLevelScore],
    groups: Sequence[object],
    *,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    gain_tolerance: float = 0.0,
) -> InformationTransferResult:
    """Score a strictly nested information ladder on independent held-out groups."""

    rows = tuple(levels)
    steps = validate_information_filtration(rows)
    predictive = decompose_predictive_resolution(
        [(row.name, row.score) for row in rows],
        groups,
        sample_weight=sample_weight,
        gain_tolerance=gain_tolerance,
    )
    return InformationTransferResult(
        score_name=_normalized_score_name(score_name),
        filtration_validated=True,
        levels=rows,
        steps=steps,
        predictive_result=predictive,
    )


def certify_information_transfer(
    levels: Sequence[InformationLevelScore],
    groups: Sequence[object],
    *,
    score_name: str = "log",
    blocks: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260913,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> InformationTransferCertification:
    """Familywise-certify a strictly nested information-transfer ladder."""

    rows = tuple(levels)
    steps = validate_information_filtration(rows)
    certification = certify_predictive_resolution(
        [(row.name, row.score) for row in rows],
        groups,
        blocks=blocks,
        sample_weight=sample_weight,
        familywise_confidence_level=familywise_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )
    return InformationTransferCertification(
        score_name=_normalized_score_name(score_name),
        filtration_validated=True,
        levels=rows,
        steps=steps,
        certification=certification,
    )
