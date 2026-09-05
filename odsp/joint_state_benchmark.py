"""Known-truth validation for joint continuous-circular ODSP state prediction."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .joint_state import fit_joint_continuous_circular_state_model


@dataclass(frozen=True)
class JointStateBenchmarkFamily:
    family: str
    replicate_count: int
    mean_joint_gain: float
    minimum_joint_gain: float
    maximum_joint_gain: float
    positive_joint_gain_fraction: float
    negative_joint_gain_fraction: float
    mean_coupling_gain: float
    minimum_coupling_gain: float
    maximum_coupling_gain: float
    positive_coupling_gain_fraction: float
    negative_coupling_gain_fraction: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class JointStateBenchmarkResult:
    seed: int
    replicate_count: int
    training_rows: int
    heldout_rows: int
    period: float
    families: tuple[JointStateBenchmarkFamily, ...]
    stable_joint_all_positive: bool
    stable_coupling_all_positive: bool
    context_null_joint_mean_near_zero: bool
    uncoupled_coupling_mean_near_zero: bool
    context_shift_joint_all_negative: bool
    coupling_shift_coupling_all_negative: bool
    phase_origin_joint_gain_error: float
    phase_origin_coupling_gain_error: float
    period_unit_joint_gain_error: float
    period_unit_coupling_gain_error: float
    height_unit_joint_gain_error: float
    height_unit_coupling_gain_error: float
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "replicate_count": self.replicate_count,
            "training_rows": self.training_rows,
            "heldout_rows": self.heldout_rows,
            "period": self.period,
            "families": [row.as_dict() for row in self.families],
            "stable_joint_all_positive": self.stable_joint_all_positive,
            "stable_coupling_all_positive": self.stable_coupling_all_positive,
            "context_null_joint_mean_near_zero": self.context_null_joint_mean_near_zero,
            "uncoupled_coupling_mean_near_zero": self.uncoupled_coupling_mean_near_zero,
            "context_shift_joint_all_negative": self.context_shift_joint_all_negative,
            "coupling_shift_coupling_all_negative": self.coupling_shift_coupling_all_negative,
            "phase_origin_joint_gain_error": self.phase_origin_joint_gain_error,
            "phase_origin_coupling_gain_error": self.phase_origin_coupling_gain_error,
            "period_unit_joint_gain_error": self.period_unit_joint_gain_error,
            "period_unit_coupling_gain_error": self.period_unit_coupling_gain_error,
            "height_unit_joint_gain_error": self.height_unit_joint_gain_error,
            "height_unit_coupling_gain_error": self.height_unit_coupling_gain_error,
            "passed": self.passed,
        }


def _sample(
    rng: np.random.Generator,
    n: int,
    *,
    beta_time: np.ndarray,
    beta_height: np.ndarray,
    coupling: float,
    time_shift: float = 0.0,
    coupling_sign: float = 1.0,
    period: float = 24.0,
    time_kappa: float = 10.0,
    height_noise_sd: float = 0.45,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    X = rng.uniform(-1.0, 1.0, size=(n, beta_time.size))
    mean_angle = 1.0 + X @ beta_time + time_shift
    angle = rng.vonmises(mean_angle, time_kappa)
    time_state = np.mod(angle, 2.0 * np.pi) * period / (2.0 * np.pi)
    height = (
        2.5
        + X @ beta_height
        + coupling_sign * coupling * np.cos(angle - 0.4)
        + rng.normal(scale=height_noise_sd, size=n)
    )
    return X, height, time_state


def _summarize(
    family: str,
    joint_gains: list[float],
    coupling_gains: list[float],
) -> JointStateBenchmarkFamily:
    joint = np.asarray(joint_gains, dtype=float)
    coupling = np.asarray(coupling_gains, dtype=float)
    return JointStateBenchmarkFamily(
        family=family,
        replicate_count=int(joint.size),
        mean_joint_gain=float(np.mean(joint)),
        minimum_joint_gain=float(np.min(joint)),
        maximum_joint_gain=float(np.max(joint)),
        positive_joint_gain_fraction=float(np.mean(joint > 0.0)),
        negative_joint_gain_fraction=float(np.mean(joint < 0.0)),
        mean_coupling_gain=float(np.mean(coupling)),
        minimum_coupling_gain=float(np.min(coupling)),
        maximum_coupling_gain=float(np.max(coupling)),
        positive_coupling_gain_fraction=float(np.mean(coupling > 0.0)),
        negative_coupling_gain_fraction=float(np.mean(coupling < 0.0)),
    )


def _score_pair(model, sample):
    X, height, time_state = sample
    score = model.score(X, height, time_state)
    return score.mean_joint_log_density_gain, score.mean_coupling_log_density_gain


def run_joint_state_benchmark(
    *,
    seed: int = 20260905,
    replicates: int = 128,
    training_rows: int = 800,
    heldout_rows: int = 1600,
    period: float = 24.0,
) -> JointStateBenchmarkResult:
    if replicates < 1 or training_rows < 50 or heldout_rows < 50:
        raise ValueError("benchmark sizes are too small")
    rng = np.random.default_rng(seed)
    beta_time = np.array([0.55, -0.35], dtype=float)
    beta_height = np.array([0.9, -0.6], dtype=float)
    zero = np.zeros_like(beta_time)
    coupling = 1.1

    names = (
        "stable_context_and_coupling",
        "context_unorganized_but_coupled",
        "contextual_but_uncoupled",
        "context_shifted",
        "coupling_shifted",
    )
    store = {name: ([], []) for name in names}

    for _ in range(replicates):
        # Main stable model; reuse its frozen training fit for both shift tests.
        train = _sample(
            rng,
            training_rows,
            beta_time=beta_time,
            beta_height=beta_height,
            coupling=coupling,
            period=period,
        )
        stable_model = fit_joint_continuous_circular_state_model(
            *train, period=period
        )
        stable = _sample(
            rng,
            heldout_rows,
            beta_time=beta_time,
            beta_height=beta_height,
            coupling=coupling,
            period=period,
        )
        joint, cross = _score_pair(stable_model, stable)
        store["stable_context_and_coupling"][0].append(joint)
        store["stable_context_and_coupling"][1].append(cross)

        context_shift = _sample(
            rng,
            heldout_rows,
            beta_time=beta_time,
            beta_height=beta_height,
            coupling=coupling,
            time_shift=np.pi,
            period=period,
        )
        joint, cross = _score_pair(stable_model, context_shift)
        store["context_shifted"][0].append(joint)
        store["context_shifted"][1].append(cross)

        coupling_shift = _sample(
            rng,
            heldout_rows,
            beta_time=beta_time,
            beta_height=beta_height,
            coupling=coupling,
            coupling_sign=-1.0,
            period=period,
        )
        joint, cross = _score_pair(stable_model, coupling_shift)
        store["coupling_shifted"][0].append(joint)
        store["coupling_shifted"][1].append(cross)

        # Context-null but height-time coupling remains real.  X should add no
        # joint predictive value, while time can still improve height prediction.
        null_train = _sample(
            rng,
            training_rows,
            beta_time=zero,
            beta_height=zero,
            coupling=coupling,
            period=period,
        )
        null_model = fit_joint_continuous_circular_state_model(
            *null_train, period=period
        )
        null_test = _sample(
            rng,
            heldout_rows,
            beta_time=zero,
            beta_height=zero,
            coupling=coupling,
            period=period,
        )
        joint, cross = _score_pair(null_model, null_test)
        store["context_unorganized_but_coupled"][0].append(joint)
        store["context_unorganized_but_coupled"][1].append(cross)

        # Context is predictive but z has no additional dependence on realized t.
        uncoupled_train = _sample(
            rng,
            training_rows,
            beta_time=beta_time,
            beta_height=beta_height,
            coupling=0.0,
            period=period,
        )
        uncoupled_model = fit_joint_continuous_circular_state_model(
            *uncoupled_train, period=period
        )
        uncoupled_test = _sample(
            rng,
            heldout_rows,
            beta_time=beta_time,
            beta_height=beta_height,
            coupling=0.0,
            period=period,
        )
        joint, cross = _score_pair(uncoupled_model, uncoupled_test)
        store["contextual_but_uncoupled"][0].append(joint)
        store["contextual_but_uncoupled"][1].append(cross)

    families = tuple(_summarize(name, *store[name]) for name in names)
    by_name = {row.family: row for row in families}

    # Invariance checks on a larger stable sample.
    train = _sample(
        rng,
        3000,
        beta_time=beta_time,
        beta_height=beta_height,
        coupling=coupling,
        period=period,
    )
    test = _sample(
        rng,
        5000,
        beta_time=beta_time,
        beta_height=beta_height,
        coupling=coupling,
        period=period,
    )
    model = fit_joint_continuous_circular_state_model(*train, period=period)
    base = model.score(*test)

    phase_shift = 5.25
    phase_train = (train[0], train[1], np.mod(train[2] + phase_shift, period))
    phase_test = (test[0], test[1], np.mod(test[2] + phase_shift, period))
    phase_model = fit_joint_continuous_circular_state_model(
        *phase_train, period=period
    )
    phase_score = phase_model.score(*phase_test)

    unit_scale = 60.0
    minute_train = (train[0], train[1], train[2] * unit_scale)
    minute_test = (test[0], test[1], test[2] * unit_scale)
    minute_model = fit_joint_continuous_circular_state_model(
        *minute_train, period=period * unit_scale
    )
    minute_score = minute_model.score(*minute_test)

    height_scale = 4.5
    height_offset = -11.0
    height_train = (
        train[0],
        train[1] * height_scale + height_offset,
        train[2],
    )
    height_test = (
        test[0],
        test[1] * height_scale + height_offset,
        test[2],
    )
    height_model = fit_joint_continuous_circular_state_model(
        *height_train, period=period
    )
    height_score = height_model.score(*height_test)

    phase_joint_error = abs(
        base.mean_joint_log_density_gain - phase_score.mean_joint_log_density_gain
    )
    phase_coupling_error = abs(
        base.mean_coupling_log_density_gain - phase_score.mean_coupling_log_density_gain
    )
    unit_joint_error = abs(
        base.mean_joint_log_density_gain - minute_score.mean_joint_log_density_gain
    )
    unit_coupling_error = abs(
        base.mean_coupling_log_density_gain - minute_score.mean_coupling_log_density_gain
    )
    height_joint_error = abs(
        base.mean_joint_log_density_gain - height_score.mean_joint_log_density_gain
    )
    height_coupling_error = abs(
        base.mean_coupling_log_density_gain - height_score.mean_coupling_log_density_gain
    )

    stable = by_name["stable_context_and_coupling"]
    context_null = by_name["context_unorganized_but_coupled"]
    uncoupled = by_name["contextual_but_uncoupled"]
    context_shift = by_name["context_shifted"]
    coupling_shift = by_name["coupling_shifted"]

    stable_joint_all_positive = stable.positive_joint_gain_fraction == 1.0
    stable_coupling_all_positive = stable.positive_coupling_gain_fraction == 1.0
    context_null_near_zero = abs(context_null.mean_joint_gain) < 0.02
    uncoupled_near_zero = abs(uncoupled.mean_coupling_gain) < 0.02
    context_shift_all_negative = context_shift.negative_joint_gain_fraction == 1.0
    coupling_shift_all_negative = coupling_shift.negative_coupling_gain_fraction == 1.0
    passed = bool(
        stable_joint_all_positive
        and stable_coupling_all_positive
        and context_null_near_zero
        and uncoupled_near_zero
        and context_shift_all_negative
        and coupling_shift_all_negative
        and phase_joint_error <= 1e-10
        and phase_coupling_error <= 1e-10
        and unit_joint_error <= 1e-10
        and unit_coupling_error <= 1e-10
        and height_joint_error <= 1e-10
        and height_coupling_error <= 1e-10
    )
    return JointStateBenchmarkResult(
        seed=int(seed),
        replicate_count=int(replicates),
        training_rows=int(training_rows),
        heldout_rows=int(heldout_rows),
        period=float(period),
        families=families,
        stable_joint_all_positive=stable_joint_all_positive,
        stable_coupling_all_positive=stable_coupling_all_positive,
        context_null_joint_mean_near_zero=context_null_near_zero,
        uncoupled_coupling_mean_near_zero=uncoupled_near_zero,
        context_shift_joint_all_negative=context_shift_all_negative,
        coupling_shift_coupling_all_negative=coupling_shift_all_negative,
        phase_origin_joint_gain_error=float(phase_joint_error),
        phase_origin_coupling_gain_error=float(phase_coupling_error),
        period_unit_joint_gain_error=float(unit_joint_error),
        period_unit_coupling_gain_error=float(unit_coupling_error),
        height_unit_joint_gain_error=float(height_joint_error),
        height_unit_coupling_gain_error=float(height_coupling_error),
        passed=passed,
    )
