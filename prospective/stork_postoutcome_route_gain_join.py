#!/usr/bin/env python3
"""Exploratory, bird-unit join of altitude-BLIND micro-route metrics with the
two already FROZEN altitude-identity per-bird score files.

No new altitude-model fitting, no GPS height values or permutations. All
correlation and between-source analyses are post-outcome descriptive.
"""
from __future__ import annotations
import argparse,csv,json,math,random,statistics
from pathlib import Path


def avg_rank(values):
    order=sorted(range(len(values)),key=lambda i:values[i])
    out=[0.]*len(values)
    i=0
    while i<len(order):
        j=i+1
        while j<len(order) and values[order[j]]==values[order[i]]:j+=1
        rank=(i+1+j)/2
        for k in order[i:j]:out[k]=rank
        i=j
    return out


def spearman(x,y):
    if len(x)!=len(y) or len(x)<3:return None
    rx,ry=avg_rank(x),avg_rank(y)
    if len(set(rx))<=1 or len(set(ry))<=1:return None
    return statistics.correlation(rx,ry)


def percentiles(s):
    vals=sorted(s)
    if not vals:return [None,None]
    def q(p):
        z=(len(vals)-1)*p
        lo=math.floor(z);hi=math.ceil(z)
        return float(vals[lo]+(vals[hi]-vals[lo])*(z-lo))
    return [q(.025),q(.975)]


def fixed_scores_csv(path):
    with path.open("rt",encoding="utf-8-sig",newline="") as stream:
        entries=list(csv.DictReader(stream))
    fields={"bird","age","days","bins","gain"}
    if not entries or not fields.issubset(entries[0]):
        raise ValueError("Previously frozen per-bird score schema unavailable")
    birds={}
    for e in entries:
        bird=e["bird"]
        if bird in birds:
            raise ValueError("Duplicate biological bird ID in original result")
        birds[bird]=dict(age=e["age"],days=int(e["days"]),
                         bins=int(e["bins"]),gain=float(e["gain"]))
    return birds


