"""Cross-geometry benchmark for the ODSP distributional gain core.

The older N2 generality benchmark establishes representation genericity within
finite discrete support tensors.  This benchmark asks a different question:
does the same held-out estimand survive a change in the *geometry of the ecological
state itself*?

Four state spaces are exercised through their native ODSP implementations:

* finite discrete state probabilities;
* a continuous scalar Gaussian density;
* a circular von Mises density;
* a joint continuous-circular density.

For each geometry, the native scorer must agree with the state-space agnostic
``score_distributional_gain`` implementation.  The benchmark also verifies that
a common row-wise reference-measure shift cancels from the gain and that the same
independent-group sign rule is used without pooling observation mass.

This is an implementation and estimand benchmark.  It does not make a biological
axis meaningful, representative, causal or transferable by itself.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .circular_state import fit_von_mises_circular_state_model
from .continuous_state import fit_gaussian_continuous_state_model
from .distributional_gain import score_distributional_gain, score_distributional_groups
from .joint_state import fit_joint_continuous_circular_state_model
from .state_prediction import score_state_probability_field


ABS_TOL = 2e-10


@dataclass(frozen=True)
class StateSpaceGeneralityCheck:
    state_space: str
    property_name: str
    passed: bool
    absolute_error: float
    tolerance: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StateSpaceGeneralityBenchmarkResult:
    check_count: int
    passed_count: int
    failed_count: int
    maximum_absolute_error: float
    state_spaces: tuple[str, ...]
    common_estimand: str
    checks: tuple[StateSpaceGeneralityCheck, ...]

    @property
    def passed(self) -> bool:
        return self.failed_count == 0

    def as_dict(self) -> dict[str, object]:
        return {
            "check_count": self.check_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "maximum_absolute_error": self.maximum_absolute_error,
            "state_spaces": list(self.state_spaces),
            "common_estimand": self.common_estimand,
            "passed": self.passed,
            "checks": [check.as_dict() for check in self.checks],
        }


def _append_close(
    checks: list[StateSpaceGeneralityCheck],
    *,
    state_space: str,
    property_name: str,
    observed: float,
    expected: float,
    tolerance: float = ABS_TOL,
) -> None:
    if observed == expected:
        error = 0.0
    elif math.isfinite(observed) and math.isfinite(expected):
        error = abs(float(observed) - float(expected))
    else:
        error = float("inf")
    checks.append(
        StateSpaceGeneralityCheck(
            state_space=state_space,
            property_name=property_name,
            passed=bool(error <= tolerance),
            absolute_error=float(error),
            tolerance=float(tolerance),
        )
    )


def _check_reference_shift(
    checks: list[StateSpaceGeneralityCheck],
    *,
    state_space: str,
    conditional: np.ndarray,
    baseline: np.ndarray,
    weights: np.ndarray,
) -> None:
    original = score_distributional_gain(
        conditional, baseline, sample_weight=weights
    ).mean_log_score_gain
    # A reference-measure/Jacobian term may vary by realized row.  If the same
    # term is added to both logarithmic scores it must cancel pointwise.
    shift = np.linspace(-1.75, 2.25, conditional.size, dtype=float)
    shifted = score_distributional_gain(
        conditional + shift,
        baseline + shift,
        sample_weight=weights,
    ).mean_log_score_gain
    _append_close(
        checks,
        state_space=state_space,
        property_name="common_reference_measure_shift_invariant",
        observed=shifted,
        expected=original,
    )


def _discrete_case(checks: list[StateSpaceGeneralityCheck]) -> None:
    conditional = np.asarray([[0.84, 0.16], [0.27, 0.73]], dtype=float)
    marginal = np.asarray([0.55, 0.45], dtype=float)
    heldout = np.asarray([[8.0, 2.0], [2.5, 7.5]], dtype=float)
    native = score_state_probability_field(
        conditional,
        heldout,
        base_ndim=1,
        marginal_probability=marginal,
    )
    conditional_log = np.log(conditional).reshape(-1)
    baseline_log = np.broadcast_to(marginal, conditional.shape)
    baseline_log = np.log(baseline_log).reshape(-1)
    weights = heldout.reshape(-1)
    generic = score_distributional_gain(
        conditional_log,
        baseline_log,
        sample_weight=weights,
    )
    _append_close(
        checks,
        state_space="finite_discrete",
        property_name="native_and_generic_gain_agree",
        observed=generic.mean_log_score_gain,
        expected=native.mean_log_score_gain,
    )
    _check_reference_shift(
        checks,
        state_space="finite_discrete",
        conditional=conditional_log,
        baseline=baseline_log,
        weights=weights,
    )


def _continuous_case(checks: list[StateSpaceGeneralityCheck]) -> None:
    x1 = np.linspace(-2.0, 2.0, 20)
    x2 = np.cos(np.linspace(0.1, 2.7, 20))
    X = np.column_stack([x1, x2])
    residual = 0.18 * np.sin(np.arange(20) * 1.7)
    y = 1.4 + 0.75 * x1 - 0.35 * x2 + residual
    model = fit_gaussian_continuous_state_model(X, y)

    hx1 = np.asarray([-1.7, -0.9, -0.2, 0.45, 1.1, 1.8])
    hx2 = np.asarray([0.82, 0.44, -0.11, -0.54, -0.78, -0.91])
    heldout_X = np.column_stack([hx1, hx2])
    heldout_y = 1.4 + 0.75 * hx1 - 0.35 * hx2 + np.asarray(
        [0.05, -0.08, 0.12, -0.04, 0.07, -0.03]
    )
    weights = np.asarray([1.0, 2.0, 1.5, 0.7, 1.2, 2.4])
    native = model.score(heldout_X, heldout_y, sample_weight=weights)
    conditional_log = model.predict_log_density(heldout_X, heldout_y)
    baseline_log = model.marginal_log_density(heldout_y)
    generic = score_distributional_gain(
        conditional_log,
        baseline_log,
        sample_weight=weights,
    )
    _append_close(
        checks,
        state_space="continuous_scalar",
        property_name="native_and_generic_gain_agree",
        observed=generic.mean_log_score_gain,
        expected=native.mean_log_density_gain,
    )
    _check_reference_shift(
        checks,
        state_space="continuous_scalar",
        conditional=conditional_log,
        baseline=baseline_log,
        weights=weights,
    )


def _circular_case(checks: list[StateSpaceGeneralityCheck]) -> None:
    x = np.linspace(-1.6, 1.6, 24)
    X = np.column_stack([x, np.sin(x)])
    state = np.mod(
        8.5 + 2.8 * x + 0.55 * np.sin(np.arange(24) * 1.3),
        24.0,
    )
    model = fit_von_mises_circular_state_model(X, state, period=24.0)

    hx = np.asarray([-1.35, -0.72, -0.05, 0.52, 1.02, 1.43])
    heldout_X = np.column_stack([hx, np.sin(hx)])
    heldout_state = np.mod(
        8.5 + 2.8 * hx + np.asarray([0.16, -0.22, 0.11, -0.13, 0.18, -0.08]),
        24.0,
    )
    weights = np.asarray([1.0, 0.8, 1.7, 1.1, 2.0, 1.4])
    native = model.score(heldout_X, heldout_state, sample_weight=weights)
    conditional_log = model.predict_log_density(heldout_X, heldout_state)
    baseline_log = model.marginal_log_density(heldout_state)
    generic = score_distributional_gain(
        conditional_log,
        baseline_log,
        sample_weight=weights,
    )
    _append_close(
        checks,
        state_space="circular_scalar",
        property_name="native_and_generic_gain_agree",
        observed=generic.mean_log_score_gain,
        expected=native.mean_log_density_gain,
    )
    _check_reference_shift(
        checks,
        state_space="circular_scalar",
        conditional=conditional_log,
        baseline=baseline_log,
        weights=weights,
    )


def _joint_case(checks: list[StateSpaceGeneralityCheck]) -> None:
    x1 = np.linspace(-1.8, 1.8, 30)
    x2 = np.cos(np.linspace(0.0, 3.2, 30))
    X = np.column_stack([x1, x2])
    time_state = np.mod(
        7.0 + 2.4 * x1 + 0.45 * np.sin(np.arange(30) * 1.1),
        24.0,
    )
    angle = 2.0 * np.pi * time_state / 24.0
    height = (
        120.0
        + 24.0 * x1
        - 9.0 * x2
        + 13.0 * np.sin(angle)
        + 2.5 * np.cos(np.arange(30) * 0.9)
    )
    model = fit_joint_continuous_circular_state_model(
        X,
        height,
        time_state,
        period=24.0,
    )

    hx1 = np.asarray([-1.45, -0.83, -0.28, 0.34, 0.91, 1.51])
    hx2 = np.asarray([0.91, 0.67, 0.21, -0.28, -0.71, -0.96])
    heldout_X = np.column_stack([hx1, hx2])
    heldout_time = np.mod(
        7.0 + 2.4 * hx1 + np.asarray([0.18, -0.14, 0.09, -0.11, 0.16, -0.07]),
        24.0,
    )
    heldout_angle = 2.0 * np.pi * heldout_time / 24.0
    heldout_height = (
        120.0
        + 24.0 * hx1
        - 9.0 * hx2
        + 13.0 * np.sin(heldout_angle)
        + np.asarray([1.2, -1.6, 0.8, -0.7, 1.4, -1.0])
    )
    weights = np.asarray([1.0, 1.5, 0.9, 1.8, 1.2, 2.1])
    native = model.score(
        heldout_X,
        heldout_height,
        heldout_time,
        sample_weight=weights,
    )
    conditional_log = model.joint_log_density(
        heldout_X, heldout_height, heldout_time
    )
    baseline_log = model.marginal_joint_log_density(heldout_height, heldout_time)
    generic = score_distributional_gain(
        conditional_log,
        baseline_log,
        sample_weight=weights,
    )
    _append_close(
        checks,
        state_space="continuous_x_circular_joint",
        property_name="native_and_generic_gain_agree",
        observed=generic.mean_log_score_gain,
        expected=native.mean_joint_log_density_gain,
    )
    _check_reference_shift(
        checks,
        state_space="continuous_x_circular_joint",
        conditional=conditional_log,
        baseline=baseline_log,
        weights=weights,
    )


def _group_rule_case(checks: list[StateSpaceGeneralityCheck]) -> None:
    mixed = score_distributional_groups(
        [
            ("positive", [-0.15, -0.12], [-0.30, -0.28]),
            ("negative", [-0.42, -0.39], [-0.31, -0.30]),
        ]
    )
    all_positive = score_distributional_groups(
        {
            "g1": ([-0.10, -0.11], [-0.20, -0.21]),
            "g2": ([-0.22, -0.18], [-0.29, -0.26]),
        }
    )
    checks.append(
        StateSpaceGeneralityCheck(
            state_space="independent_group_rule",
            property_name="conflicting_groups_remain_mixed",
            passed=mixed.gain_category == "mixed",
            absolute_error=0.0 if mixed.gain_category == "mixed" else 1.0,
            tolerance=0.0,
        )
    )
    checks.append(
        StateSpaceGeneralityCheck(
            state_space="independent_group_rule",
            property_name="all_positive_groups_are_generalizing",
            passed=all_positive.gain_category == "generalizing",
            absolute_error=0.0 if all_positive.gain_category == "generalizing" else 1.0,
            tolerance=0.0,
        )
    )


def run_state_space_generality_benchmark() -> StateSpaceGeneralityBenchmarkResult:
    checks: list[StateSpaceGeneralityCheck] = []
    _discrete_case(checks)
    _continuous_case(checks)
    _circular_case(checks)
    _joint_case(checks)
    _group_rule_case(checks)
    failures = [check for check in checks if not check.passed]
    finite_errors = [
        check.absolute_error for check in checks if math.isfinite(check.absolute_error)
    ]
    return StateSpaceGeneralityBenchmarkResult(
        check_count=len(checks),
        passed_count=len(checks) - len(failures),
        failed_count=len(failures),
        maximum_absolute_error=max(finite_errors, default=0.0),
        state_spaces=(
            "finite_discrete",
            "continuous_scalar",
            "circular_scalar",
            "continuous_x_circular_joint",
        ),
        common_estimand=(
            "E_heldout[log q_train(A|X) - log q0_train(A)] evaluated under a shared reference measure"
        ),
        checks=tuple(checks),
    )
