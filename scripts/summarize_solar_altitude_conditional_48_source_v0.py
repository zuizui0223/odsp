"""Source-study-equal summary of post-result original GPS solar elevation sensitivity.

Preserve 48 original public study archives in the denominator, including the
28 previously radiation-unidentifiable sources and original provider/ERA5
drift holds. Use one equal source-study ID, NOT per GPS fix, animal, original
source taxon, selected weather grid or sampled weather hour. Do not change
the earlier first and heldout source effect results or verdict.
"""
from __future__ import annotations
from collections import defaultdict
import argparse
import json
from pathlib import Path
import random
from statistics import mean

from scripts.movebank_native_ecology_20261019 import HERE

CONTRACT=HERE/"research/SOLAR_RADIATION_SOLAR_ALTITUDE_CONDITIONAL_48_SOURCE_V0_CONTRACT.json"
INPUT=HERE/"research/SOLAR_ALTITUDE_GPS_48_SOURCE_FIRST_ALL_RESULTS_20261025.json"
SEED=20261025


def cluster_ci(values,draws=2000,seed=SEED):
    if len(values)<6:
        return None
    rng=random.Random(seed)
    n=len(values)
    res=sorted(mean(values[rng.randrange(n)] for _ in range(n))
               for _ in range(draws))
    return [res[int(.025*draws)],res[min(draws-1,int(.975*draws)-1)]]


def source_study_equal_effect(study):
    by_taxon=defaultdict(list)
    preold=defaultdict(list)
    preweather=0
    replay=0
    for row in study["siteyear_contexts"]:
        if row.get("original_animal_shortwave_slope_replayed"):
            replay+=1
        if row["source_status"]=="GEOMETRY_ADJUSTED_GROUP_OBSERVED":
            by_taxon[row["taxon"]].append(
                row["geometric_solar_adjustment_effect"]["mean_slope_per100_Wm2"])
            preold[row["taxon"]].append(
                row["source_previous_irradiance_slope_per_100Wm2"])
    vals=[mean(a) for a in by_taxon.values() if a]
    old=[mean(a) for a in preold.values() if a]
    return {
        "source_original_uuid":study["source_package_uuid"],
        "source_original_cohort":study["cohort"],
        "original_archive_study_ID":study["original_study_ids"],
        "source_MD5_verified":study["original_provider_MD5_verified"],
        "source_prior_GPS_effect_replayed_before_new_weather":
            study["all_native_original_GPS_effects_replayed_before_ERA5"],
        "source_original_native_taxa_count":len(study["original_native_taxa"]),
        "original_radiation_supported_contexts_attempted":len(study["siteyear_contexts"]),
        "original_radiation_contexts_replayed_first_weather":replay,
        "original_contexts_solar_altitude_adjusted":sum(
            len(v) for v in by_taxon.values()),
        "original_contexts_weather_replay_or_model_HOLD":sum(
            c["source_status"] in ("SOURCE_WEATHER_REPLAY_HOLD","SOURCE_WEATHER_HOLD")
            for c in study["siteyear_contexts"]),
        "source_adjusted_equal_taxon_siteyear_mean_per100Wm2":
            mean(vals) if vals else None,
        "original_slope_before_solar_altitude_on_matching_siteyears":
            mean(old) if old else None,
        "note":"Prior original slope averages over a broader qualifying tagged-animal set than the altitude-adjusted geometry-identifiable animals. The difference cannot estimate a solar-geometry mediation proportion."
    }


