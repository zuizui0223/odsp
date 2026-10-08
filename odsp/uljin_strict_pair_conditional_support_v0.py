"""Source-free analytical feasibility screen for strict paired-label conditional tests.

The published independent-event totals cover the whole released year, NOT
the 41 matched 2022 calendar date pairs. These explicit hypothetical
retention fractions must never be confused with known real study coverage.

For N events independently assigned to G site-pairs and assigned to the
two branches with probabilities f/(2G) each, the expected number of
site-pairs with at least one detection on BOTH branches is exactly

  G * [1 - 2(1 - f/(2G))**N + (1 - f/G)**N].

This is a necessary (not sufficient) condition for per-site-pair exact
phase-label shuffling that holds branch totals fixed. In contrast, a
ONE-SIDED detection can still inform the existing pooled conditional-
Poisson beta-bin parameters if both device exposures are >0. Thus the
diagnostic is NOT a power ceiling for that existing ODSP model.
"""
from __future__ import annotations

import math
from typing import Mapping

ID="uljin_41pair_strict_conditional_support_feasibility_v0"
SITES=82
PAIRS=41
G=SITES*PAIRS
TAXA={"goral":2317,"water_deer":814,"roe_deer":808,"wild_boar":684}
RETAIN=(1.,.25,.10)


def _check_plan(plan:Mapping[str,object])->None:
    pub=plan.get("public_benchmark_only",{})
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=ID
        or plan.get("stage")!="FROZEN_ANALYTIC_SOURCE_FREE_BEFORE_FIRST_SUPPORT_OUTPUT"
        or pub.get("published_yearwide_independent_event_counts")!=TAXA
        or pub.get("published_site_count")!=SITES
        or pub.get("originally_predeclared_pair_count")!=PAIRS
        or pub.get("raw_event_rows_read") is not False
        or plan.get("selected_day_event_retention_scenarios")!=list(RETAIN)
        or not any("one-sided detection" in s.lower()
                   for s in plan.get("scientific_guardrails",[]))
    ):
        raise ValueError("frozen source-free conditional support contract changed")


def _validate(N:int, fraction:float, groups:int)->None:
    if (type(N) is not int or N<0
        or type(groups) is not int or groups<=0
        or isinstance(fraction,bool)
        or not isinstance(fraction,(int,float))
        or not math.isfinite(fraction)
        or not 0.<=fraction<=1.):
        raise ValueError("invalid event total, retention or group count")


def expected_both_branches(N:int, fraction:float, groups:int=G)->float:
    """Exact fixed-N multinomial occupancy expectation, not Poisson approximation."""
    _validate(N,fraction,groups)
    if N<2 or fraction==0.:
        return 0.
    x=float(fraction)/groups
    # Numerically stable cancellation-safe expression for tiny x.
    log_both_missing=(-math.inf if x==1. else math.log1p(-x))
    ans=groups*(-2.*math.expm1(N*math.log1p(-x/2.))
                +math.expm1(N*log_both_missing))
    if not -1e-8 <= ans <= groups + 1e-8:
        raise ValueError("inconsistent strict paired-support expectation")
    return max(0.,min(float(groups),ans))


def expected_at_least_two_any_branch(
    N:int,fraction:float,groups:int=G,
)->float:
    """Site-pair groups with >=2 events, irrespective of branch."""
    _validate(N,fraction,groups)
    if N<2 or fraction==0.:
        return 0.
    x=float(fraction)/groups
    logq=(-math.inf if x==1. else math.log1p(-x))
    prob=-math.expm1(N*logq)-N*x*math.exp((N-1)*logq)
    if not -1e-8 <= prob <= 1+1e-8:
        raise ValueError("invalid occupancy ≥2 probability")
    return groups*max(0.,min(1.,prob))


def run_strict_pair_support_screen(plan:Mapping[str,object])->dict[str,object]:
    _check_plan(plan)
    cases=[]
    for taxon,N in (*TAXA.items(),("all_four_pooled",sum(TAXA.values()))):
        for f in RETAIN:
            needed=expected_both_branches(N,f)
            two=expected_at_least_two_any_branch(N,f)
            cases.append({
                "taxon":taxon,
                "full_year_published_event_count":N,
                "assumed_fraction_of_events_retained":f,
                "expected_both_branch_site_pair_groups":needed,
                "expected_any_branch_two_plus_site_pair_groups":two,
                "both_branch_fraction_of_3362_groups":needed/G,
                "total_physical_site_pair_groups":G,
                "combinatorial_upper_bound_at_all_year_counts":N//2,
                "real_observed_both_branch_groups_known":False,
                "strict_phase_permutation_information_certified":False,
            })
    return {
        "schema_version":1,
        "method":ID,
        "status":"SOURCE_FREE_IDEALIZED_STRICT_PAIR_SUPPORT_ONLY",
        "published_event_total_pooled":sum(TAXA.values()),
        "nominal_site_pair_group_count":G,
        "cases":cases,
        "this_is_not_a_pooled_conditional_poisson_power_bound":True,
        "single_branch_observations_still_inform_pooled_conditional_poisson":True,
        "actual_source_events_opened":False,
        "original_camera_uptime_records_verified":False,
        "original_ODSP_primary_routes_reclassified":False,
    }
