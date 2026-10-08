"""Exact minimal supplemental count release for the frozen 2x2x6 fiber.

This is a DESIGN calculation on the already disclosed synthetic full-table
ambiguity, not a new general theorem, animal observation, or confidence
interval. Search ALL 2^6 subsets of previously withheld EARLY-site RISING
season phase-bin counts, conditioning on all three original pairwise margins.

Measurement budgets for different targets need not be the same:
reconstruct a 24-cell table versus identify one odds ratio versus its sign.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from fractions import Fraction
from itertools import combinations, product
import numpy as np

from .uljin_threeway_margin_identifiability_v0 import (
    WORLD_A, WORLD_B, two_way_margins, marginalization_matrix
)
from .uljin_threeway_margin_fiber_bounds_v1 import (
    early_log_odds_ratio,reconstruct_from_early_rise
)

METHOD="uljin_minimal_threeway_measurement_design_v0"
CANDIDATES=tuple(range(6))
PARENT_COUNT=2723


def _validate_frozen(plan:Mapping[str,object],ledger:Mapping[str,object])->None:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
            "FROZEN_POST_PARENT_FIBER_RESULTS_BEFORE_FIRST_SUPPLEMENTAL_DESIGN_RESULT"
        or plan.get("parent_pr")!=240
        or plan.get("parent_contract")!=
            "ULJIN_THREEWAY_MARGIN_FIBER_BOUNDS_V1_CONTRACT.json"
        or plan.get("parent_first_result")!=
            "ULJIN_THREEWAY_MARGIN_FIBER_BOUNDS_V1_FIRST_RESULT_LEDGER.json"
        or plan.get("candidate_supplemental_measurement")!=
            "Exact early-site × rising-branch count in each of six labeled solar-phase bins; each query is ONE previously withheld three-way cell"
        or plan.get("design_space")!=
            "ALL 64 subsets of six candidate cells, no candidate cherry-picking"
        or plan.get("strict_assumptions",{}).get(
            "positive_integer_cells_at_least")!=1
        or plan.get("strict_assumptions",{}).get(
            "fix_original_parent_three_pairwise_margins") is not True
        or plan.get("source_access")!={
            "EcoBank_animal_events":False,
            "real_device_uptime":False,
            "protected_station_coordinates":False
        }
        or ledger.get("record_type")!=
            "FIRST_PRE_FROZEN_THREEWAY_POSITIVE_INTEGER_FIBER_BOUNDS_V1_TERMINAL_RESULT"
        or ledger.get("first_method_ci_run")!=37792974347
        or ledger.get("frozen_positive_integer_complete_table_count")!=PARENT_COUNT
        or ledger.get("interval_crosses_one") is not True
    ):
        raise ValueError("frozen minimal measurement design or parent evidence changed")


def enumerate_original_fiber()->list[tuple[tuple[int,...],Fraction,int]]:
    """Exact integer enumeration, no stochastic generation or data access."""
    m=two_way_margins(WORLD_A)
    lower=[max(1,int(m["branch_phase"][0,k]-m["site_phase"][1,k]+1))
           for k in range(6)]
    upper=[min(int(m["site_phase"][0,k]-1),int(m["branch_phase"][0,k]-1))
           for k in range(6)]
    target=int(m["site_branch"][0,0])
    items=[]
    for first_five in product(*(range(lower[k],upper[k]+1) for k in range(5))):
        last=target-sum(first_five)
        if not lower[5]<=last<=upper[5]:
            continue
        x=tuple(map(int,first_five))+(int(last),)
        table=reconstruct_from_early_rise(x,m)
        ratio,_,sign=early_log_odds_ratio(table)
        items.append((x,ratio,sign))
    if (len(items)!=PARENT_COUNT
        or tuple(map(int,WORLD_A[0,0])) not in {x for x,_,_ in items}
        or tuple(map(int,WORLD_B[0,0])) not in {x for x,_,_ in items}):
        raise ValueError("parent integer fiber count or original worlds did not replay")
    return items


def _all_subsets()->list[tuple[int,...]]:
    return [subset for size in range(7)
            for subset in combinations(CANDIDATES,size)]


def evaluate_all_minimal_measurements(
    plan:Mapping[str,object],parent_ledger:Mapping[str,object]
)->dict[str,object]:
    _validate_frozen(plan,parent_ledger)
    universe=enumerate_original_fiber()
    full_keys={x for x,_,_ in universe}
    if len(full_keys)!=len(universe):
        raise ValueError("original full table count not unique")
    base=marginalization_matrix()
    summaries=[]
    minimum={"sign":None,"exact_odds_ratio":None,"full_table":None}
    universal_identifiers={"sign":[],"exact_odds_ratio":[],"full_table":[]}
    single_measurement_details=[]
    for selected in _all_subsets():
        observed_classes=defaultdict(list)
        for x,ratio,sign in universe:
            observed_classes[tuple(x[i] for i in selected)].append((x,ratio,sign))
        num_classes=len(observed_classes)
        sign_ambiguous=0
        ratio_ambiguous=0
        table_ambiguous=0
        sign_unresolved_candidates=0
        distinct_sign_ambiguous_outputs=[]
        for key,worlds in observed_classes.items():
            distinct_signs={w[2] for w in worlds}
            distinct_ratios={w[1] for w in worlds}
            if len(distinct_signs)>1:
                sign_ambiguous+=1
                sign_unresolved_candidates+=len(worlds)
                if len(selected)==1:
                    distinct_sign_ambiguous_outputs.append(list(key))
            if len(distinct_ratios)>1:
                ratio_ambiguous+=1
            if len(worlds)>1:
                table_ambiguous+=1
        extra=np.eye(24,dtype=np.int64)[list(selected)] if selected else np.empty((0,24),dtype=np.int64)
        rank=int(np.linalg.matrix_rank(np.vstack([base,extra])))
        singleton_full=table_ambiguous==0
        singleton_ratio=ratio_ambiguous==0
        singleton_sign=sign_ambiguous==0
        if rank==24 and not singleton_full:
            raise ValueError("full-rank supplemental release failed exact reconstruction")
        features={"sign":singleton_sign,
                  "exact_odds_ratio":singleton_ratio,
                  "full_table":singleton_full}
        for target,identified in features.items():
            if identified:
                universal_identifiers[target].append(list(selected))
                if minimum[target] is None:
                    minimum[target]=len(selected)
        row={
            "additional_early_rising_phase_bins":list(selected),
            "supplemental_cell_count":len(selected),
            "augmented_linear_margin_rank":rank,
            "distinct_supplemental_measurement_outcomes":num_classes,
            "ambiguous_output_classes_for_sign":sign_ambiguous,
            "ambiguous_output_classes_for_odds_ratio":ratio_ambiguous,
            "ambiguous_output_classes_for_full_table":table_ambiguous,
            "feasible_tables_in_sign_ambiguous_classes":sign_unresolved_candidates,
            "sign_universally_identified":singleton_sign,
            "odds_ratio_universally_identified":singleton_ratio,
            "complete_table_universally_identified":singleton_full
        }
        summaries.append(row)
        if len(selected)==1:
            row["sign_ambiguous_single_cell_observations"]=distinct_sign_ambiguous_outputs
            single_measurement_details.append(row)

    def released_world_diagnostics(x:np.ndarray)->dict[str,object]:
        v=tuple(int(y) for y in x[0,0])
        out={}
        for subset in ((5,),(0,),(0,5)):
            vals=tuple(v[i] for i in subset)
            matching=[(t,r,s) for t,r,s in universe
                      if tuple(t[i] for i in subset)==vals]
            odds={r for _,r,_ in matching}
            signs={s for _,_,s in matching}
            out["bins_"+("_".join(map(str,subset)))]={
                "released_counts":list(vals),
                "remaining_full_tables":len(matching),
                "remaining_odds_ratio_values":len(odds),
                "possible_signs":sorted(signs),
                "odds_min":float(min(odds)),
                "odds_max":float(max(odds)),
            }
        return out
    if (
        len(summaries)!=64 or minimum["full_table"]!=5
        or minimum["exact_odds_ratio"]!=2 or minimum["sign"]!=2
        or [0,5] not in universal_identifiers["sign"]
        or [0,5] not in universal_identifiers["exact_odds_ratio"]
        or any(item["sign_universally_identified"] for item in single_measurement_details)
        or not any(item["feasible_tables_in_sign_ambiguous_classes"]<PARENT_COUNT
                   for item in single_measurement_details)
    ):
        raise ValueError("pre-frozen target-specific minimal design gates failed")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_TARGET_SPECIFIC_MINIMUM_OBSERVATION_DESIGN",
        "parent_complete_positive_integer_tables":PARENT_COUNT,
        "supplemental_candidate_count":6,
        "exhaustive_subset_count":64,
        "minimum_number_of_additional_cell_counts_to_identify_any_fiber_world":
            minimum,
        "globally_sufficient_subsets_by_target":universal_identifiers,
        "every_frozen_candidate_subset":summaries,
        "single_cell_designs":single_measurement_details,
        "original_world_A_release_diagnostics":released_world_diagnostics(WORLD_A),
        "original_world_B_release_diagnostics":released_world_diagnostics(WORLD_B),
        "information_is_exact_cells_not_record_count_sample_size":True,
        "number_of_possible_completions_not_a_probability_distribution":True,
        "no_ecological_data_read":True,
        "real_device_effort_unknown":True,
        "no_qualified_ODSP_route_change":True,
    }
