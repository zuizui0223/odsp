"""Nonreplication diagnosis across TWO frozen cohorts of 24 original GPS studies.

Inputs: previously committed original-source group results only. NEVER reads a
new individual animal track, selects favorable source studies, or modifies
the preregistered fresh-source nonreplication decision.

The source bootstrap/permutation reference conditions on original sampled
study IDs, NOT a random draw of independent world biomes or a causal effect.
"""
from __future__ import annotations
from collections import Counter
import argparse
import json
import math
from pathlib import Path
import random
from statistics import mean

from scripts.movebank_native_ecology_20261019 import HERE

CONTRACT=HERE/"research/SOLAR_RADIATION_TWO_24_SOURCE_NONREPLICATION_DIAGNOSTIC_V0_CONTRACT.json"
EARLIER=HERE/"research/SOLAR_AZIMUTH_24_SOURCE_WEATHER_SOURCE_BLOCK_MACRO_FIRST_RESULT_20261025.json"
EXTERNAL=HERE/"research/SOLAR_RADIATION_EXTERNAL_24_STUDY_SIGNED_TEST_FIRST_RESULT_20261025.json"
EARLIER_CONTEXTS=HERE/"research/SOLAR_AZIMUTH_24_SOURCE_MULTI_POPULATION_ERA5_V0_FIRST_ALL_RESULTS_20261025.json"
EXTERNAL_CONTEXTS=HERE/"research/SOLAR_RADIATION_EXTERNAL_24_SOURCE_FIRST_ALL_RESULTS_20261025.json"

BOOTSTRAP_DRAWS=20000
PERMUTATIONS=20000
SEED=20261025


def mean_ci(values,nboot=BOOTSTRAP_DRAWS,seed=SEED,minn=5):
    if len(values)<minn:
        return None
    if any(not math.isfinite(v) for v in values):
        raise ValueError("Nonfinite original study source slope")
    rng=random.Random(seed)
    n=len(values)
    samples=sorted(mean(values[rng.randrange(n)] for _ in range(n))
                   for _ in range(nboot))
    return [samples[int(.025*nboot)],samples[min(nboot-1,int(.975*nboot)-1)]]


def two_source_set_comparison(a,b,nboot=BOOTSTRAP_DRAWS,nperm=PERMUTATIONS):
    if len(a)<6 or len(b)<6:
        raise ValueError("Source-level diagnostic requires enough original studies")
    rng=random.Random(SEED)
    delta=mean(a)-mean(b)
    n,m=len(a),len(b)
    boot=[]
    for _ in range(nboot):
        draw_a=mean(a[rng.randrange(n)] for _ in range(n))
        draw_b=mean(b[rng.randrange(m)] for _ in range(m))
        boot.append(draw_a-draw_b)
    boot.sort()
    leave_a=[mean(a[:i]+a[i+1:])-mean(b) for i in range(n)]
    leave_b=[mean(a)-mean(b[:i]+b[i+1:]) for i in range(m)]
    pooled=a+b
    rnd=random.Random(SEED+1)
    total=0
    for _ in range(nperm):
        shuffle=rnd.sample(pooled,len(pooled))
        randomized=mean(shuffle[:n])-mean(shuffle[n:])
        if abs(randomized)>=abs(delta)-1e-15:
            total+=1
    return {
        "earlier_source_N":n,"external_source_N":m,
        "equal_source_earlier_mean":mean(a),
        "equal_source_external_mean":mean(b),
        "earlier_minus_external_observed_mean_difference":delta,
        "source_within_sample_bootstrap95_difference":
            [boot[int(.025*nboot)],boot[min(nboot-1,int(.975*nboot)-1)]],
        "observed_mean_difference_source_leave_one_earlier_out_range":
            [min(leave_a),max(leave_a)],
        "observed_mean_difference_source_leave_one_external_out_range":
            [min(leave_b),max(leave_b)],
        "pooled_source_equal_mean":mean(pooled),
        "pooled_source_cluster_bootstrap95":mean_ci(pooled,seed=SEED+2),
        "Monte_Carlo_two_sided_permutation_reference":{
            "n_shuffles":nperm,
            "fraction_random_source_labels_with_abs_difference_as_large":total/nperm,
            "NOT_a_valid_randomized_world_source_design_p_value":True,
            "reason":"Original source archive selection/biome/taxon distribution not exchangeable between two source collections."
        }
    }


def source_biological_class(taxa,classes):
    match=[cl for cl,names in classes.items() if set(taxa)&set(names)]
    unknown=set(taxa)-{name for names in classes.values() for name in names}
    if unknown:
        raise ValueError("Unknown source native taxonomic group not in fixed class roster")
    if len(match)!=1:
        raise ValueError("Source taxon group mixed; explicitly label rather than select")
    return match[0]


