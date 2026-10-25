"""Study-block ecological summaries for all original 24 Movebank solar/weather sources.

Aggregates each distinct archived source ID equally, not individual GPS fixes,
animal instances, selected site-years, species pairs, or paper effect sizes.
This is descriptive across selected original source studies, not a random-biome
significance test or causal sunlight/wind mediation.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import random
from statistics import mean

from scripts.movebank_native_ecology_20261019 import HERE

CONTRACT=HERE/"research/SOLAR_AZIMUTH_24_SOURCE_WEATHER_STUDY_BLOCK_SYNTHESIS_V0_CONTRACT.json"
SOURCES=HERE/"research/GLOBAL_SOLAR_AZIMUTH_NEW24_PROVIDER_FROZEN_SOURCE_FILE_MANIFEST_20261025.json"
INPUT=HERE/"research/SOLAR_AZIMUTH_24_SOURCE_MULTI_POPULATION_ERA5_V0_FIRST_ALL_RESULTS_20261025.json"
MEASURES=("sunward_cos","windflow_cos","wind_sun_cos",
          "wind_speed_100m_ms","shortwave_Wm2","temperature_2m_C")
PREDICTORS=("wind_sun_cos","windspeed_ms","shortwave_Wm2","temperature_C")


def _study_mean(source):
    """Within native taxon equal site-years; within source equal supported taxa."""
    taxon_summaries=[]
    for t in source["source_taxa"]:
        contexts=[
            x for x in t.get("source_gridyear_weather_contexts",[])
            if x.get("weather_environmental_effect_status")==
               "SOURCE_GROUP_OBSERVED_ENVIRONMENT_DESCRIPTION"
        ]
        m={}
        for key in MEASURES:
            vals=[x["environmental_group_means"][key]["mean"]
                  for x in contexts if x.get("environmental_group_means") is not None
                  and x["environmental_group_means"][key]["mean"] is not None]
            m[key]=mean(vals) if vals else None
        for var in PREDICTORS:
            vals=[x["within_animal_clock_month_weather_associations"][var]["mean"]
                  for x in contexts
                  if x.get("within_animal_clock_month_weather_associations")
                  and x["within_animal_clock_month_weather_associations"][var]["mean"] is not None]
            m["slope_"+var]=mean(vals) if vals else None
        taxon_summaries.append({
            "taxon":t["taxon"],"source_siteyear_observed_contexts":len(contexts),
            "source_siteyear_all_selected_contexts":
                len(t.get("source_gridyear_weather_contexts",[])),
            "means":m,
        })
    keys=list(MEASURES)+["slope_"+x for x in PREDICTORS]
    source_means={}
    for key in keys:
        v=[r["means"][key] for r in taxon_summaries if r["means"][key] is not None]
        source_means[key]=mean(v) if v else None
    return {
        "source_package_uuid":source["source_package_uuid"],
        "original_repository_study_ids":source["source_study_ids"],
        "original_source_status":source["original_source_status"],
        "source_GPS_first_results_replayed":source["source_original_replay_success"],
        "original_native_taxa_total":len(source["source_taxa"]),
        "source_modal_gridyears_attempted":sum(
            len(t.get("source_gridyear_weather_contexts",[])) for t in source["source_taxa"]),
        "source_modal_gridyears_observed":sum(
            x["source_siteyear_observed_contexts"] for x in taxon_summaries),
        "source_taxa_with_environmental_description":sum(
            x["source_siteyear_observed_contexts"]>0 for x in taxon_summaries),
        "original_ERA5_gridyear_requests":source["source_climate_request_count"],
        "source_taxa":taxon_summaries,
        "source_study_equal_taxon_context_means":source_means,
        "source_effects_are_observational":True
    }


def study_bootstrap_mean(values, n=2000, seed=20261025):
    if len(values)<6:
        return None
    rand=random.Random(seed)
    k=len(values)
    sample=sorted(mean(values[rand.randrange(k)] for _ in range(k))
                  for _ in range(n))
    return [sample[int(.025*n)],sample[min(n-1,int(.975*n)-1)]]


def study_mean_summary(sources, key):
    entries=[x["source_study_equal_taxon_context_means"][key]
             for x in sources if x["source_study_equal_taxon_context_means"][key] is not None]
    lo=[]
    if len(entries)>2:
        lo=[mean(entries[:i]+entries[i+1:]) for i in range(len(entries))]
    return {
        "total_original_source_archives":len(sources),
        "study_ID_source_archives_with_identifiable_effect":len(entries),
        "study_equal_mean":mean(entries) if entries else None,
        "source_cluster_bootstrap95":study_bootstrap_mean(entries),
        "original_study_source_means_positive":sum(x>0 for x in entries),
        "original_study_source_means_negative":sum(x<0 for x in entries),
        "leave_one_source_out_mean_range":[min(lo),max(lo)] if lo else None,
        "source_study_result_is_causal_or_global_probability":False
    }


def _average_tie_ranks(vals):
    indexed=sorted(enumerate(vals),key=lambda x:x[1])
    result=[0.0]*len(vals)
    i=0
    while i<len(vals):
        j=i+1
        while j<len(vals) and indexed[j][1]==indexed[i][1]:
            j+=1
        avg=(i+j-1)/2+1
        for k in range(i,j):
            result[indexed[k][0]]=avg
        i=j
    return result


def _pearson(a,b):
    if len(a)!=len(b) or len(a)<3:
        return None
    ma,mb=mean(a),mean(b)
    xx=sum((v-ma)**2 for v in a)
    yy=sum((v-mb)**2 for v in b)
    if xx<=1e-12 or yy<=1e-12:
        return None
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(xx*yy)


def spearman(a,b):
    return _pearson(_average_tie_ranks(a),_average_tie_ranks(b))


def source_block_spearman(sources, climate_key, nbootstrap=1000):
    pairs=[]
    for item in sources:
        s=item["source_study_equal_taxon_context_means"]
        if s["sunward_cos"] is not None and s[climate_key] is not None:
            pairs.append((s[climate_key],s["sunward_cos"]))
    x=[v[0] for v in pairs]
    y=[v[1] for v in pairs]
    rho=spearman(x,y) if len(pairs)>=8 else None
    ranges=[]
    if len(pairs)>=9:
        ranges=[spearman(x[:i]+x[i+1:],y[:i]+y[i+1:]) for i in range(len(pairs))]
        ranges=[z for z in ranges if z is not None]
    boots=None
    if rho is not None:
        rng=random.Random(20261025)
        sim=[]
        for j in range(nbootstrap):
            rows=[pairs[rng.randrange(len(pairs))] for _ in pairs]
            z=spearman([p[0] for p in rows],[p[1] for p in rows])
            if z is not None:
                sim.append(z)
        if len(sim)>=int(.9*nbootstrap):
            sim.sort()
            boots=[sim[int(.025*len(sim))],sim[min(len(sim)-1,int(.975*len(sim))-1)]]
    return {
      "one_equal_unit_per_original_source_study":True,
      "n_original_source_archives_with_both_weather_and_solar":len(pairs),
      "Spearman_source_level_rho":rho,
      "source_cluster_bootstrap95_descriptive":boots,
      "leave_one_original_source_out_rho_range":[min(ranges),max(ranges)] if ranges else None,
      "interpretation":"Descriptive across source-observed study-conditions, confounded by taxon and region. No global causal climate effect."
    }


def analyze_combined(first):
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    roster=json.loads(SOURCES.read_text(encoding="utf-8"))["source_file_entries"]
    if contract["version"]!="solar-azimuth-24-original-source-weather-study-block-synthesis-v0":
        raise ValueError("Post-outcome synthesis contract changed")
    if first.get("version")!="original-gps-solar-population-weather-v0":
        raise ValueError("Wrong ecological original source first result version")
    if len(first["source_groups"])!=24:
        raise ValueError("Must preserve all original 24 source archives")
    uuids=[r["package_uuid"] for r in roster]
    original=[x["source_package_uuid"] for x in first["source_groups"]]
    if set(uuids)!=set(original) or len(set(original))!=24:
        raise ValueError("Original source roster/duplicates changed")
    studies=[_study_mean(x) for x in sorted(first["source_groups"],
                                         key=lambda v:uuids.index(v["source_package_uuid"]))]
    existing=[study_id for source in studies for study_id in source["original_repository_study_ids"]]
    if len(existing)!=24 or len(set(existing))!=24:
        raise ValueError("Cannot treat duplicate or missing study IDs as separate source blocks")
    associations={
        k:study_mean_summary(studies,"slope_"+k) for k in PREDICTORS
    }
    climate={
        k:source_block_spearman(studies,k)
        for k in ("temperature_2m_C","shortwave_Wm2","wind_speed_100m_ms")
    }
    observed_siteyear_contexts=sum(s["source_modal_gridyears_observed"] for s in studies)
    report={
       "version":"solar-azimuth-24-original-source-weather-study-block-synthesis-v0",
       "complete_fixed_source_archive_denominator":24,
       "distinct_repository_study_ID_labels":len(set(existing)),
       "original_source_MD5_and_previous_effect_replay_passes":
           sum(s["source_GPS_first_results_replayed"] for s in studies),
       "source_archives_with_at_least_one_environmental_group":
           sum(s["source_modal_gridyears_observed"]>0 for s in studies),
       "source_study_taxon_environment_contexts_observed":
           observed_siteyear_contexts,
       "study_equal_univariate_within_tagged_animal_climate_slopes":associations,
       "study_equal_meteorological_context_correlations":climate,
       "all_24_source_level_descriptions":studies,
       "conclusion_ceiling":"Exploratory same-GPS-step ERA5 contextual variation, not causal sunlight/weather orientation, species phylogenetic pattern, or independent world's ecological landscapes."
    }
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--first-results",type=Path,default=INPUT)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    first=json.loads(args.first_results.read_text(encoding="utf-8"))
    r=analyze_combined(first)
    (args.out/"study_block_macroecology.json").write_text(
        json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    summary={k:v for k,v in r.items() if k!="all_24_source_level_descriptions"}
    print("SOLAR_WEATHER_SOURCE_BLOCK_MACROECOLOGY "+
          json.dumps(summary,sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
