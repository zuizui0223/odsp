"""Deterministic property benchmark for the generic N2 evidence core.

This module does not add a new empirical endpoint.  It tests implementation-level
and mathematical generality of the axis-agnostic quantities already used by N2:

* conditional added-axis information ``H(A|B)``;
* effective added-state count ``exp(H(A|B))``;
* fitted organization ``I(A;B)``;
* held-out conditional-versus-marginal log-score gain;
* conservative independent-group classification.

The benchmark deliberately varies tensor dimension, axis placement, state
cardinality, positive mass scale, category labels, omitted nuisance axes and
independent-group mass.  It therefore tests invariance/equivariance properties
that should hold regardless of whether an added axis is called height, depth,
time, behaviour, substrate, microhabitat or something else.

The empirical meaning of an axis is still a separate scientific requirement:
passing these properties does not make biased observations representative or
convert a descriptive state axis into a causal mechanism.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .grouped_transferability import score_independent_groups
from .niche_geometry import conditional_information, effective_conditional_states
from .transferability import (
    base_added_mutual_information,
    score_conditional_transferability,
)


DEFAULT_SEED = 20260904
DEFAULT_RANDOM_CASES = 128
ABS_TOL = 2e-10


@dataclass(frozen=True)
class GeneralityCheck:
    """One deterministic proof obligation evaluated by the benchmark."""

    family: str
    case_id: str
    property_name: str
    passed: bool
    absolute_error: float
    tolerance: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GeneralityBenchmarkResult:
    """Audit-ready summary of the deterministic generality benchmark."""

    seed: int
    randomized_case_count: int
    check_count: int
    passed_count: int
    failed_count: int
    maximum_absolute_error: float
    tensor_ndim_range: tuple[int, int]
    state_cardinality_range: tuple[int, int]
    properties: tuple[str, ...]
    checks: tuple[GeneralityCheck, ...]

    @property
    def passed(self) -> bool:
        return self.failed_count == 0

    def as_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "randomized_case_count": self.randomized_case_count,
            "check_count": self.check_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "maximum_absolute_error": self.maximum_absolute_error,
            "tensor_ndim_range": list(self.tensor_ndim_range),
            "state_cardinality_range": list(self.state_cardinality_range),
            "properties": list(self.properties),
            "passed": self.passed,
            "checks": [check.as_dict() for check in self.checks],
        }


def _finite_error(left: float, right: float) -> float:
    if left == right:
        return 0.0
    if math.isfinite(left) and math.isfinite(right):
        return abs(float(left) - float(right))
    return float("inf")


def _append_close(
    checks: list[GeneralityCheck],
    *,
    family: str,
    case_id: str,
    property_name: str,
    observed: float,
    expected: float,
    tolerance: float = ABS_TOL,
) -> None:
    error = _finite_error(float(observed), float(expected))
    checks.append(
        GeneralityCheck(
            family=family,
            case_id=case_id,
            property_name=property_name,
            passed=bool(error <= tolerance),
            absolute_error=float(error),
            tolerance=float(tolerance),
        )
    )


def _positive_random_field(rng: np.random.Generator, shape: Sequence[int]) -> np.ndarray:
    """Return strictly positive heterogeneous support so every log score is finite."""

    return rng.gamma(shape=1.7, scale=1.0, size=tuple(shape)) + 0.05


def _random_axis_partition(
    rng: np.random.Generator,
    ndim: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    order = [int(value) for value in rng.permutation(ndim)]
    max_base = min(2, ndim - 1)
    n_base = int(rng.integers(1, max_base + 1))
    remaining = ndim - n_base
    max_added = min(2, remaining)
    n_added = int(rng.integers(1, max_added + 1))
    return tuple(order[:n_base]), tuple(order[n_base : n_base + n_added])


def _relabel_states(
    rng: np.random.Generator,
    field: np.ndarray,
) -> np.ndarray:
    result = np.asarray(field, dtype=float)
    for axis, cardinality in enumerate(result.shape):
        labels = rng.permutation(cardinality)
        result = np.take(result, labels, axis=axis)
    return result


def _run_randomized_invariance_cases(
    rng: np.random.Generator,
    checks: list[GeneralityCheck],
    case_count: int,
) -> None:
    for index in range(case_count):
        ndim = int(rng.integers(2, 7))
        shape = tuple(int(value) for value in rng.integers(2, 6, size=ndim))
        base_axes, added_axes = _random_axis_partition(rng, ndim)
        support = _positive_random_field(rng, shape)
        case_id = f"random-{index:03d}-d{ndim}-shape{'x'.join(map(str, shape))}"

        h = conditional_information(
            support,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        n_eff = effective_conditional_states(
            support,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        mi = base_added_mutual_information(
            support,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        same_score = score_conditional_transferability(
            support,
            support,
            base_axes=base_axes,
            added_axes=added_axes,
        )

        # Identity: evaluating the exact same distribution makes the expected
        # conditional-vs-marginal log-score gain equal I(A;B).
        _append_close(
            checks,
            family="same_distribution_identity",
            case_id=case_id,
            property_name="heldout_gain_equals_mutual_information",
            observed=same_score.mean_log_score_gain,
            expected=mi,
        )

        # Entropy/effective-state bounds depend only on added-axis cardinality.
        added_cardinality = int(np.prod([shape[axis] for axis in added_axes]))
        checks.append(
            GeneralityCheck(
                family="information_bounds",
                case_id=case_id,
                property_name="effective_states_within_added_cardinality",
                passed=bool(1.0 - ABS_TOL <= n_eff <= added_cardinality + ABS_TOL),
                absolute_error=float(
                    max(0.0, 1.0 - n_eff, n_eff - added_cardinality)
                ),
                tolerance=ABS_TOL,
            )
        )

        # Positive rescaling changes neither normalized probabilities nor scores.
        model_scale = float(10.0 ** rng.uniform(-5.0, 5.0))
        heldout_scale = float(10.0 ** rng.uniform(-5.0, 5.0))
        scaled = support * model_scale
        h_scaled = conditional_information(
            scaled,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        mi_scaled = base_added_mutual_information(
            scaled,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        score_scaled = score_conditional_transferability(
            support * model_scale,
            support * heldout_scale,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        _append_close(
            checks,
            family="positive_mass_scaling",
            case_id=case_id,
            property_name="conditional_information_invariant",
            observed=h_scaled,
            expected=h,
        )
        _append_close(
            checks,
            family="positive_mass_scaling",
            case_id=case_id,
            property_name="mutual_information_invariant",
            observed=mi_scaled,
            expected=mi,
        )
        _append_close(
            checks,
            family="positive_mass_scaling",
            case_id=case_id,
            property_name="heldout_gain_invariant_to_separate_model_and_test_mass",
            observed=score_scaled.mean_log_score_gain,
            expected=same_score.mean_log_score_gain,
        )

        # Axis names/order are representational.  Simultaneously permuting the
        # tensor dimensions and remapping axis indices must leave the quantities.
        axis_order = tuple(int(value) for value in rng.permutation(ndim))
        transposed = np.transpose(support, axis_order)
        new_index = {old_axis: axis_order.index(old_axis) for old_axis in range(ndim)}
        base_transposed = tuple(new_index[axis] for axis in base_axes)
        added_transposed = tuple(new_index[axis] for axis in added_axes)
        h_transposed = conditional_information(
            transposed,
            base_axes=base_transposed,
            added_axes=added_transposed,
        )
        mi_transposed = base_added_mutual_information(
            transposed,
            base_axes=base_transposed,
            added_axes=added_transposed,
        )
        score_transposed = score_conditional_transferability(
            transposed,
            transposed,
            base_axes=base_transposed,
            added_axes=added_transposed,
        )
        _append_close(
            checks,
            family="axis_permutation_equivariance",
            case_id=case_id,
            property_name="conditional_information_equivariant",
            observed=h_transposed,
            expected=h,
        )
        _append_close(
            checks,
            family="axis_permutation_equivariance",
            case_id=case_id,
            property_name="mutual_information_equivariant",
            observed=mi_transposed,
            expected=mi,
        )
        _append_close(
            checks,
            family="axis_permutation_equivariance",
            case_id=case_id,
            property_name="heldout_gain_equivariant",
            observed=score_transposed.mean_log_score_gain,
            expected=same_score.mean_log_score_gain,
        )

        # Category labels are arbitrary.  Relabel every state on every axis.
        relabeled = _relabel_states(rng, support)
        h_relabeled = conditional_information(
            relabeled,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        mi_relabeled = base_added_mutual_information(
            relabeled,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        score_relabeled = score_conditional_transferability(
            relabeled,
            relabeled,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        _append_close(
            checks,
            family="state_label_permutation",
            case_id=case_id,
            property_name="conditional_information_label_invariant",
            observed=h_relabeled,
            expected=h,
        )
        _append_close(
            checks,
            family="state_label_permutation",
            case_id=case_id,
            property_name="mutual_information_label_invariant",
            observed=mi_relabeled,
            expected=mi,
        )
        _append_close(
            checks,
            family="state_label_permutation",
            case_id=case_id,
            property_name="heldout_gain_label_invariant",
            observed=score_relabeled.mean_log_score_gain,
            expected=same_score.mean_log_score_gain,
        )

        # Add an omitted nuisance axis that simply refines each state into two
        # parts whose masses sum to the original.  Marginalizing omitted axes must
        # recover exactly the original base-added evidence.
        split = float(rng.uniform(0.05, 0.95))
        refined = np.stack((support * split, support * (1.0 - split)), axis=-1)
        h_refined = conditional_information(
            refined,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        mi_refined = base_added_mutual_information(
            refined,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        score_refined = score_conditional_transferability(
            refined,
            refined,
            base_axes=base_axes,
            added_axes=added_axes,
        )
        _append_close(
            checks,
            family="omitted_nuisance_refinement",
            case_id=case_id,
            property_name="conditional_information_unchanged",
            observed=h_refined,
            expected=h,
        )
        _append_close(
            checks,
            family="omitted_nuisance_refinement",
            case_id=case_id,
            property_name="mutual_information_unchanged",
            observed=mi_refined,
            expected=mi,
        )
        _append_close(
            checks,
            family="omitted_nuisance_refinement",
            case_id=case_id,
            property_name="heldout_gain_unchanged",
            observed=score_refined.mean_log_score_gain,
            expected=same_score.mean_log_score_gain,
        )


def _run_conditional_independence_cases(
    rng: np.random.Generator,
    checks: list[GeneralityCheck],
    case_count: int = 32,
) -> None:
    for index in range(case_count):
        n_base = int(rng.integers(2, 7))
        n_a1 = int(rng.integers(2, 7))
        n_a2 = int(rng.integers(2, 7))
        p_base = rng.dirichlet(np.full(n_base, 1.5))
        p_a1_given_b = np.vstack(
            [rng.dirichlet(np.full(n_a1, 1.2)) for _ in range(n_base)]
        )
        p_a2_given_b = np.vstack(
            [rng.dirichlet(np.full(n_a2, 1.2)) for _ in range(n_base)]
        )
        support = (
            p_base[:, None, None]
            * p_a1_given_b[:, :, None]
            * p_a2_given_b[:, None, :]
        )
        case_id = f"factorized-{index:02d}-{n_base}x{n_a1}x{n_a2}"
        h1 = conditional_information(support, base_axes=(0,), added_axes=(1,))
        h2 = conditional_information(support, base_axes=(0,), added_axes=(2,))
        h12 = conditional_information(support, base_axes=(0,), added_axes=(1, 2))
        eff1 = effective_conditional_states(support, base_axes=(0,), added_axes=(1,))
        eff2 = effective_conditional_states(support, base_axes=(0,), added_axes=(2,))
        eff12 = effective_conditional_states(support, base_axes=(0,), added_axes=(1, 2))
        _append_close(
            checks,
            family="conditional_independence_composition",
            case_id=case_id,
            property_name="conditional_information_additive",
            observed=h12,
            expected=h1 + h2,
            tolerance=5e-10,
        )
        _append_close(
            checks,
            family="conditional_independence_composition",
            case_id=case_id,
            property_name="effective_states_multiplicative",
            observed=eff12,
            expected=eff1 * eff2,
            tolerance=2e-9,
        )


def _run_independent_group_cases(checks: list[GeneralityCheck]) -> None:
    model = np.asarray([[3.0, 1.0], [1.0, 3.0]], dtype=float)
    same = model.copy()
    shifted = model[::-1].copy()

    reference = score_independent_groups(
        model,
        [("positive", same), ("shifted", shifted)],
        base_axes=(0,),
        added_axes=(1,),
        gain_tolerance=0.0,
    )
    reweighted = score_independent_groups(
        model * 10_000.0,
        [("positive", same * 1e-6), ("shifted", shifted * 1e8)],
        base_axes=(0,),
        added_axes=(1,),
        gain_tolerance=0.0,
    )
    checks.append(
        GeneralityCheck(
            family="independent_group_mass_invariance",
            case_id="mixed-two-groups",
            property_name="classification_not_changed_by_group_mass",
            passed=reference.classification == reweighted.classification == "mixed",
            absolute_error=0.0 if reference.classification == reweighted.classification == "mixed" else 1.0,
            tolerance=0.0,
        )
    )
    for index, (left, right) in enumerate(zip(reference.gains, reweighted.gains)):
        _append_close(
            checks,
            family="independent_group_mass_invariance",
            case_id="mixed-two-groups",
            property_name=f"group_{index}_gain_mass_invariant",
            observed=right,
            expected=left,
        )

    expected_mi = base_added_mutual_information(model, base_axes=(0,), added_axes=(1,))
    for group_count in (1, 3, 7):
        groups = [
            (f"group-{index}", same * (10.0 ** (index - 3)))
            for index in range(group_count)
        ]
        result = score_independent_groups(
            model,
            groups,
            base_axes=(0,),
            added_axes=(1,),
            gain_tolerance=0.0,
        )
        checks.append(
            GeneralityCheck(
                family="independent_group_count",
                case_id=f"same-process-{group_count}-groups",
                property_name="all_positive_groups_generalize",
                passed=result.classification == "generalizing",
                absolute_error=0.0 if result.classification == "generalizing" else 1.0,
                tolerance=0.0,
            )
        )
        for index, gain in enumerate(result.gains):
            _append_close(
                checks,
                family="independent_group_count",
                case_id=f"same-process-{group_count}-groups",
                property_name=f"group_{index}_gain_equals_information",
                observed=gain,
                expected=expected_mi,
            )


def run_n2_generality_benchmark(
    *,
    seed: int = DEFAULT_SEED,
    randomized_cases: int = DEFAULT_RANDOM_CASES,
) -> GeneralityBenchmarkResult:
    """Run deterministic generality proof obligations for the N2 generic core."""

    if randomized_cases < 1:
        raise ValueError("randomized_cases must be >= 1")
    rng = np.random.default_rng(int(seed))
    checks: list[GeneralityCheck] = []
    _run_randomized_invariance_cases(rng, checks, int(randomized_cases))
    _run_conditional_independence_cases(rng, checks)
    _run_independent_group_cases(checks)

    failed = [check for check in checks if not check.passed]
    max_error = max((check.absolute_error for check in checks), default=0.0)
    properties = tuple(sorted({check.family for check in checks}))
    return GeneralityBenchmarkResult(
        seed=int(seed),
        randomized_case_count=int(randomized_cases),
        check_count=len(checks),
        passed_count=len(checks) - len(failed),
        failed_count=len(failed),
        maximum_absolute_error=float(max_error),
        tensor_ndim_range=(2, 6),
        state_cardinality_range=(2, 5),
        properties=properties,
        checks=tuple(checks),
    )