def join(geometry_2013,geometry_2014,score_2013,score_2014,nboot=5000,seed=20261021):
    info={
      "rotics2013":(geometry_2013,score_2013,25,111,6951),
      "flack2014":(geometry_2014,score_2014,11,33,2040),
    }
    metric_names=["self_fine_fraction","other_fine_fraction",
      "other_equal_bird_fine_fraction", "fine_self_minus_equal_bird_other",
      "fine_self_minus_other","own_coarse_revisit_gap_days",
      "nested_fine_subcells_per_day"]
    report={
        "analysis":"POST_OUTCOME_STORK_FINE_ROUTE_X_VERTICAL_IDENTITY_V1",
        "scoring":"No altitude shape models re-run; merge exact frozen bird-level scores only",
        "inferential_claim":"Exploratory between cohort route reuse and age/date source comparison; no causal ecological mechanism inferred",
        "n_bootstrap":nboot,"bootstrap_seed":seed,
        "metric_definitions":{
           "self_fine_fraction":"Fraction target 5min x-y fixes in fine 5km cells that focal bird visited on another UTC date within same 50km coarse cell",
           "other_fine_fraction":"Fraction target 5min x-y fixes in fine 5km cells other birds visited on OTHER UTC dates within same 50km coarse cell",
           "fine_self_minus_other":"Historical asymmetric focal-vs-pooled-ANY-other-bird reference, retained for audit only",
           "other_equal_bird_fine_fraction":"Probability of matching one uniformly chosen other bird that has source records on another date in same 50km cell, rather than any bird in an inflated pooled union",
           "fine_self_minus_equal_bird_other":"Corrected bird-day equal focal minus equally weighted other biological bird nested fine-cell re-use",
           "own_coarse_revisit_gap_days":"For matched bird-day/coarse cells, nearest earlier or later different UTC day this bird used same 50km coarse cell",
        },
        "sources":{},
        "cross_cohort":{}
    }
    series={}
    for source,(geom,scores,expected_birds,expected_days,expected_fixes) in info.items():
        if geom["altitude_values_read"] is not False or geom["source"]!=source:
            raise ValueError("Geometry source or altitude-blind guarantee mismatch")
        g=geom["geometry"]
        birds=g["birds"]
        if (len(birds),g["bird_day_count"],g["scored_fixes"])!=(expected_birds,expected_days,expected_fixes):
            raise ValueError("Original source cohort structure drift")
        if set(birds)!=set(scores):
            raise ValueError("Frozen altitude scores are not precisely the same bird roster")
        names=sorted(birds)
        correlations={}
        for name in metric_names:
            vals=[birds[b][name] for b in names]
            gain=[scores[b]["gain"] for b in names]
            correlations[name]=spearman(vals,gain)
        report["sources"][source]={
           "birds":len(birds),
           "bird_days":g["bird_day_count"],
           "scored_fixes":g["scored_fixes"],
           "route_metrics":g["equal_bird_summary"],
           "spearman_route_vs_original_altitude_gain_descriptive":correlations,
           "original_positive_bird_scores":sum(scores[b]["gain"]>0 for b in names),
           "original_age_breakdown":dict(sorted(
               (k,sum(scores[b]["age"]==k for b in names))
               for k in set(scores[b]["age"] for b in names))),
           "original_mean_altitude_gain":statistics.mean(scores[b]["gain"] for b in names),
           "coarse_preheight_roster_hash":g["eligible_roster_hash"],
        }
        series[source]={metric:[birds[b][metric] for b in names] for metric in metric_names}

    rng=random.Random(seed)
    for metric in metric_names:
        A,B=series["rotics2013"][metric],series["flack2014"][metric]
        n,m=len(A),len(B)
        # Bird is the sampling unit. Do not resample GPS fixes or sessions.
        bootstrap=[
            statistics.mean(A[rng.randrange(n)] for _ in range(n))
            - statistics.mean(B[rng.randrange(m)] for _ in range(m))
            for _ in range(nboot)
        ]
        report["cross_cohort"][metric]={
          "rotics2013_equal_bird_mean":statistics.mean(A),
          "flack2014_equal_bird_mean":statistics.mean(B),
          "difference_2013_minus_2014":statistics.mean(A)-statistics.mean(B),
          "bird_bootstrap_95pct_exploratory":percentiles(bootstrap),
          "causal_or_confirmatory":False,
        }
    report["claim_limits"]=[
      "Fine 5km within 50km x-y recurrence approximates repeated geometric corridor use, not actual wind, uplift, resource type or behavioural mode.",
      "The initial any-other-bird pooled union artificially increased the comparison opportunity. Prefer the equal-other-bird probabilities; even those are not matched on GPS fixes or duration.",
      "Already-opened 2013 positive vs 2014 non-supported vertical identities made this a post-outcome mechanism exploratory analysis.",
      "Different source year, age stage, time coverage, terrain, GPS tags and 25 vs 11 eligible birds confound source contrasts.",
      "Correlations with original altitude identity score are not a cross-taxon causal test or new calibration of its fixed null.",
      "Overlapping cohorts may share a tag serial used on distinct individuals in the full source database; source tags do not provide independent GPS height calibration."
    ]
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--geometry-2013",type=Path,required=True)
    p.add_argument("--geometry-2014",type=Path,required=True)
    p.add_argument("--original-birds-2013",type=Path,required=True)
    p.add_argument("--original-birds-2014",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    a=json.loads(args.geometry_2013.read_text())
    b=json.loads(args.geometry_2014.read_text())
    x=fixed_scores_csv(args.original_birds_2013)
    y=fixed_scores_csv(args.original_birds_2014)
    result=join(a,b,x,y)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
      "route_self_2013":result["sources"]["rotics2013"]["route_metrics"]["self_fine_fraction"]["mean"],
      "route_self_2014":result["sources"]["flack2014"]["route_metrics"]["self_fine_fraction"]["mean"],
      "route_self_difference_bootstrap":result["cross_cohort"]["self_fine_fraction"]["bird_bootstrap_95pct_exploratory"],
      "route_self_minus_other_2013":result["sources"]["rotics2013"]["route_metrics"]["fine_self_minus_other"]["mean"],
      "route_self_minus_other_2014":result["sources"]["flack2014"]["route_metrics"]["fine_self_minus_other"]["mean"],
      "equal_other_bird_2013":result["sources"]["rotics2013"]["route_metrics"]["other_equal_bird_fine_fraction"]["mean"],
      "equal_other_bird_2014":result["sources"]["flack2014"]["route_metrics"]["other_equal_bird_fine_fraction"]["mean"],
      "self_minus_equal_other_2013":result["sources"]["rotics2013"]["route_metrics"]["fine_self_minus_equal_bird_other"]["mean"],
      "self_minus_equal_other_2014":result["sources"]["flack2014"]["route_metrics"]["fine_self_minus_equal_bird_other"]["mean"],
      "gain_vs_route_recurrence_2013":result["sources"]["rotics2013"]["spearman_route_vs_original_altitude_gain_descriptive"]["fine_self_minus_equal_bird_other"],
      "gain_vs_route_recurrence_2014":result["sources"]["flack2014"]["spearman_route_vs_original_altitude_gain_descriptive"]["fine_self_minus_equal_bird_other"],
    },sort_keys=True))


if __name__=="__main__":
    main()
