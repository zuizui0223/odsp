"""Observed acoustic detector-stratum information and whole-day transfer only.

This is NOT a model for true organism flight z or species occupancy.
No source-file metadata or response is owned here; values must come from a
separately pinned, prospectively declared source adapter.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import math
import random
from statistics import mean
from typing import NamedTuple

ALPHA = .5
SEED = 20261122
N_BOOT = 10000

class Record(NamedTuple):
    day: str
    hour: int
    bat_label: str
    recorded_stratum: str

def _validate(records):
    records=list(records)
    if len(records)==0: raise ValueError("nonempty observed source required")
    if len({r.day for r in records})<2: raise ValueError("multiple independent days required")
    for r in records:
        if r.recorded_stratum not in ("above","below"): raise ValueError("unrecognized detector stratum")
        if not r.day or not r.bat_label or not isinstance(r.hour,int) or not 0<=r.hour<=23:
            raise ValueError("invalid source context")
    return records

def _p(counts, pos):
    numerator=counts[pos]+ALPHA
    denominator=counts["above"]+counts["below"]+2*ALPHA
    return numerator/denominator

def _quantile(sorted_values,p):
    at=(len(sorted_values)-1)*p
    lo=int(math.floor(at))
    hi=int(math.ceil(at))
    return sorted_values[lo]+(at-lo)*(sorted_values[hi]-sorted_values[lo])

def conditional_information_given_hour(records):
    """In-sample I(Bat;recorded layer|hour) weighted by recording-row counts."""
    rows=_validate(records)
    hour=Counter()
    hs=Counter()
    hz=Counter()
    hsz=Counter()
    for r in rows:
        hour[r.hour]+=1
        hs[(r.hour,r.bat_label)]+=1
        hz[(r.hour,r.recorded_stratum)]+=1
        hsz[(r.hour,r.bat_label,r.recorded_stratum)]+=1
    info=0.
    for (h,s,z),n in hsz.items():
        info+=(n/len(rows))*math.log((n*hour[h])/(hs[(h,s)]*hz[(h,z)]))
    return float(max(0,info))

def minimum_detector_ratio_to_erase_partition(table, *, alpha=ALPHA, min_records=1):
    """Necessary & sufficient Γ for a COMMON latent above/below odds, in a
    free class×layer detector, given the *input table of positive expected means*.

    Counts + Jeffreys smoothing is only a plug-in field diagnostic.
    q_{sz} in [1/Γ,1]. Γ = sqrt(max observed odds/min observed odds).
    """
    if alpha<0 or not math.isfinite(alpha):raise ValueError("invalid smoothing")
    if min_records<1: raise ValueError("invalid minimum records")
    observed=[]
    for s,c in table.items():
        hi=float(c.get("above",0));lo=float(c.get("below",0))
        if hi<0 or lo<0 or not math.isfinite(hi+lo):
            raise ValueError("counts must be finite nonnegative")
        if hi+lo<min_records: continue
        if hi+alpha==0 or lo+alpha==0:
            raise ValueError("positive table cells/smoothing required")
        observed.append((hi+alpha)/(lo+alpha))
    if len(observed)<2:return None
    return math.sqrt(max(observed)/min(observed))

def score_recorded_stratum_by_day(records):
    rows=_validate(records)
    days=sorted({r.day for r in rows},key=lambda x:int(x) if x.isdecimal() else x)
    fold_scores=[]
    for day in days:
        train=[r for r in rows if r.day!=day]
        test=[r for r in rows if r.day==day]
        h=defaultdict(Counter)
        hs=defaultdict(Counter)
        for r in train:
            h[r.hour][r.recorded_stratum]+=1
            hs[(r.hour,r.bat_label)][r.recorded_stratum]+=1
        b0=b1=0.
        for r in test:
            if sum(h[r.hour].values())==0:
                raise ValueError("heldout hour has no reference training support")
            p0=_p(h[r.hour],r.recorded_stratum)
            c=hs.get((r.hour,r.bat_label))
            p1=_p(c,r.recorded_stratum) if c else p0
            b0+=math.log(p0)
            b1+=math.log(p1)
        n=len(test)
        fold_scores.append({"day":day,"record_rows":n,"b0":b0/n,"b1":b1/n,"delta":(b1-b0)/n})
    gains=[f["delta"] for f in fold_scores]
    rng=random.Random(SEED)
    boot=sorted(mean(rng.choice(gains) for _ in gains) for _ in range(N_BOOT))
    positive=sum(g>0 for g in gains)
    if positive==len(gains): verdict="all_days_positive"
    elif positive==0:verdict="no_day_positive"
    else: verdict="mixed_days"
    table=defaultdict(Counter)
    for r in rows:table[r.bat_label][r.recorded_stratum]+=1
    info=conditional_information_given_hour(rows)
    return {
        "n_source_rows":len(rows),
        "n_day_folds":len(days),
        "bat_acoustic_label_count":len(table),
        "above_row_count":sum(c["above"] for c in table.values()),
        "below_row_count":sum(c["below"] for c in table.values()),
        "in_sample_observed_record_I_bat_stratum_given_hour_nats":info,
        "in_sample_observed_record_I_bits":info/math.log(2),
        "equal_day_B0_logscore_nats_per_record":mean(f["b0"] for f in fold_scores),
        "equal_day_B1_logscore_nats_per_record":mean(f["b1"] for f in fold_scores),
        "equal_day_delta_nats_per_record":mean(gains),
        "delta_day_bootstrap_95pct_descriptive":[_quantile(boot,.025),_quantile(boot,.975)],
        "positive_day_folds":positive,
        "transfer_category":verdict,
        "per_day_fold_aggregates":[{"fold":i+1,"n_rows":f["record_rows"],
              "b0_nats":f["b0"],"b1_nats":f["b1"],"delta_nats":f["delta"]}
              for i,f in enumerate(fold_scores)],
        "detector_bias_gamma_min_all_labels_jeffreys_plugin":minimum_detector_ratio_to_erase_partition(table),
        "detector_bias_gamma_min_ge20_source_rows_jeffreys_plugin":minimum_detector_ratio_to_erase_partition(table,min_records=20),
        "bat_labels_ge20_source_rows":sum(sum(c.values())>=20 for c in table.values()),
        "evaluation_unit":"DAY (nine shared-region recording nights)",
        "outcome":"recorded_detector_position_by_original_table_row",
        "no_organism_flight_height_or_det_calibration":True,
        "sensor_gamma_is_not_measured":True,
    }
