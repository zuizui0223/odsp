"""V2 study-heldout vertical biodiversity profile forecasting (source proxy only).

Frozen scientific contract: docs/vertebrate_vertical_study_v2_preoutcome_scoring_freeze.md.
No animal GPS z, no species-level occupancy, no corrected source detector q.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from math import exp, isfinite, log, fsum
from random import Random
from statistics import mean
from typing import Iterable

BETA_GRID = tuple(-6.0 + 0.25 * k for k in range(49))
ORIGINAL_TAXA = ("Amphibians","Bats","Birds","Small mammals")
ORIGINAL_ENDPOINTS = ("abundance","richness")
STUDY_SHRINK = 5.0
MIN_STUDIES_FOR_TAXON = 4
MIN_STUDIES_FOR_ENDPOINT = 15
BOOTSTRAP_REPS = 10000
BOOTSTRAP_SEEDS = {"abundance":20261123,"richness":20261124}


@dataclass(frozen=True)
class SourceRow:
    study: str
    site: str
    taxon: str
    metric: str
    height: float
    value: float


@dataclass(frozen=True)
class Profile:
    study: str
    site: str
    taxon: str
    metric: str
    heights: tuple[float,...]
    q: tuple[float,...]
    source_rows: int
    repeated_height_rows: int


def assemble_profiles(rows: Iterable[SourceRow]):
    raw = defaultdict(list)
    for r in rows:
        if not r.study or not r.site or r.taxon not in ORIGINAL_TAXA or r.metric not in ORIGINAL_ENDPOINTS:
            raise ValueError("invalid study, site, taxon or original biodiversity endpoint")
        if not isfinite(r.height) or r.height < -1e-9 or r.height > 1.000000001:
            raise ValueError("original normalized height invalid")
        raw[(r.site,r.metric)].append(r)
    if not raw:
        raise ValueError("no original source profile")

    profiles = []
    invalid_response_units = 0
    source_repeat_rows=0
    source_repeat_units=0
    for (site,metric),group in sorted(raw.items()):
        studies={r.study for r in group}
        taxa={r.taxon for r in group}
        if len(studies)!=1 or len(taxa)!=1:
            raise ValueError("original site×endpoint has conflicting study or taxa")
        by_height=defaultdict(list)
        for r in group:
            by_height[round(r.height,8)].append(r.value)
        if len(by_height)<2:
            # This is a fixed *geometry-only* exclusion. No y inspected.
            continue
        repeat_count=len(group)-len(by_height)
        if repeat_count:
            source_repeat_units+=1
            source_repeat_rows+=repeat_count
        if any((not isfinite(r.value)) or r.value < 0 for r in group):
            invalid_response_units+=1
            continue
        heights=sorted(by_height)
        y=[mean(by_height[h]) for h in heights]
        total=fsum(y)
        if total<=0 or not isfinite(total):
            invalid_response_units+=1
            continue
        q=tuple(v/total for v in y)
        if abs(fsum(q)-1)>1e-10:
            raise ValueError("target unit did not normalize")
        profiles.append(Profile(
            study=group[0].study,site=site,taxon=group[0].taxon,metric=metric,
            heights=tuple(heights),q=q,source_rows=len(group),
            repeated_height_rows=repeat_count,
        ))
    if invalid_response_units:
        # V2 predeclared: the WHOLE source outcome evaluation stops if even a
        # single geometry-qualified group has an invalid numerical response.
        raise ValueError(f"SOURCE_RESPONSE_STOP: {invalid_response_units} source site×metric groups invalid")
    if not profiles:
        raise ValueError("SOURCE_RESPONSE_STOP: no analyzable source profiles")
    return profiles, {
        "geometry_qualified_profile_count":len(profiles),
        "site_metric_units_with_duplicate_heights":source_repeat_units,
        "extra_height_rows_collapsed_by_arithmetic_mean":source_repeat_rows,
        "site_metric_profiles_with_numeric_response_exclusions":0,
        "height_coordinate":"mean_strata_height_p original canopy-scaled coordinate",
        "numerical_response":"author corrected_biodiversity_metric_value normalized within site×endpoint",
    }


def logscore(profile: Profile, beta:float)->float:
    if not isfinite(beta):
        raise ValueError("nonfinite model slope")
    logits=[beta*h for h in profile.heights]
    high=max(logits)
    lse=high+log(fsum(exp(z-high) for z in logits))
    return fsum(w*(z-lse) for w,z in zip(profile.q,logits))


def site_macro_by_study(profiles:list[Profile],beta:float)->float:
    scores=defaultdict(list)
    for p in profiles:
        scores[p.study].append(logscore(p,beta))
    if not scores:
        raise ValueError("training study cohort has no profiles")
    return mean(mean(v) for v in scores.values())


def fit_beta(profiles:list[Profile])->float:
    # 49 grid settings specified before original source target access.
    # Minimize negative study-equal logscore; deterministic tie breaker.
    return max(BETA_GRID,key=lambda beta:(
        site_macro_by_study(profiles,beta), -abs(beta), -beta
    ))


def fit_training_slopes(profiles:list[Profile], heldout_study:str, metric:str):
    train=[p for p in profiles if p.study!=heldout_study and p.metric==metric]
    n_global=len({p.study for p in train})
    if n_global<MIN_STUDIES_FOR_ENDPOINT-1:
        raise ValueError("too few heldout original-study training groups")
    beta_global=fit_beta(train)
    by_taxon={}
    for taxon in ORIGINAL_TAXA:
        subset=[p for p in train if p.taxon==taxon]
        n=len({p.study for p in subset})
        if n<MIN_STUDIES_FOR_TAXON:
            by_taxon[taxon]=(beta_global,n,False)
        else:
            beta_taxon=fit_beta(subset)
            shrunk=(n*beta_taxon+STUDY_SHRINK*beta_global)/(n+STUDY_SHRINK)
            by_taxon[taxon]=(shrunk,n,True)
    return beta_global,by_taxon


def _bootstrap(gains:list[float],seed:int)->list[float]:
    rng=Random(seed)
    samples=sorted(mean(rng.choice(gains) for _ in gains)
                   for __ in range(BOOTSTRAP_REPS))
    def q(p):
        x=(len(samples)-1)*p
        lo=int(x);hi=min(lo+1,len(samples)-1)
        return samples[lo]+(x-lo)*(samples[hi]-samples[lo])
    return [q(.025),q(.975)]


def _summarize(folds:list[dict],metric:str,cohort:str):
    vals=[r["delta_b1_minus_b0"] for r in folds]
    if not vals:
        return None
    pos=sum(v>0 for v in vals)
    return {
        "taxon_or_endpoint":cohort,
        "metric":metric,
        "original_independent_heldout_studies":len(vals),
        "positive_heldout_study_gains":pos,
        "source_study_fold_category":(
            "all-positive" if pos==len(vals) else
            "all-nonpositive" if pos==0 else "mixed"
        ),
        "equal_study_logscore_B0":mean(x["b0"] for x in folds),
        "equal_study_logscore_B1":mean(x["b1"] for x in folds),
        "equal_study_logscore_Bminus1_uniform":mean(x["bminus1_uniform"] for x in folds),
        "equal_study_mean_gain_nats_per_normalized_profile":mean(vals),
        "study_gain_range":[min(vals),max(vals)],
        "descriptive_study_bootstrap_95pct":_bootstrap(vals,BOOTSTRAP_SEEDS[metric]),
        "heldout_study_folds":[
            {"fold":i+1,"site_count":x["site_count"],
             "delta":x["delta_b1_minus_b0"],
             "b0":x["b0"],"b1":x["b1"],
             "b1_taxon_training_study_count":x["taxon_train_studies"],
             "b1_fitted_taxon":x["taxon_specific_fitted"]}
            for i,x in enumerate(sorted(folds,key=lambda f:f["study"]))
        ],
        "original_study_id_names_redacted_from_receipt":True,
    }


def evaluate_transfer(profiles:list[Profile])->dict:
    original_studies={p.study for p in profiles}
    if len(original_studies)<MIN_STUDIES_FOR_ENDPOINT:
        raise ValueError("too few independent original studies for source transfer")
    output={}
    for metric in ORIGINAL_ENDPOINTS:
        subset=[p for p in profiles if p.metric==metric]
        studies=sorted({p.study for p in subset})
        if len(studies)<MIN_STUDIES_FOR_ENDPOINT:
            output[metric]={"status":"endpoint_insufficient_original_studies","n_original_studies":len(studies)}
            continue
        folds=[]
        for held in studies:
            target=[p for p in subset if p.study==held]
            assert target
            taxa={p.taxon for p in target}
            if len(taxa)!=1:
                raise ValueError("heldout study spans broad taxa")
            taxon=next(iter(taxa))
            bg,bt=fit_training_slopes(profiles,held,metric)
            chosen,n_taxon,supported=bt[taxon]
            folds.append({
                "study":held, "taxon":taxon,"metric":metric,"site_count":len(target),
                "bminus1_uniform":mean(logscore(p,0) for p in target),
                "b0":mean(logscore(p,bg) for p in target),
                "b1":mean(logscore(p,chosen) for p in target),
                "delta_b1_minus_b0":mean(logscore(p,chosen)-logscore(p,bg) for p in target),
                "taxon_train_studies":n_taxon,
                "taxon_specific_fitted":supported,
            })
        per_taxon={}
        for taxon in ORIGINAL_TAXA:
            fs=[r for r in folds if r["taxon"]==taxon]
            if fs:
                per_taxon[taxon]=_summarize(fs,metric,taxon)
        output[metric]={
            "status":"prospective_whole_original_study_holdout_evaluated",
            "all_taxa_original_study_summary":_summarize(folds,metric,"all_taxa"),
            "by_original_taxon":per_taxon,
            "source_site_metric_profile_count":len(subset),
            "original_heldout_study_count":len(studies),
        }
    return {
        "status":"source_curated_vertical_biodiversity_proxy_study_holdout_evaluated",
        "scores_by_endpoint":output,
        "beta_grid":{"min":-6.0,"max":6.0,"step":.25,"n":len(BETA_GRID)},
        "study_shrinkage_strength":STUDY_SHRINK,
        "train_studies_taxon_minimum":MIN_STUDIES_FOR_TAXON,
        "original_study_group_holdout":True,
        "within_site_repeated_height_policy":"arithmetic_mean_before_profile_normalization",
        "is_species_level_SDM":False,
        "is_latent_organism_height_or_detector_q_corrected":False,
        "is_independent_heldout_forest_study_predictive_comparison":True,
    }