def full_study_source_summary(original):
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if c["version"]!="original-GPS-irradiance-conditioned-on-solar-altitude-v0":
        raise ValueError("No frozen physical geometry sensitivity contract")
    selected=c["selected_existing_study_originals_for_sensitivity"]
    held=c["existing_nonestimable_study_originals_retained"]
    if len(selected)!=20 or len(held)!=28 or len(original["all_source_results"])!=20:
        raise ValueError("All 48 original public source study descriptors required")
    provided={r["source_package_uuid"]:r for r in original["all_source_results"]}
    if set(provided)!={x["source_uuid"] for x in selected}:
        raise ValueError("Original source descriptor roster differs from previous source identifiability")
    rows=[source_study_equal_effect(provided[x["source_uuid"]]) for x in selected]
    for x in held:
        rows.append({
            "source_original_uuid":x["source_uuid"],
            "source_original_cohort":x["cohort"],
            "source_original_archived_study_radiation_unidentifiable":True,
            "source_adjusted_equal_taxon_siteyear_mean_per100Wm2":None,
            "original_slope_before_solar_altitude_on_matching_siteyears":None,
            "original_radiation_supported_contexts_attempted":0,
            "original_contexts_solar_altitude_adjusted":0,
            "original_contexts_weather_replay_or_model_HOLD":0
        })
    if len(rows)!=48 or len({r["source_original_uuid"] for r in rows})!=48:
        raise ValueError("Do not drop source-unavailable original study sample entries")
    cohorts={}
    for label in ("earlier","external"):
        sources=[r for r in rows if r["source_original_cohort"]==label]
        vals=[r["source_adjusted_equal_taxon_siteyear_mean_per100Wm2"]
              for r in sources if r["source_adjusted_equal_taxon_siteyear_mean_per100Wm2"] is not None]
        original=[r["original_slope_before_solar_altitude_on_matching_siteyears"]
                  for r in sources if r["source_adjusted_equal_taxon_siteyear_mean_per100Wm2"] is not None]
        cohorts[label]={
            "all_original_study_archives_in_frozen_source_set":len(sources),
            "prior_radiation_slope_support_study_archives":10,
            "geometry_adjusted_radiation_source_archives":len(vals),
            "source_studies_source_weather_or_geometry_HOLDs":10-len(vals),
            "geometry_adjusted_mean_slope_per100Wm2":mean(vals) if vals else None,
            "source_study_bootstrap95":cluster_ci(vals,seed=SEED+(label=="external")),
            "source_study_means_negative":sum(v<0 for v in vals),
            "source_study_means_positive":sum(v>0 for v in vals),
            "prior_unadjusted_siteyear_source_mean_on_geometry_support":
                mean(original) if original else None,
            "caution":"Conditional geometry slopes and prior source means can use different original tagged-animal subsets. No causal effect or attenuation fraction."
        }
    all_valid=[
       r["source_adjusted_equal_taxon_siteyear_mean_per100Wm2"]
       for r in rows if r["source_adjusted_equal_taxon_siteyear_mean_per100Wm2"] is not None
    ]
    difference=None
    if (cohorts["earlier"]["geometry_adjusted_radiation_source_archives"]>=6 and
        cohorts["external"]["geometry_adjusted_radiation_source_archives"]>=6):
        a=[r["source_adjusted_equal_taxon_siteyear_mean_per100Wm2"] for r in rows
           if r["source_original_cohort"]=="earlier" and
           r["source_adjusted_equal_taxon_siteyear_mean_per100Wm2"] is not None]
        b=[r["source_adjusted_equal_taxon_siteyear_mean_per100Wm2"] for r in rows
           if r["source_original_cohort"]=="external" and
           r["source_adjusted_equal_taxon_siteyear_mean_per100Wm2"] is not None]
        difference=mean(a)-mean(b)
    return {
        "version":"original-GPS-irradiance-conditioned-on-solar-altitude-v0",
        "all_original_source_archives":48,
        "prior_radiation_identifiable_studies_selected_for_geometry":20,
        "previously_original_unidentifiable_studies_retained":28,
        "frozen_previous_signed_radiation_replication_decision_UNCHANGED":
            "NEGATIVE_DIRECTION_NOT_REPLICATED_IN_HELDOUT_SOURCE_SAMPLE",
        "source_weather_GPS_replay_verified_studies":sum(
            x["source_prior_GPS_effect_replayed_before_new_weather"] for x in rows
            if "source_prior_GPS_effect_replayed_before_new_weather" in x),
        "source_inferred_marginal_weather_replay_contexts":sum(
            x["original_radiation_contexts_replayed_first_weather"] for x in rows
            if "original_radiation_contexts_replayed_first_weather" in x),
        "source_solar_altitude_adjusted_contexts":sum(
            x["original_contexts_solar_altitude_adjusted"] for x in rows),
        "per_prior_source_cohort":cohorts,
        "all_source_study_adjusted_mean":mean(all_valid) if all_valid else None,
        "all_source_study_adjusted_descriptive_bootstrap95":cluster_ci(all_valid),
        "new_geometry_adjusted_between_original_cohort_mean_difference":difference,
        "all_48_source_archived_study_descriptions":rows,
        "claim_ceiling":"Post-result geometry sensitivity only. Identifiability/ERA5 source replay may reduce sample. No causal animal irradiance choice, sunlight-compass behavior, wind mediation or globally representative macroecological mean. Never overwrite the prior nonreplicated signed hypothesis."
    }


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--input",type=Path,default=INPUT)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    r=full_study_source_summary(json.loads(args.input.read_text(encoding="utf-8")))
    (args.out/"full48_solar_elevation_weather_source_study_sensitivity.json").write_text(
        json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SUN_ALTITUDE_SHORTWAVE_48_SOURCE_SUMMARY "+
          json.dumps({k:v for k,v in r.items()
                      if k!="all_48_source_archived_study_descriptions"},
                     sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
