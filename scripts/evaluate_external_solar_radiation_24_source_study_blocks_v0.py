"""Frozen directional source-block replication decision for 24 NEW GPS sources.

The external source UUIDs and sign <0 were frozen before opening ANY of
these original GPS displacements or ERA5 weather values. Source-group bootstrap
is descriptive across archived field-source study IDs, NOT a world-ecology
population p-value, causal sunlight effect, or direct solar-avoidance test.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from statistics import mean

from scripts.movebank_native_ecology_20261019 import HERE
from scripts.analyze_solar_azimuth_24_source_weather_study_blocks_v0 import (
    study_bootstrap_mean
)

CONTRACT=HERE/"research/SOLAR_RADIATION_EXTERNAL_24_ORIGINAL_SOURCE_V0_CONTRACT.json"
MANIFEST=HERE/"research/SOLAR_RADIATION_EXTERNAL_24_PROVIDER_FROZEN_SOURCE_MANIFEST_20261025.json"
INPUT=HERE/"research/SOLAR_RADIATION_EXTERNAL_24_SOURCE_FIRST_ALL_RESULTS_20261025.json"
VARS=("wind_sun_cos","windspeed_ms","shortwave_Wm2","temperature_C")


def analyze_external_heldout(original_results):
    spec=json.loads(CONTRACT.read_text(encoding="utf-8"))
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    if spec["version"]!="external-24-original-GPS-solar-radiation-validation-v0":
        raise ValueError("Unfrozen original GPS external source hypothesis")
    if original_results["version"]!=spec["version"]:
        raise ValueError("Wrong external original GPS weather response schema")
    roster=manifest["all_selected_original_source_entries"]
    samples=original_results["all_external_first_source_results"]
    if len(roster)!=24 or len(samples)!=24:
        raise ValueError("Every predeclared original source must remain in the external result")
    previous_ids=[x["original_source_package_uuid"] for x in roster]
    seen=[x["source_package_uuid"] for x in samples]
    if set(previous_ids)!=set(seen) or len(set(seen))!=24:
        raise ValueError("Pre-registered source frame missing or altered")
    samples=sorted(samples,key=lambda s:previous_ids.index(s["source_package_uuid"]))
    ids=[sid for x in samples for sid in x["source_study_ids"]]
    if len(ids)!=24 or len(set(ids))!=24:
        raise ValueError("Duplicate native original source study ID cannot be independent block")
    effects={}
    for key in VARS:
        effects[key]=[]
    source_details=[]
    for src in samples:
        taxon=src["source_taxa"][0]
        contexts=taxon["source_gridyear_weather_contexts"]
        taxon_effect={}
        for var in VARS:
            values=[
                c["within_animal_clock_month_weather_associations"][var]["mean"]
                for c in contexts
                if c.get("within_animal_clock_month_weather_associations") is not None
                and c["within_animal_clock_month_weather_associations"][var]["mean"] is not None
            ]
            taxon_effect[var]=mean(values) if values else None
            if values:
                effects[var].append(mean(values))
        direct=src["source_original_GPS_first_directional_result"]
        sun=direct["results"]["raw_toward_sun_mean_cos"]["mean"] if direct is not None else None
        source_details.append({
            "source_package_uuid":src["source_package_uuid"],
            "taxon":src["original_taxon"],
            "original_repository_study_ids":src["source_study_ids"],
            "original_source_status":src["source_status"],
            "source_MDB_provider_checksum_verified":
                bool(src.get("provider_original_source_checksum_receipt")),
            "source_first_GPS_directional_n_animals":
                direct["supported_individuals"] if direct is not None else None,
            "source_first_GPS_sunward_mean":
                sun,
            "source_modal_gridyear_contexts_attempted":len(contexts),
            "source_modal_gridyear_contexts_with_environmental_groups":sum(
                c.get("weather_environmental_effect_status")==
                "SOURCE_GROUP_OBSERVED_ENVIRONMENT_DESCRIPTION" for c in contexts),
            "source_study_equal_context_weather_slopes":taxon_effect,
        })
    results={}
    for var in VARS:
        values=effects[var]
        ci=study_bootstrap_mean(values)
        loo=[mean(values[:j]+values[j+1:]) for j in range(len(values))] if len(values)>2 else []
        results[var]={
            "all_frozen_source_archives":24,
            "supported_original_source_study_IDs":len(values),
            "equal_original_source_study_mean":mean(values) if values else None,
            "source_study_bootstrap95":ci,
            "source_study_means_negative":sum(x<0 for x in values),
            "source_study_means_positive":sum(x>0 for x in values),
            "leave_one_source_out_mean_range":[min(loo),max(loo)] if loo else None
        }
    primary=results["shortwave_Wm2"]
    if primary["supported_original_source_study_IDs"]<6:
        status="INSUFFICIENT_HELDOUT_STUDY_SUPPORT"
    elif primary["source_study_bootstrap95"] is not None and primary["source_study_bootstrap95"][1]<0:
        status="NEGATIVE_DIRECTION_REPLICATED_IN_HELDOUT_SOURCE_SAMPLE"
    else:
        status="NEGATIVE_DIRECTION_NOT_REPLICATED_IN_HELDOUT_SOURCE_SAMPLE"
    return {
        "version":spec["version"],
        "date":"2026-10-25",
        "original_sample_prior_effect_data_access":"NO_NEW_SOURCE_OUTCOME_OPEN_BEFORE_PREDECLARED_ROSTER",
        "previous_exploratory_original_24_source_mean_shortwave_slope_per_100Wm2":-0.019658718057344777,
        "first_external_original_source_study_frame":24,
        "original_study_IDs_source_blocks":24,
        "source_primary_radiation_per_100Wm2":{
            **primary,
            "predeclared_external_replication_decision":status,
            "strict_source_minimum":6,
            "preregistered_direction":"negative",
            "test":"2000 fixed-seed source-ID resample percentile 95% upper endpoint <0 and N>=6; not a global population p-value"
        },
        "all_four_environmental_slopes":results,
        "all_24_heldout_original_source_study_results":source_details,
        "limitations":"New original public archive sample only; original study IDs are distinct but local tagged animals/populations might overlap geographically or differ in sampling schedule. The within month/4-hour source slope can reflect residual sun-altitude and clock geometry, animal migration/route, weather and selection. Shortwave gridded ERA5 is not individual incident sunlight. No causal shade/solar compass effect, independent worldwide biome likelihood, or source animal-level global p-values."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,default=INPUT)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    result=analyze_external_heldout(
        json.loads(args.input.read_text(encoding="utf-8")))
    (args.out/"heldout_24_original_source_radiation_directional_test.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    headline={k:v for k,v in result.items() if k not in
              ("all_four_environmental_slopes","all_24_heldout_original_source_study_results")}
    print("SOLAR_RADIATION_HELDOUT_24_SOURCE_RESULT "+
          json.dumps(headline,sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
