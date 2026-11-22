"""Gomes (2020) source-verified local two-tower leave-group-out transfer.

COLOR = red/green COPAS canopy tower, proven by original paper Table 2
Tower=random effects and author Hourly_Models.R (1|COLOR).
This is *not* a globally independent held-out study nor detection-corrected z.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from statistics import mean
from typing import NamedTuple
import math


ALPHA=0.5
AUTHOR_TRAINING_MIN_TOTAL=6
TOWERS=("green","red")

class TowerCell(NamedTuple):
    day: str
    hour: int
    label: str
    stratum: str
    number: int
    tower: str


def _p(c: Counter, z: str) -> float:
    return (c[z]+ALPHA)/(c["above"]+c["below"]+2*ALPHA)


def check_source(cells: list[TowerCell]) -> None:
    if not cells:
        raise ValueError("no source records")
    towers={c.tower for c in cells}
    if towers!=set(TOWERS):
        raise ValueError("source must have exactly the two source-authenticated towers")
    for r in cells:
        if not r.day or not r.label or r.stratum not in ("above","below") or r.tower not in TOWERS:
            raise ValueError("source labels/strata invalid")
        if not isinstance(r.hour,int) or not 0<=r.hour<=23:
            raise ValueError("invalid source hour")
        if not isinstance(r.number,int) or r.number<0:
            raise ValueError("Number must be nonnegative integer")


def _score_records(train: list[TowerCell],test: list[TowerCell]) -> dict:
    by_hour=defaultdict(Counter)
    by_bat_hour=defaultdict(Counter)
    label_totals=Counter()
    all_strata=Counter()
    for r in train:
        label_totals[r.label]+=r.number
        all_strata[r.stratum]+=r.number
        by_hour[r.hour][r.stratum]+=r.number
        by_bat_hour[(r.hour,r.label)][r.stratum]+=r.number
    if sum(all_strata.values())==0:
        raise ValueError("training group has zero acoustic counts")
    sample_n=sum(r.number for r in test)
    if sample_n<=0:
        raise ValueError("target physical-tower×day has zero counts")
    B0=B1=0.0
    previously_unseen=0
    fallback=0
    for r in test:
        if r.number==0:
            continue
        reference=by_hour[r.hour]
        if sum(reference.values())==0:
            reference=all_strata
        p0=_p(reference,r.stratum)
        class_counts=by_bat_hour.get((r.hour,r.label))
        class_supported=(label_totals[r.label]>=AUTHOR_TRAINING_MIN_TOTAL
                         and class_counts is not None
                         and sum(class_counts.values())>0)
        if class_supported:
            p1=_p(class_counts,r.stratum)
        else:
            p1=p0
            fallback+=r.number
            if label_totals[r.label]==0:
                previously_unseen+=r.number
        B0+=r.number*math.log(p0)
        B1+=r.number*math.log(p1)
    return {
        "heldout_recorded_acoustic_counts":sample_n,
        "B0_hour_only_score_nats_per_count":B0/sample_n,
        "B1_hour_plus_acoustic_label_score_nats_per_count":B1/sample_n,
        "delta_B1_minus_B0_nats_per_count":(B1-B0)/sample_n,
        "previously_unseen_label_count_share":previously_unseen/sample_n,
        "training_rare_or_unseen_label_fallback_count_share":fallback/sample_n,
        "training_labels_ge6_counts":sum(n>=AUTHOR_TRAINING_MIN_TOTAL for n in label_totals.values()),
    }


def score_tower_transfer(cells) -> dict:
    rows=list(cells)
    check_source(rows)
    days=sorted({r.day for r in rows},key=lambda x:int(x) if x.isdecimal() else x)
    if len(days)!=9:
        raise ValueError("source support changed: 9 independent DAY groups required")

    # The primary whole-tower target is independent of day×tower completeness.
    direct=[]
    for tower in TOWERS:
        train=[r for r in rows if r.tower!=tower]
        target=[r for r in rows if r.tower==tower]
        direct.append({"tower":tower,**_score_records(train,target)})

    def report_average(items,field):
        return mean(r[field] for r in items)

    primary = {
        "by_tower":direct,
        "equal_tower_mean_B0_nats_per_count":report_average(direct,"B0_hour_only_score_nats_per_count"),
        "equal_tower_mean_B1_nats_per_count":report_average(direct,"B1_hour_plus_acoustic_label_score_nats_per_count"),
        "equal_tower_mean_delta_nats_per_count":report_average(direct,"delta_B1_minus_B0_nats_per_count"),
        "positive_tower_folds":sum(x["delta_B1_minus_B0_nats_per_count"]>0 for x in direct),
    }

    tower_day_total=Counter()
    for r in rows:
        tower_day_total[(r.tower,r.day)]+=r.number
    missing=[(tower,day) for tower in TOWERS for day in days
             if tower_day_total[(tower,day)]<=0]
    # The frozen secondary protocol mandates STOP if even one target
    # tower×DAY cell has no observed positive pass. Do not silently drop
    # missing folds or relax the 18-fold design post-outcome.
    if missing:
        secondary={
            "status":"structural_stop_missing_or_zero_tower_day_count",
            "secondary_scientific_scores_opened":False,
            "required_tower_day_cells":len(TOWERS)*len(days),
            "missing_or_zero_tower_day_cells":len(missing),
            "eligible_positive_tower_day_cells":len(TOWERS)*len(days)-len(missing),
            "no_support_filling_or_new_split":True,
        }
    else:
        tower_day=[]
        for tower in TOWERS:
            for day in days:
                train=[r for r in rows if r.tower!=tower and r.day!=day]
                held=[r for r in rows if r.tower==tower and r.day==day]
                if not all(r.tower!=tower and r.day!=day for r in train):
                    raise AssertionError("source leakage")
                tower_day.append({"tower":tower,"fold_day":day,**_score_records(train,held)})

        def sanitized(item):
            return {**{k:v for k,v in item.items() if k not in ("tower","fold_day")},
                    "day_fold":days.index(item["fold_day"])+1}
        by_tower_day=[]
        for tower in TOWERS:
            vals=[x for x in tower_day if x["tower"]==tower]
            by_tower_day.append({
                "tower":tower,
                "n_heldout_day_folds":len(vals),
                "equal_day_delta_nats_per_count":report_average(vals,"delta_B1_minus_B0_nats_per_count"),
                "positive_day_folds":sum(x["delta_B1_minus_B0_nats_per_count"]>0 for x in vals),
                "per_day_aggregate":[sanitized(x) for x in vals],
            })
        secondary={
            "status":"source_supported_two_tower_night_folds",
            "by_tower":by_tower_day,
            "equal_tower_then_day_delta_nats_per_count":mean(
                v["equal_day_delta_nats_per_count"] for v in by_tower_day
            ),
            "positive_tower_day_folds":sum(x["delta_B1_minus_B0_nats_per_count"]>0 for x in tower_day),
            "n_tower_day_folds":len(tower_day),
            "tower_day_folds_are_not_independent_geographies":True,
        }

    return {
        "source": "Gomes et al. 2020 Zenodo v1",
        "model_level":"observed bat acoustic passes and original sampled microphone position",
        "independent_tower_count":len(TOWERS),
        "tower_spacing_m_original_paper":180,
        "cross_geography_generalization_claim":False,
        "unmeasured_species_stratum_detection_bias":True,
        "original_count_weighted_n":sum(r.number for r in rows),
        "leave_one_tower_out":primary,
        "leave_both_tower_and_night_out":secondary,
    }
