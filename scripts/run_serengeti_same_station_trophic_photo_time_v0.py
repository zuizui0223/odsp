#!/usr/bin/env python3
"""Same camera site/cycle predator–prey recorded photo-time seasonal contrast.

EXPLORATORY after prior pooled/cycle results. Not proof of predator-prey
encounters, temporal avoidance, animal activity, or source q/ON hours.
Original source and exact previous photo outcome MUST replay first.
No protected camera/site/timestamp fields are exported.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import timedelta
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median

from scripts.run_serengeti_photo_weather_cycle_alignment_v0 import (
    original_first_receipt_verified, raw_source_data
)
from scripts.run_serengeti_source_recorded_solar_season_v0 import (
    load_effort, solar_boundaries, zone,
    DAYLENGTH_MISMATCH_MAX_MINUTES, INDEPENDENCE_MINUTES,
)
PAIRS = (
    ("hyenaSpotted", "zebra", "predator_possible_prey"),
    ("lionFemale", "wildebeest", "predator_possible_prey_secondary"),
    ("buffalo", "zebra", "herbivore_context"),
    ("hyenaSpotted", "lionFemale", "carnivore_context"),
)
ORIGINAL_EVENTS = 38792
ORIGINAL_DATE_PAIRS = 24290
ORIGINAL_SITE_COUNT = 186
YEARS = (2010, 2011, 2012)

def night_day(c: Counter) -> tuple[int,int]:
    return c.get("night",0), c.get("core",0)+c.get("edge",0)

def strict_log_three_way(
    f_a:Counter, f_b:Counter, r_a:Counter, r_b:Counter
) -> float | None:
    an,ad=night_day(f_a); bn,bd=night_day(f_b)
    cn,cd=night_day(r_a); dn,dd=night_day(r_b)
    if min(an,ad,bn,bd,cn,cd,dn,dd) <= 0:
        return None
    return (math.log(an/ad) - math.log(bn/bd)
            - math.log(cn/cd) + math.log(dn/dd))

def sitecycle_difference(f_a:Counter,f_b:Counter,r_a:Counter,r_b:Counter):
    # Every taxon × seasonal-branch marginal must have an observed source
    # detection. No taxon/day-zone pseudocounts.
    margin=[sum(x.values()) for x in (f_a,f_b,r_a,r_b)]
    if not all(margin): return None
    frac=lambda c:c.get("night",0)/sum(c.values())
    return (frac(f_a)-frac(f_b))-(frac(r_a)-frac(r_b))

def stats(values:list[float]):
    if not values: return {
        "n":0, "mean":None,"median":None,
        "positive":0,"negative":0,"zero":0
    }
    return {
        "n":len(values),"mean":mean(values),"median":median(values),
        "positive":sum(v>0 for v in values),
        "negative":sum(v<0 for v in values),
        "zero":sum(v==0 for v in values),
    }

def pair_summary(focal:str,comparison:str,role:str,
                 species_counts:dict, structural_sitecycles:set):
    by_cam=defaultdict(list)
    by_year=defaultdict(lambda:defaultdict(list))
    all_d=[]
    complete=[]
    candidate_by_year=Counter()
    records_by_tax_year=defaultdict(lambda:defaultdict(Counter))
    n_photo=0
    for site,year in sorted(structural_sitecycles):
        a=species_counts.get(focal,{})
        b=species_counts.get(comparison,{})
        fa=a.get((site,year,"falling"),Counter())
        ra=a.get((site,year,"rising"),Counter())
        fb=b.get((site,year,"falling"),Counter())
        rb=b.get((site,year,"rising"),Counter())
        for label,c0 in ((focal,fa),(focal,ra),(comparison,fb),(comparison,rb)):
            records_by_tax_year[year][label].update(c0)
            n_photo+=sum(c0.values())
        D=sitecycle_difference(fa,fb,ra,rb)
        if D is None: continue
        candidate_by_year[year]+=1
        by_cam[site].append(D)
        by_year[year][site].append(D)
        all_d.append(D)
        ld=strict_log_three_way(fa,fb,ra,rb)
        if ld is not None: complete.append(ld)
    site_means=[mean(vals) for vals in by_cam.values()]
    loo=[]
    for site in by_cam:
        v=[mean(vals) for s,vals in by_cam.items() if s!=site]
        if v: loo.append(mean(v))
    year_rows=[]
    for year in YEARS:
        site_scores=[mean(vals) for vals in by_year[year].values()]
        year_rows.append({
            "solstice_cycle_year":year,
            "eligible_codetected_sitecycles":candidate_by_year[year],
            "camera_equal_D":stats(site_scores),
            "original_record_counts_focal_and_comparison":{
                tax:dict(records_by_tax_year[year][tax])
                for tax in (focal,comparison)
            },
        })
    return {
        "focal_taxon":focal,"comparison_taxon":comparison,"ecological_role":role,
        "structurally_eligible_camera_sitecycles":len(structural_sitecycles),
        "sitecycles_with_both_taxa_recorded_in_both_season_branches":len(all_d),
        "distinct_physical_cameras_supporting_pair":len(by_cam),
        "sitecycle_equal_D":stats(all_d),
        "physical_camera_equal_D":stats(site_means),
        "physical_camera_leave_one_out_D_min_max":
            [min(loo),max(loo)] if loo else None,
        "strict_eight_nonzero_record_cells_sitecycles":len(complete),
        "strict_no_pseudocount_three_way_log_or_sitecycle_mean":
            mean(complete) if complete else None,
        "strict_no_pseudocount_three_way_log_or_sitecycle_median":
            median(complete) if complete else None,
        "original_source_records_focal_and_comparison_all_sitecycles":n_photo,
        "per_solstice_cycle":year_rows,
        "sampling_ceiling":"Co-recording selected on positive source events; D is a detected-photo night-fraction contrast only; not animal-independent causal predator-prey timing.",
    }

def derive_calendar_eligibility(cycles, geos):
    eligibility={}
    source_pairs=0
    structural_sitecycles=set()
    for site,by_cycle in cycles.items():
        if site not in geos:continue
        lat,lon=geos[site]
        for cycle,pairs in by_cycle.items():
            for rising,falling in pairs:
                _,_,up=solar_boundaries(rising,lat,lon)
                _,_,down=solar_boundaries(falling,lat,lon)
                if abs(up-down)>DAYLENGTH_MISMATCH_MAX_MINUTES:continue
                eligibility[(site,rising)]=(cycle,"rising")
                eligibility[(site,falling)]=(cycle,"falling")
                structural_sitecycles.add((site,cycle))
                source_pairs+=1
    if source_pairs != ORIGINAL_DATE_PAIRS:
        raise ValueError("HOLD_ORIGINAL_FROZEN_PHOTOPERIOD_ROSTER_DRIFT")
    return eligibility,structural_sitecycles

def run(consensus:Path,effort:Path):
    original=original_first_receipt_verified(consensus,effort)
    cycles,_=load_effort(effort)
    geos,events=raw_source_data(consensus,set(cycles))
    if len(geos)!=ORIGINAL_SITE_COUNT:
        raise ValueError("HOLD_FIRST_PHYSICAL_SITE_ROSTER_DRIFT")
    eligible,sitecycles=derive_calendar_eligibility(cycles,geos)
    focal_taxa=set(x for a,b,_ in PAIRS for x in (a,b))
    observed={sp:defaultdict(Counter) for sp in focal_taxa}
    last_seen={}
    n_retained=0
    for site,sp,t in events:
        prior=last_seen.get((site,sp))
        if prior is not None and t-prior<timedelta(minutes=INDEPENDENCE_MINUTES):
            continue
        last_seen[(site,sp)]=t
        date_info=eligible.get((site,t.date()))
        if date_info is None:continue
        n_retained+=1
        if sp in observed:
            cycle,branch=date_info
            observed[sp][(site,cycle,branch)][zone(t,*geos[site])]+=1
    if n_retained!=ORIGINAL_EVENTS:
        raise ValueError("HOLD_FIRST_SOURCE_38792_REPLAY_MISMATCH")
    all_original_taxa=sorted(t["species"] for t in original["taxa"])
    if any(t not in all_original_taxa for t in focal_taxa):
        raise ValueError("HOLD_SOURCE_TAXON_NOT_PRESENT")
    outcomes=[
        pair_summary(a,b,role,observed,sitecycles)
        for a,b,role in PAIRS
    ]
    return {
        "status":"EXPLORATORY_CO_RECORDED_PREDATOR_PREY_NIGHT_FRACTION_DESCRIPTIVE",
        "previous_original_photo_result_still_immutable":True,
        "original_first_source_sha256":
            "0b70f7425d8ade2489a989bebc7b22fda997d82b2190e5e7d3c5d6f83ee71ef3",
        "source_camera_photo_events_replayed":n_retained,
        "source_solar_caliper_site_date_pairs":ORIGINAL_DATE_PAIRS,
        "original_source_taxon_labels_unmodified":len(all_original_taxa),
        "structurally_eligible_camera_sitecycles":len(sitecycles),
        "pairs":outcomes,
        "site_ids_coordinates_and_photo_times_exported":False,
        "source_hardware_on_hours_or_detector_q_calibrated":False,
        "prey_predator_encounters_hunting_or_competition_proven":False,
        "biological_population_replication_across_regions_proven":False,
        "interpretation":"Within CAMERA/SOURCE record fractions ONLY; paired co-detection roster is selected on source observations. No valid animal-level p or causal predation.",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--consensus",type=Path,required=True)
    p.add_argument("--effort",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    try:
        result=run(args.consensus,args.effort)
    except (OSError,ValueError,TypeError,KeyError,IndexError) as e:
        result={
            "status":"HOLD_ORIGINAL_CAMERA_SOURCE_OR_ANALYSIS_REPLAY_FAILED",
            "error_type":type(e).__name__,
            "animal_ecological_conclusion":None
        }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "source_records_replayed":result.get("source_camera_photo_events_replayed"),
        "structurally_eligible_site_cycles":result.get("structurally_eligible_camera_sitecycles"),
        "pairs":[{
            "pair":z["focal_taxon"]+"/"+z["comparison_taxon"],
            "n_physical_cameras":z["distinct_physical_cameras_supporting_pair"],
            "site_cycle_support":z["sitecycles_with_both_taxa_recorded_in_both_season_branches"],
            "camera_equal_D":z["physical_camera_equal_D"],
            "cycle_support":[(x["solstice_cycle_year"],x["eligible_codetected_sitecycles"]) for x in z["per_solstice_cycle"]],
            "strict_8cell_support":z["strict_eight_nonzero_record_cells_sitecycles"]
        } for z in result.get("pairs",[])],
        "true_interaction_or_hunting_inferred":False,
    },sort_keys=True))
    if result["status"].startswith("HOLD"): raise SystemExit(2)

if __name__=="__main__": main()
