"""A nonparametric indistinguishability bound for weak positive block means.

This is DESIGN THEORY, independent of the experimental ODSP e-IUT test.
It does not infer an effect from Snapshot USA observations.

Let iid validation-block gains lie in [L,U]. Compare a point alternative
P1(X=d)=1, d>tau, with a legitimate boundary-null distribution
P0(X=d)=(tau-L)/(d-L), P0(X=L)=1-P0(X=d).
Both are iid distributions supported by [L,U], and E0[X]=tau.

Under the alternative the B-vector is always (d,...,d). Under P0 this
same B-vector has probability p0**B. Therefore any size-alpha test
phi(x) in [0,1] for the full distribution-free null must obey:
 phi(d,...,d) <= min(1,alpha/p0**B).

For a nonrandomized test, phi is 0 or 1. If p0**B > alpha, the
point alternative MUST have power zero. This is a theorem about testing
with no further variance/shape assumptions, not a statement about the
actual empirical gain or iid legitimacy of any camera array.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math


@dataclass(frozen=True)
class PointAlternativeTestingBarrier:
    schema_version: int
    block_count: int
    score_lower_bound: float
    score_upper_bound: float
    one_sided_null_threshold: float
    constant_positive_gain: float
    component_test_alpha: float
    null_mass_at_positive_gain: float
    null_mass_at_score_lower_bound: float
    null_probability_of_all_positive_blocks: float
    max_randomized_power_for_any_distribution_free_level_alpha_test: float
    any_nonrandomized_level_alpha_test_can_reject_all_positive_blocks: bool
    minimum_iid_blocks_per_group_to_allow_nonrandomized_point_alternative_rejection: int
    observational_result: bool
    assumes_iid_physical_blocks: bool
    ecological_sampling_iid_verified: bool
    applies_only_to_particular_constant_gain_alternative: bool
    existing_methods_or_empirical_endpoints_reclassified: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def point_alternative_distribution_free_barrier(
    blocks: int,
    constant_positive_gain: float,
    *,
    score_lower_bound: float = -1.0,
    score_upper_bound: float = 1.0,
    null_threshold: float = 0.0,
    component_test_alpha: float = 0.002,
) -> PointAlternativeTestingBarrier:
    """Exact two-point-null contamination argument (not a simulation)."""
    if isinstance(blocks, bool) or not isinstance(blocks, int) or blocks < 1:
        raise ValueError("blocks must be a positive integer")
    values = (
        constant_positive_gain, score_lower_bound,
        score_upper_bound, null_threshold, component_test_alpha,
    )
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not math.isfinite(float(v)) for v in values):
        raise ValueError("inputs must be finite numeric")
    d, L, U, tau, alpha = map(float, values)
    if not L < tau < d <= U:
        raise ValueError("require lower bound < null threshold < positive gain <= upper bound")
    if not 0.0 < alpha < 1.0:
        raise ValueError("component_test_alpha must lie in (0,1)")
    p0 = (tau - L) / (d - L)
    log_probability = blocks * math.log(p0)
    null_event_prob = math.exp(log_probability)
    log_upper = math.log(alpha) - log_probability
    randomized_power_max = 1.0 if log_upper >= 0.0 else math.exp(log_upper)
    allowed_nonrandomized = log_probability <= math.log(alpha)
    minimum_blocks = math.ceil(math.log(alpha) / math.log(p0))
    # Exact boundary could be affected by last-bit rounding;
    # enforce the strict power-zero condition using computed log values.
    while minimum_blocks > 1 and (minimum_blocks-1)*math.log(p0) <= math.log(alpha):
        minimum_blocks -= 1
    while minimum_blocks*math.log(p0) > math.log(alpha):
        minimum_blocks += 1
    return PointAlternativeTestingBarrier(
        schema_version=1,
        block_count=blocks,
        score_lower_bound=L,
        score_upper_bound=U,
        one_sided_null_threshold=tau,
        constant_positive_gain=d,
        component_test_alpha=alpha,
        null_mass_at_positive_gain=p0,
        null_mass_at_score_lower_bound=1-p0,
        null_probability_of_all_positive_blocks=null_event_prob,
        max_randomized_power_for_any_distribution_free_level_alpha_test=randomized_power_max,
        any_nonrandomized_level_alpha_test_can_reject_all_positive_blocks=allowed_nonrandomized,
        minimum_iid_blocks_per_group_to_allow_nonrandomized_point_alternative_rejection=minimum_blocks,
        observational_result=False,
        assumes_iid_physical_blocks=True,
        ecological_sampling_iid_verified=False,
        applies_only_to_particular_constant_gain_alternative=True,
        existing_methods_or_empirical_endpoints_reclassified=False,
    )
