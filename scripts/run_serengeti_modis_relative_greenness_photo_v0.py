#!/usr/bin/env python3
"""Post-first-photo NDVI-level/rank-vs-delta ecological SOURCE diagnostic.

Replays original 83 NASA/Terra source scenes and original 38,792 Serengeti
PHOTO records, then exactly recovers previous 15 first paper Spearman rhos
BEFORE reporting new (a) mean greenness level and (b) across-camera relative
NDVI rank change. Every original source camera coordinate stays in ephemeral
runner memory. No camera-hours, animal latent behavior or causal mechanism.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
import statistics

from scripts.run_serengeti_camera_ndvi_photo_assoc_v0 import (
    FIRST_SATELLITE_SHA,
    REQUIRED_ORIGINAL_SITES,REQUIRED_ORIGINAL_DATE_PAIRS,
    REQUIRED_ORIGINAL_PHOTOS,FOCAL,YEARS,MIN_YEAR_VALID_NDVI_PAIR_DATES,
    MIN_YEAR_VALID_NDVI_PAIR_FRACTION,MIN_PHOTO_EVENTS_PER_BRANCH_PER_SITE,
    MIN_SITES_PER_SPECIES_YEAR_FOR_CORRELATION,MIN_YEAR_PHOTO_COVERAGE,
    pinned_original_scene_receipt,source_scene_roster,scene_pixels,
    last_completed_site_NDVI,correlations_by_taxon_year,
    spearman,_rank,mean
)
from scripts.run_serengeti_regional_modis_container_token_v1 import (
    official_anonymous_container_token
)
from scripts.run_serengeti_source_recorded_solar_season_v0 import (
    INDEPENDENCE_MINUTES,zone,load_effort
)
from scripts.run_serengeti_photo_weather_cycle_alignment_v0 import (
    original_first_receipt_verified,raw_source_data
)
from scripts.run_serengeti_same_station_trophic_photo_time_v0 import (
    derive_calendar_eligibility
)

OLD_NDVI_CAMERA_PHOTO_SHA = "b6ed0294d6e4c6277f07ef9327f536c564c33c79265570bf7b37197eb951c25f"
COVARIATES=("delta_NDVI","mean_level_NDVI","relative_rank_shift")
OUTCOMES=("photographed_count_log_ratio","photographed_night_share_delta")
SPEARMAN_SOURCE_REPLAY_TOL=1e-10
SOURCE_EXPECTED_SAT_QA_CAMERA_YEARS=(98,112,112)
REQUIRED_FIRST_SUPPORTED={
    ("zebra",2011):53,
    ("zebra",2012):31,
    ("wildebeest",2011):27
}

def prior_source_receipt(path:Path)->dict:
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=OLD_NDVI_CAMERA_PHOTO_SHA:
        raise ValueError("HOLD_20261015_FIRST_CAMERA_NDVI_PHOTO_RECEIPT_CHANGED")
    prior=json.loads(raw)
    if (prior.get("all_original_match_photo_records")!=REQUIRED_ORIGINAL_PHOTOS
        or prior.get("original_24_290_photoperiod_site_date_pairs")!=REQUIRED_ORIGINAL_DATE_PAIRS
        or len(prior.get("all_five_prelisted_taxa_and_three_years_descriptive_correlations",[]))!=15):
        raise ValueError("HOLD_PREVIOUS_SOURCE_SAMPLE_CHANGED")
    return prior

def source_pixel_and_camera_date_sample(consensus:Path,effort:Path,satellite:Path):
    original_first_receipt_verified(consensus,effort)
    old_sat=pinned_original_scene_receipt(satellite)
    cycles,_=load_effort(effort)
    geos,events=raw_source_data(consensus,set(cycles))
    if len(geos)!=REQUIRED_ORIGINAL_SITES:
        raise ValueError("HOLD_OLD_CAMERA_COORDINATE_ROSTER_CHANGED")
    source_dates,structural=derive_calendar_eligibility(cycles,geos)
    scenes,old_items=source_scene_roster(old_sat)
    token=official_anonymous_container_token()
    ndvi_series=[]
    for original_scene,prior_scene in zip(scenes,old_items):
        values,_=scene_pixels(original_scene,token,geos,prior_scene)
        ndvi_series.append(values)
    ends=[date.fromisoformat(s["end_date"]) for s in scenes]
    if ends!=sorted(ends):
        raise ValueError("HOLD_NDVI_COMPOSITE_DATE_ORDER")

    qualified_siteyear={}
    qualified_photo_dates={}
    year_roster=defaultdict(lambda:{"total_source_pairs":0,"qa_source_pairs":0,
                                    "original_sitecycles":0,"admitted_sites":0})
    orig_pair_sum=0
    for site,by_year in cycles.items():
        if site not in geos: continue
        for year,pairs in by_year.items():
            original_pairs=[]
            for rising,falling in pairs:
                if (source_dates.get((site,rising))==(year,"rising")
                    and source_dates.get((site,falling))==(year,"falling")):
                    original_pairs.append((rising,falling))
            orig_pair_sum+=len(original_pairs)
            if year not in YEARS or not original_pairs: continue
            stats=year_roster[year]
            stats["original_sitecycles"]+=1
            stats["total_source_pairs"]+=len(original_pairs)
            valid=[]
            for rising,falling in original_pairs:
                u=last_completed_site_NDVI(ends,ndvi_series,site,rising)
                f=last_completed_site_NDVI(ends,ndvi_series,site,falling)
                if u is not None and f is not None:
                    valid.append((rising,falling,u,f))
            stats["qa_source_pairs"]+=len(valid)
            if (len(valid)<MIN_YEAR_VALID_NDVI_PAIR_DATES
                or len(valid)/len(original_pairs)<MIN_YEAR_VALID_NDVI_PAIR_FRACTION):
                continue
            stats["admitted_sites"]+=1
            rising=mean([row[2] for row in valid])
            falling=mean([row[3] for row in valid])
            qualified_siteyear[(site,year)]={
                "rising":rising,
                "falling":falling,
                "delta_NDVI":mean([row[3]-row[2] for row in valid]),
                "mean_level_NDVI":.5*(rising+falling),
            }
            for r,f,u,v in valid:
                qualified_photo_dates[(site,r)]=(year,"rising")
                qualified_photo_dates[(site,f)]=(year,"falling")
    if orig_pair_sum!=REQUIRED_ORIGINAL_DATE_PAIRS:
        raise ValueError("HOLD_OLD_SOURCE_PHOTOPERIOD_PAIR_ROSTER")

    # NDVI rank shift is defined against ALL original QA-qualified cameras,
    # NOT photo-positive selected cameras.
    for y in YEARS:
        sites=sorted(s for s,k in qualified_siteyear if k==y)
        if len(sites)!=SOURCE_EXPECTED_SAT_QA_CAMERA_YEARS[YEARS.index(y)]:
            raise ValueError("HOLD_OLD_NDVI_CAMERA_YEAR_ADMISSION")
        rvals=[qualified_siteyear[(s,y)]["rising"] for s in sites]
        fvals=[qualified_siteyear[(s,y)]["falling"] for s in sites]
        ranks_r=_rank(rvals)
        ranks_f=_rank(fvals)
        if len(sites)>1:
            for site,rr,ff in zip(sites,ranks_r,ranks_f):
                qualified_siteyear[(site,y)]["relative_rank_shift"]=(ff-rr)/(len(sites)-1)
        else:
            raise ValueError("HOLD_SINGLE_SATELLITE_SOURCE_SITE")
    return geos,events,source_dates,qualified_photo_dates,qualified_siteyear,year_roster

def species_photo_cells(geos,events,source_dates,qualified_photo_dates):
    previous_photo_count=0
    last={}
    full_totals=Counter()
    cells=defaultdict(Counter)
    for site,sp,t in events:
        key=(site,sp)
        if key in last and t-last[key]<timedelta(minutes=INDEPENDENCE_MINUTES):
            continue
        last[key]=t
        source=source_dates.get((site,t.date()))
        if source is None: continue
        previous_photo_count+=1
        year,branch=source
        if sp not in FOCAL: continue
        full_totals[(sp,year,branch)]+=1
        qualified=qualified_photo_dates.get((site,t.date()))
        if qualified is None: continue
        yr,br=qualified
        cells[(site,yr,sp,br)][zone(t,*geos[site])]+=1
    if previous_photo_count!=REQUIRED_ORIGINAL_PHOTOS:
        raise ValueError("HOLD_PREVIOUS_PHOTO_EVENT_COUNTS_CHANGED")
    return cells,full_totals

def compare_prior_inference(prior,old_results):
    registered=prior["all_five_prelisted_taxa_and_three_years_descriptive_correlations"]
    originals={(r["source_taxon"],r["solstice_cycle_year"]):r for r in registered}
    replay={(r["source_taxon"],r["solstice_cycle_year"]):r for r in old_results}
    if originals.keys()!=replay.keys():
        raise ValueError("HOLD_PREVIOUS_FIVE_TAXA_FIFTEEN_CYCLES")
    admitted={}
    for k in originals:
        a=originals[k];b=replay[k]
        for field in ("focal_photo_sites_both_branches_with_at_least_5_events",
                      "supported_descriptive_association","ndvi_siteyears_available"):
            if a[field]!=b[field]:
                raise ValueError("HOLD_PREVIOUS_SITE_OR_SUPPORT_GATES")
        for field in ("ndvi_vs_camera_photo_count_log_falling_rising",
                      "ndvi_vs_night_photo_fraction_difference"):
            old=a[field]["spearman"]
            new=b[field]["spearman"]
            if (old is None)!=(new is None):
                raise ValueError("HOLD_PREVIOUS_SPEARMAN_DEFINITION_CHANGED")
            if old is not None and abs(old-new)>SPEARMAN_SOURCE_REPLAY_TOL:
                raise ValueError("HOLD_PREVIOUS_SPEARMAN_RESULT_CHANGED")
        if b["supported_descriptive_association"]:
            admitted[k]=b["focal_photo_sites_both_branches_with_at_least_5_events"]
    if admitted!=REQUIRED_FIRST_SUPPORTED:
        raise ValueError("HOLD_POST_ECOLOGICAL_SELECTION_CHANGED")
    return True

def rho_leave_one_out(x,y):
    rho=spearman(x,y)
    if rho is None: return {"rho":None,"leave_one_camera_out_min_max":None}
    loos=[]
    for k in range(len(x)):
        r=spearman(x[:k]+x[k+1:],y[:k]+y[k+1:])
        if r is not None:loos.append(r)
    return {"rho":rho,
            "leave_one_camera_out_min_max":[min(loos),max(loos)] if loos else None}

def candidate_report(cells,photo_totals,siteyear,prior):
    delta={k:v["delta_NDVI"] for k,v in siteyear.items()}
    old=correlations_by_taxon_year(cells,delta,photo_totals)
    compare_prior_inference(prior,old)
    old_idx={(x["source_taxon"],x["solstice_cycle_year"]):x for x in old}
    output=[]
    for year in YEARS:
        for tax in FOCAL:
            old_row=old_idx[(tax,year)]
            sites=sorted(s for s,y in siteyear if y==year)
            data=[]
            for site in sites:
                b=cells.get((site,year,tax,"falling"),Counter())
                a=cells.get((site,year,tax,"rising"),Counter())
                N_f=sum(b.values());N_r=sum(a.values())
                if min(N_r,N_f)<MIN_PHOTO_EVENTS_PER_BRANCH_PER_SITE: continue
                pred=siteyear[(site,year)]
                data.append({
                    "delta_NDVI":pred["delta_NDVI"],
                    "mean_level_NDVI":pred["mean_level_NDVI"],
                    "relative_rank_shift":pred["relative_rank_shift"],
                    "photographed_count_log_ratio":math.log(N_f/N_r),
                    "photographed_night_share_delta":
                        b["night"]/N_f-a["night"]/N_r,
                })
            if len(data)!=old_row["focal_photo_sites_both_branches_with_at_least_5_events"]:
                raise ValueError("HOLD_PREVIOUS_CAMERA_TAXON_SOURCE_SAMPLE")
            predstats={}
            for cov in COVARIATES:
                predstats[cov]={
                    outcome:(
                        rho_leave_one_out(
                            [r[cov] for r in data],
                            [r[outcome] for r in data]
                        ) if old_row["supported_descriptive_association"]
                        else {"rho":None,"leave_one_camera_out_min_max":None}
                    ) for outcome in OUTCOMES
                }
            # Previous 'delta_NDVI' result must be unchanged, one more
            # explicit independent assertion before output new hypotheses.
            source=old_row["ndvi_vs_camera_photo_count_log_falling_rising"]["spearman"]
            follow=predstats["delta_NDVI"]["photographed_count_log_ratio"]["rho"]
            if (source is None)!=(follow is None) or (
                source is not None and abs(source-follow)>1e-10):
                raise ValueError("HOLD_OLD_PHOTO_NDVI_RHO_NOT_REPLAYED")
            source=old_row["ndvi_vs_night_photo_fraction_difference"]["spearman"]
            follow=predstats["delta_NDVI"]["photographed_night_share_delta"]["rho"]
            if (source is None)!=(follow is None) or (
                source is not None and abs(source-follow)>1e-10):
                raise ValueError("HOLD_OLD_PHOTO_NIGHT_RHO_NOT_REPLAYED")
            output.append({
                "taxon":tax,"year":year,
                "photo_positive_camera_sample_n":len(data),
                "supported_under_original_20261015_gate":old_row["supported_descriptive_association"],
                "source_photo_minimum_branch_coverage":
                    old_row["original_photo_count_coverage_min_branch"],
                "predictor_spearman":predstats,
            })
    return output

def analyze(consensus:Path,effort:Path,satellite:Path,prior:Path):
    previous=prior_source_receipt(prior)
    (
        geo,events,source_dates,qualified_dates,siteyears,roster
    )=source_pixel_and_camera_date_sample(consensus,effort,satellite)
    cells,full_totals=species_photo_cells(geo,events,source_dates,qualified_dates)
    science=candidate_report(cells,full_totals,siteyears,previous)
    spatial=[]
    for year in YEARS:
        v=[item for (site,y),item in siteyears.items() if y==year]
        d=[x["delta_NDVI"] for x in v]
        lvl=[x["mean_level_NDVI"] for x in v]
        rank=[x["relative_rank_shift"] for x in v]
        spatial.append({
            "year":year,
            "independent_source_camera_NDVI_QA_years":len(v),
            "delta_NDVI_min_max":[min(d),max(d)],
            "mean_level_NDVI_min_max":[min(lvl),max(lvl)],
            "relative_rank_shift_min_max":[min(rank),max(rank)],
            "fraction_site_pixel_NDVI_greenup_positive":
                sum(a>0 for a in d)/len(d),
            "source_camera_day_pairs":roster[year]["total_source_pairs"],
            "qa_good_source_camera_day_pairs":roster[year]["qa_source_pairs"],
        })
    return {
        "status":"EXPLORATORY_MODIS_RELATIVE_GREENNESS_PHOTO_RECORDS_ONLY",
        "original_first_photo_source_sha256":
            "0b70f7425d8ade2489a989bebc7b22fda997d82b2190e5e7d3c5d6f83ee71ef3",
        "original_first_modis_source_sha256":FIRST_SATELLITE_SHA,
        "original_camera_ndvi_photo_source_sha256":OLD_NDVI_CAMERA_PHOTO_SHA,
        "previous_five_taxa_all_15_rhos_replayed_exactly":True,
        "source_total_original_camera_PHOTO_events":REQUIRED_ORIGINAL_PHOTOS,
        "original_site_datepairs":REQUIRED_ORIGINAL_DATE_PAIRS,
        "original_source_camera_sites_count":REQUIRED_ORIGINAL_SITES,
        "years_camera_vegetation_source_coverage":spatial,
        "source_five_taxa_x_three_years_all_eighteen_outcome_correlations":science,
        "number_focal_taxon_years_previously_eligible":
            sum(c["supported_under_original_20261015_gate"] for c in science),
        "camera_ids_exact_location_raw_animal_time_data_exported":False,
        "independent_animals_or_device_hour_q_identified":False,
        "significance_pvalues_or_population_confidence_intervals_computed":False,
        "new_ecological_biomes_or_true_migration_identified":False,
        "interpretation":"Three alternative satellite greenness descriptors on EXACT same post-outcome PHOTO positive source rosters, not independent confirmation of an ecosystem response."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--consensus",required=True,type=Path)
    p.add_argument("--effort",required=True,type=Path)
    p.add_argument("--original-satellite-receipt",required=True,type=Path)
    p.add_argument("--old-camera-ndvi-photo-receipt",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    try:
        out=analyze(args.consensus,args.effort,args.original_satellite_receipt,
                    args.old_camera_ndvi_photo_receipt)
    except (OSError,ValueError,TypeError,KeyError,IndexError) as exc:
        out={"status":"HOLD_SOURCE_REPLAY_OR_SATELLITE_RELATIVE_RANK_FAILED",
             "error_type":type(exc).__name__,
             "no_causal_or_activity_result":True}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    selected=[{
        "taxon":r["taxon"],"year":r["year"],
        "cameras":r["photo_positive_camera_sample_n"],
        "predictors":{k:{o:z["rho"] for o,z in y.items()}
                      for k,y in r["predictor_spearman"].items()},
    } for r in out.get("source_five_taxa_x_three_years_all_eighteen_outcome_correlations",[])
      if r["supported_under_original_20261015_gate"]]
    print(json.dumps({"status":out["status"],"verified_source":out.get("previous_five_taxa_all_15_rhos_replayed_exactly"),
                      "eligible_groups":len(selected),"results":selected,"no_causality":True},sort_keys=True))
    if out["status"].startswith("HOLD"):raise SystemExit(2)

if __name__=="__main__":
    main()