def sign_pattern(original_contexts):
    valid=[
        c for c in original_contexts
        if c.get("within_animal_clock_month_weather_associations")
        and c["within_animal_clock_month_weather_associations"].get("shortwave_Wm2")
        and c["within_animal_clock_month_weather_associations"]["shortwave_Wm2"]["mean"] is not None
    ]
    values=[c["within_animal_clock_month_weather_associations"]["shortwave_Wm2"]["mean"]
            for c in valid]
    if len(values)<2:
        status="ONLY_ONE_OR_ZERO_IDENTIFIABLE_SOURCE_CONTEXT"
    elif any(v<0 for v in values) and any(v>0 for v in values):
        status="OPPOSITE_SIGN_ACROSS_SELECTED_SOURCE_CONTEXTS"
    elif all(v<0 for v in values):
        status="ALL_IDENTIFIABLE_SOURCE_CONTEXTS_NEGATIVE"
    elif all(v>0 for v in values):
        status="ALL_IDENTIFIABLE_SOURCE_CONTEXTS_POSITIVE"
    else:
        status="ZERO_PRESENT"
    coarse_bands=sorted({
        tuple([c.get("geographic_latitude_band_not_coordinate",{}).get("hemisphere"),
               *c.get("geographic_latitude_band_not_coordinate",{}).get("absolute_latitude_band_degrees",[])])
        for c in valid if c.get("geographic_latitude_band_not_coordinate")
    })
    hemispheres={b[0] for b in coarse_bands}
    return {
        "original_source_siteyear_taxon_contexts_with_supported_shortwave_slopes":len(valid),
        "original_source_context_shortwave_negative":sum(v<0 for v in values),
        "original_source_context_shortwave_positive":sum(v>0 for v in values),
        "within_original_source_study_context_sign_consistency":status,
        "source_observed_hemisphere":
            next(iter(hemispheres)) if len(hemispheres)==1 else
            "MIXED" if hemispheres else None,
        "original_observed_coarse_latitude_bands_15degrees":
            [list(b) for b in coarse_bands]
    }


def build_source_entries(earlier,external,early_contexts,later_contexts,classes):
    orig={x["source_package_uuid"]:x for x in early_contexts["source_groups"]}
    ext={x["source_package_uuid"]:x for x in later_contexts["all_external_first_source_results"]}
    rows=[]
    for s in earlier["all_24_source_level_descriptions"]:
        x=orig[s["source_package_uuid"]]
        values=x["source_taxa"]
        eligible=[
            t for t in values
            if any(c.get("within_animal_clock_month_weather_associations",{}).get("shortwave_Wm2",{}).get("mean") is not None
                   for c in t["source_gridyear_weather_contexts"]
                   if c.get("within_animal_clock_month_weather_associations"))
        ]
        slope=s["source_study_equal_taxon_context_means"]["slope_shortwave_Wm2"]
        biological_class=(source_biological_class([t["taxon"] for t in eligible],classes)
                          if eligible else None)
        contexts=[c for t in eligible for c in t["source_gridyear_weather_contexts"]]
        rows.append({
            "cohort":"earlier","source_package_uuid":s["source_package_uuid"],
            "study_ids":s["original_repository_study_ids"],
            "original_native_taxon_labels":sorted({t["taxon"] for t in values}),
            "original_native_taxa_with_radiation_slopes":[t["taxon"] for t in eligible],
            "ecological_locomotion_class":biological_class,
            "radiation_slope_per_100Wm2":slope,
            "source_siteyear_recorded_contexts":s["source_modal_gridyears_attempted"],
            "source_siteyear_weather_qualified_contexts":s["source_modal_gridyears_observed"],
            **sign_pattern(contexts)
        })
    for s in external["all_24_source_study_slope_means"]:
        x=ext[s["source_uuid"]]
        slope=s["source_slope_means"]["shortwave_Wm2"]
        eligible=[x["original_taxon"]] if slope is not None else []
        contexts=x["source_taxa"][0]["source_gridyear_weather_contexts"] if eligible else []
        rows.append({
            "cohort":"external","source_package_uuid":s["source_uuid"],
            "study_ids":s["source_study_ids"],
            "original_native_taxon_labels":[x["original_taxon"]],
            "original_native_taxa_with_radiation_slopes":eligible,
            "ecological_locomotion_class":source_biological_class(eligible,classes) if eligible else None,
            "radiation_slope_per_100Wm2":slope,
            "source_siteyear_recorded_contexts":s["weather_context_count"],
            "source_siteyear_weather_qualified_contexts":s["weather_context_supported"],
            **sign_pattern(contexts)
        })
    return rows


