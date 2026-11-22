"""Original-author bat count weighted detector-stratum transfer.

Source table row is a design cell, response 'Number' is recorded activity.
Original source had a balanced cartesian-like design, so unweighted row MI
cannot be interpreted as biological activity. No habitat/site identifiers
are recovered or imputed. Only detected acoustic patterns are modeled.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import math,random
from statistics import mean
from typing import NamedTuple

from .detected_vertical_transfer import minimum_detector_ratio_to_erase_partition

PRIOR=.5
SEED=20261122
N_BOOT=10000
ORIGINAL_AUTHOR_MIN_TOTAL=6

class CountCell(NamedTuple):
    day: str
    hour: int
    label: str
    position: str
    number: int

def _quantile(vals,q):
    a=sorted(vals)
    at=(len(a)-1)*q
    lo=int(math.floor(at));hi=int(math.ceil(at))
    return a[lo]+(at-lo)*(a[hi]-a[lo])

def _p(table,layer):
    return (table[layer]+PRIOR)/(table["above"]+table["below"]+2*PRIOR)

def condition_information_from_counts(cells):
    by_h=Counter();by_hs=Counter();by_hz=Counter();by_hsz=Counter()
    total=0
    for r in cells:
        n=r.number
        total+=n
        by_h[r.hour]+=n
        by_hs[(r.hour,r.label)]+=n
        by_hz[(r.hour,r.position)]+=n
        by_hsz[(r.hour,r.label,r.position)]+=n
    if total<=0:raise ValueError("no positive source activity")
    mi=0.
    for (h,s,z),n in by_hsz.items():
        if n<=0:continue
        mi+=(n/total)*math.log(n*by_h[h]/(by_hs[(h,s)]*by_hz[(h,z)]))
    return max(0.,float(mi))

def score_weighted_counts(cells):
    cells=list(cells)
    if not cells:raise ValueError("no source cells")
    for r in cells:
        if not r.day or not r.label or not isinstance(r.hour,int) or not 0<=r.hour<=23:
            raise ValueError("bad bat source context")
        if r.position not in ("above","below"):
            raise ValueError("invalid microphone stratum")
        if not isinstance(r.number,int) or r.number<0:
            raise ValueError("Number must be a nonnegative integer")
    days=sorted({r.day for r in cells},key=lambda x:int(x) if x.isdecimal() else x)
    if len(days)!=9:
        raise ValueError("frozen original study needs nine DAY blocks")
    totals=Counter()
    for r in cells:totals[r.label]+=r.number
    admitted={s for s,v in totals.items() if v>=ORIGINAL_AUTHOR_MIN_TOTAL}
    clean=[r for r in cells if r.label in admitted]
    if len(admitted)<2:raise ValueError("fewer than two qualified original bat labels")

    global_label_table=defaultdict(Counter)
    selected_table=defaultdict(Counter)
    for r in cells:
        global_label_table[r.label][r.position]+=r.number
        if r.label in admitted:
            selected_table[r.label][r.position]+=r.number

    folds=[]
    for day in days:
        test=[r for r in clean if r.day==day]
        train=[r for r in clean if r.day!=day]
        train_all=Counter()
        byhour=defaultdict(Counter)
        bybat_hour=defaultdict(Counter)
        for r in train:
            train_all[r.position]+=r.number
            byhour[r.hour][r.position]+=r.number
            bybat_hour[(r.hour,r.label)][r.position]+=r.number
        if sum(train_all.values())==0:raise ValueError("no training activity")
        b0=b1=0.;target_total=0
        for r in test:
            if r.number==0:continue  # zero contributes 0, not a fictitious non-detection
            target_total+=r.number
            base=byhour[r.hour] if sum(byhour[r.hour].values())>0 else train_all
            p0=_p(base,r.position)
            contextual=bybat_hour.get((r.hour,r.label))
            p1=_p(contextual,r.position) if contextual and sum(contextual.values())>0 else p0
            b0+=r.number*math.log(p0)
            b1+=r.number*math.log(p1)
        if target_total==0:raise ValueError("whole heldout DAY has no positive recorded counts")
        folds.append({"day":day,"count":target_total,
                      "b0":b0/target_total,"b1":b1/target_total,
                      "delta":(b1-b0)/target_total})
    gains=[f["delta"] for f in folds]
    rng=random.Random(SEED)
    boot=[mean(rng.choice(gains) for _ in gains) for _ in range(N_BOOT)]
    pos=sum(v>0 for v in gains)
    verdict="all_days_positive" if pos==len(gains) else ("no_day_positive" if pos==0 else "mixed_days")
    return {
        "source_data_cell_rows":len(cells),
        "source_all_acoustic_labels":len(totals),
        "source_nonzero_count_cells":sum(r.number>0 for r in cells),
        "source_zero_count_cells":sum(r.number==0 for r in cells),
        "source_total_number_counts_including_rare_labels":sum(totals.values()),
        "author_rule_excluded_labels_total_le5":len(totals)-len(admitted),
        "retained_acoustic_labels_author_rule":len(admitted),
        "total_scored_recorded_counts_retained":sum(f["count"] for f in folds),
        "in_sample_recorded_count_weighted_I_label_stratum_given_hour_nats":condition_information_from_counts(clean),
        "B0_equal_day_logscore_nats_per_recorded_count":mean(f["b0"] for f in folds),
        "B1_equal_day_logscore_nats_per_recorded_count":mean(f["b1"] for f in folds),
        "B1_minus_B0_equal_day_gain_nats_per_recorded_count":mean(gains),
        "day_gain_bootstrap_95pct_descriptive":[_quantile(boot,.025),_quantile(boot,.975)],
        "positive_whole_day_folds":pos,
        "nine_day_transfer_category":verdict,
        "per_day_folds":[{"fold":i+1,"recorded_count":f["count"],"B0":f["b0"],
                          "B1":f["b1"],"gain":f["delta"]} for i,f in enumerate(folds)],
        "detector_gamma_min_author_retained_labels_jeffreys_plugin":minimum_detector_ratio_to_erase_partition(selected_table,alpha=PRIOR),
        "detector_gamma_min_all_labels_jeffreys_plugin":minimum_detector_ratio_to_erase_partition(global_label_table,alpha=PRIOR),
        "data_unit":"sum(Number) acoustic passes within grouped day",
        "independent_model_evaluation_unit":"DAY (same sampled source region)",
        "organism_height_estimated":False,
        "species_by_stratum_detection_probability_estimated":False,
        "independent_site_transfer_estimated":False,
    }
