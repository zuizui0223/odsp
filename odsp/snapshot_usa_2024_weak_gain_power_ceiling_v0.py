"""Theory-only upper bound on certification probability for frozen e-betting IUT.

For independent identically distributed block gains with true mean mu and
lower support L, expected fixed-bet factor is
1+lambda*(mu-tolerance)/(tolerance-L). Product expectations factorize.
For an arithmetic mixture of products, Markov implies
P(E_mix>1/a) <= a * mean_lambda(expected_factor(lambda)^B).
No variance or normality assumption is needed for this upper bound.

If EACH independent process refit has a weakest required cell whose true
mean is at most mu, then P(refit certified) <= u. Regardless of the
dependence of certificates through shared V, E[K] <= R*u, so
P(K>=K_min) <= min(1,R*u/K_min). These are conditional theoretical
power bounds, not empirical results, and do not prove iid site sampling.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

MIX=(0.25,0.5,0.75,1.0)
TEST_ALPHA=0.002
DELTA=0.025
PROCESS_ALPHA=0.025


def _tail(k:int,n:int,p:float)->float:
    if k<=0: return 1.
    if k>n or p<=0: return 0.
    if p>=1: return 1.
    coeff=math.lgamma(n+1)
    terms=[
        coeff-math.lgamma(j+1)-math.lgamma(n-j+1)
        +j*math.log(p)+(n-j)*math.log1p(-p)
        for j in range(k,n+1)
    ]
    top=max(terms)
    return min(1.,math.exp(top)*math.fsum(math.exp(x-top) for x in terms))


def _cp_lower(k:int,n:int,alpha:float)->float:
    if k==0: return 0.
    if k==n: return alpha**(1/n)
    lo,hi=0.,k/n
    for _ in range(90):
        mid=(lo+hi)/2
        if _tail(k,n,mid)<alpha: lo=mid
        else: hi=mid
    return (lo+hi)/2


def min_certificates_for_q(R:int,q:float=0.8)->int|None:
    if isinstance(R,bool) or not isinstance(R,int) or R<1 or not 0<q<1:
        raise ValueError("R must be positive integer and q in (0,1)")
    c=TEST_ALPHA/DELTA
    return next((
        k for k in range(1,R+1)
        if (_cp_lower(k,R,PROCESS_ALPHA)-c)/(1-c)>q
    ),None)


def fixed_betting_component_power_upper(
    B:int,
    mu:float,
    *,
    L:float=-1.,
    tolerance:float=0.,
    a:float=TEST_ALPHA,
)->float:
    """A genuine alternative distribution-free upper bound given iid blocks.

    Requires an upper ceiling on the true block-uniform population mean,
    each block score bounded below by L, and the fixed mixture fractions.
    """
    if isinstance(B,bool) or not isinstance(B,int) or B<1:
        raise ValueError("B must be a positive integer")
    if any(not math.isfinite(v) for v in (mu,L,tolerance,a)):
        raise ValueError("nonfinite bound input")
    if not L<tolerance or mu<L or not 0<a<1:
        raise ValueError("invalid gain support or alpha")
    z=(mu-tolerance)/(tolerance-L)
    logs=[]
    for lam in MIX:
        factor=1+lam*z
        if factor<0: raise ValueError("expected betting factor negative")
        logs.append(-math.inf if factor==0 else B*math.log(factor))
    top=max(logs)
    if top == -math.inf: return 0.
    log_expectation=top+math.log(
        math.fsum(math.exp(x-top) for x in logs)/len(logs))
    log_upper=math.log(a)+log_expectation
    return 1. if log_upper>=0 else math.exp(log_upper)


@dataclass(frozen=True)
class WeakGainDesignCeiling:
    published_total_arrays:int
    reported_forest_fraction:float
    rounding_half_width:float
    max_nonforest_arrays_under_rounding:int
    grassland_arrays_upper_bound:int
    iid_array_blocks_assumed_not_verified:bool
    weak_mean_gain_cap:float
    refit_count:int
    required_certified_for_q:int|None
    single_refit_certification_power_upper_bound:float
    q_decision_power_upper_bound:float
    post_statistical_panel_design_theory_only:bool
    actual_deployment_rows_read:bool
    ecological_prediction_claim:bool
    original_routes_reclassified:bool

    def as_dict(self)->dict[str,object]:
        return asdict(self)


def snapshot_usa_2024_weak_gain_ceiling(
    *,
    R:int=20,
    gain_cap:float=0.05,
    total_arrays:int=184,
    rounded_forest_fraction:float=0.77,
    half_rounding_interval:float=0.005,
)->WeakGainDesignCeiling:
    """Conditional design argument from public article aggregate counts.

    If 77% is nearest-whole-percent rounding, forest fraction >=0.765,
    giving <=43 nonforest arrays among 184. Grassland is a subset.
    Actual array independence and weak-gain assumption remain UNVERIFIED.
    """
    if isinstance(total_arrays,bool) or not isinstance(total_arrays,int) or total_arrays<1:
        raise ValueError("total_arrays must be positive integer")
    if not(0<half_rounding_interval<rounded_forest_fraction<1-half_rounding_interval):
        raise ValueError("invalid percentage rounding")
    if not math.isfinite(gain_cap) or gain_cap < -1.:
        raise ValueError("invalid gain cap")
    B=math.floor(total_arrays*(1-(rounded_forest_fraction-half_rounding_interval))+1e-12)
    power=fixed_betting_component_power_upper(B,gain_cap)
    k=min_certificates_for_q(R)
    return WeakGainDesignCeiling(
        published_total_arrays=total_arrays,
        reported_forest_fraction=rounded_forest_fraction,
        rounding_half_width=half_rounding_interval,
        max_nonforest_arrays_under_rounding=B,
        grassland_arrays_upper_bound=B,
        iid_array_blocks_assumed_not_verified=True,
        weak_mean_gain_cap=gain_cap,
        refit_count=R,
        required_certified_for_q=k,
        single_refit_certification_power_upper_bound=power,
        q_decision_power_upper_bound=(0. if k is None else min(1.,R*power/k)),
        post_statistical_panel_design_theory_only=True,
        actual_deployment_rows_read=False,
        ecological_prediction_claim=False,
        original_routes_reclassified=False,
    )