def diagnose(earlier,external,early_contexts,later_contexts):
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["version"]!="original-GPS-shortwave-nonreplication-diagnostic-v0":
        raise ValueError("Post-exposure source sensitivity contract not frozen")
    if (earlier["complete_fixed_source_archive_denominator"]!=24
        or len(external["all_24_source_study_slope_means"])!=24
        or early_contexts["version"]!="original-gps-solar-population-weather-v0"
        or later_contexts["version"]!="external-24-original-GPS-solar-radiation-validation-v0"):
        raise ValueError("Original first study and heldout 24-source denominators modified")
    verdict=external["source_primary_radiation_per_100Wm2"]["predeclared_external_replication_decision"]
    if verdict!="NEGATIVE_DIRECTION_NOT_REPLICATED_IN_HELDOUT_SOURCE_SAMPLE":
        raise ValueError("No retrospective change to frozen original source first nonreplication")
    rows=build_source_entries(
        earlier,external,early_contexts,later_contexts,
        contract["ecological_interpretation"]["frozen_taxa_groups"])
    old=[r for r in rows if r["cohort"]=="earlier" and r["radiation_slope_per_100Wm2"] is not None]
    new=[r for r in rows if r["cohort"]=="external" and r["radiation_slope_per_100Wm2"] is not None]
    if len(rows)!=48 or len(old)!=10 or len(new)!=10:
        raise ValueError("Incomplete source-inclusive two-cohort initial ecological denominators")
    ids=[id for row in rows for id in row["study_ids"]]
    if len(ids)!=48 or len(set(ids))!=48:
        raise ValueError("Original public source study IDs overlap; cannot compare as 48 source units")
    av=[r["radiation_slope_per_100Wm2"] for r in old]
    bv=[r["radiation_slope_per_100Wm2"] for r in new]
    def insist(a,b):
        if abs(a-b)>1e-12:raise ValueError("Original frozen radiation effect cannot be rewritten")
    insist(mean(av),earlier["study_equal_univariate_within_tagged_animal_climate_slopes"]["shortwave_Wm2"]["study_equal_mean"])
    insist(mean(bv),external["source_primary_radiation_per_100Wm2"]["equal_original_source_study_mean"])
    main=two_source_set_comparison(av,bv)
    class_frame={}
    for cl in contract["ecological_interpretation"]["frozen_taxa_groups"]:
        source=[r for r in rows if r["ecological_locomotion_class"]==cl]
        earlier_vals=[r["radiation_slope_per_100Wm2"] for r in source if r["cohort"]=="earlier"]
        external_vals=[r["radiation_slope_per_100Wm2"] for r in source if r["cohort"]=="external"]
        pooled=earlier_vals+external_vals
        class_frame[cl]={
            "earlier_original_studies":len(earlier_vals),
            "external_original_studies":len(external_vals),
            "earlier_source_mean":mean(earlier_vals) if earlier_vals else None,
            "external_source_mean":mean(external_vals) if external_vals else None,
            "all_source_mean":mean(pooled) if pooled else None,
            "all_source_bootstrap95":mean_ci(pooled,seed=SEED+3),
            "signs_negative":sum(v<0 for v in pooled),
            "signs_positive":sum(v>0 for v in pooled),
            "post_result_class_exploration_only":True,
        }
    signcounts=dict(Counter(r["within_original_source_study_context_sign_consistency"]
                            for r in rows if r["radiation_slope_per_100Wm2"] is not None))
    cohort_source={
        c:{"all_registered_source_studies":24,
           "source_studies_with_shortwave_slope":len([
               r for r in rows if r["cohort"]==c and r["radiation_slope_per_100Wm2"] is not None]),
           "source_studies_without_shortwave_slope":len([
               r for r in rows if r["cohort"]==c and r["radiation_slope_per_100Wm2"] is None])}
        for c in ("earlier","external")
    }
    return {
        "version":contract["version"],
        "post_first_results_date":"2026-10-25",
        "prior_frozen_external_replication_decision_UNCHANGED":verdict,
        "all_48_previously_frozen_source_studies_included":len(rows),
        "first_24_and_external_24_original_source_weather_observation_coverages":cohort_source,
        "study_equal_original_shortwave_slope_two_cohort_difference":main,
        "post_result_ecological_taxon_class_source_descriptions":class_frame,
        "within_study_source_siteyear_sign_consistency":signcounts,
        "all_original_studies_anonymized_source_descriptions":rows,
        "claim_ceiling":"Post-result descriptive diagnostic, not a new independent confirmation, solar-altitude-adjusted radiation mechanism, or proof two original source cohort means differ. The source-label permutation is a nonrandom exchangeability reference; raw GPS/time and environment are not exported."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    r=diagnose(*[json.loads(x.read_text(encoding="utf-8")) for x in
                 (EARLIER,EXTERNAL,EARLIER_CONTEXTS,EXTERNAL_CONTEXTS)])
    (args.out/"full48_original_source_radiation_nonreplication_diagnostic.json").write_text(
        json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("ORIGINAL_SHORTWAVE_NONREPLICATION_DIAGNOSTIC "+
          json.dumps({k:v for k,v in r.items()
                      if k!="all_original_studies_anonymized_source_descriptions"},
                      sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
