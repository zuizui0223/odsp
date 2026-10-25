"""FIRST solar bearing + ERA5 hourly weather analysis of 24 new source studies.

The exact 24 source UUIDs, 24 nonhuman single-taxon labels, original provider
bitstreams and exact original checksums were frozen WITHOUT viewing any new
source-specific solar direction or ERA5 shortwave observations. The negative
solar-radiation hypothesis was derived from the OLDER 24-study observational
sample and is prospectively assessed here without source replacement.

This is an *external source-archive directional replication* under fixed GPS
and weather sampling rules. It is not an independently sampled world biome
experiment, and raw animal GPS records must never leave the runner.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import (
    HERE,original_files,checksum_and_download
)
from scripts.global_solar_azimuth_12_new_original_events_v1 import load_source_taxa
from scripts.solar_azimuth_macro_v0 import analyze_taxon
from scripts.solar_azimuth_era5_wind_v0 import (
    year_request_parameters,get_original_hourly_response,validate_and_parse_weather
)
from scripts.run_solar_azimuth_24_source_population_weather_v0 import (
    original_directional_grid_years,source_siteyear_environment_response,
    latitude_band
)

CONTRACT=HERE/"research/SOLAR_RADIATION_EXTERNAL_24_ORIGINAL_SOURCE_V0_CONTRACT.json"
SOURCE_MANIFEST=HERE/"research/SOLAR_RADIATION_EXTERNAL_24_PROVIDER_FROZEN_SOURCE_MANIFEST_20261025.json"


def verify_external_frozen_frame():
    spec=json.loads(CONTRACT.read_text(encoding="utf-8"))
    src=json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if spec["version"]!="external-24-original-GPS-solar-radiation-validation-v0":
        raise ValueError("First external original GPS solar-radiation study contract changed")
    if src["version"]!=spec["version"]:
        raise ValueError("Source-original metadata pre-outcome freeze not found")
    selected=spec["selected_source_roster"]
    originals=src["all_selected_original_source_entries"]
    if len(selected)!=24 or len(originals)!=24:
        raise ValueError("Not all new preselected source original archives retained")
    if [x["package_uuid"] for x in selected]!=[x["original_source_package_uuid"] for x in originals]:
        raise ValueError("External source order/UUID changed after source metadata freeze")
    for i,(a,b) in enumerate(zip(selected,originals),1):
        if (a["rank"]!=i or a["taxon"]!=b["original_taxon"] or
            a["expected_original_primary_csv_bytes"]!=b["expected_original_primary_csv_bytes"]):
            raise ValueError("Original source identity or pre-outcome expected bytes changed")
        if b["original_source_status"] not in ("ORIGINAL_FILE_METADATA_QUALIFIED","SOURCE_METADATA_HOLD"):
            raise ValueError("Unrecognized frozen provider metadata status")
        if b["original_source_status"]=="ORIGINAL_FILE_METADATA_QUALIFIED":
            original=b["original_file"]
            if not original or original["bytes"]!=a["expected_original_primary_csv_bytes"]:
                raise ValueError("Original provider full MD5 source identity missing")
    if src["original_GPS_positions_or_bearings_read"]!=0:
        raise ValueError("Original full provider event data were not shielded before freeze")
    return spec,originals


def source_original_analysis(original,out):
    uuid=original["original_source_package_uuid"]
    taxon=original["original_taxon"]
    result={
        "source_package_uuid":uuid,
        "source_study_ids":original["original_repository_study_ids"],
        "original_source_doIs":original["original_dois"],
        "original_taxon":taxon,
        "original_license_labels":original["original_licenses"],
        "source_status":"SOURCE_HOLD",
        "source_original_GPS_first_directional_result":None,
        "source_taxa":[{"taxon":taxon,"source_gridyear_weather_contexts":[]}],
        "source_weather_gridyear_attempts":0,
        "original_weather_source_receipts":[],
        "no_original_events_exported":True
    }
    if original["original_source_status"]!="ORIGINAL_FILE_METADATA_QUALIFIED":
        result["reason"]="Source metadata was frozen as SOURCE_HOLD; no replacement"
        return result

    file=original["original_file"]
    private=out/("private_external_source_"+uuid+".csv")
    try:
        check=[x for x in original_files(uuid) if x["bitstream_uuid"]==file["bitstream_uuid"]]
        if (len(check)!=1 or check[0]["bytes"]!=file["bytes"]
                or check[0]["checksum"]!=file["provider_checksum"]):
            raise ValueError("Frozen original provider CSV source UUID/MD5/size no longer matches")
        result["provider_original_source_checksum_receipt"]=checksum_and_download(check[0],private)
        tracks,coverage,count=load_source_taxa(private,file["original_file_name"],[taxon])
        result["original_source_rows_read"]=count["original_total_rows"]
        result["original_source_tagged_animals"]=coverage[taxon]["source_individuals"]
        result["original_source_taxonomy_validated_native_rows"]=coverage[taxon]["original_taxon_rows"]

        gps=analyze_taxon({
            animal:list(track.values()) for animal,track in tracks[taxon].items()
        })
        result["source_original_GPS_first_directional_result"]=gps
        # Keep original GPS first result even if no suitable source siteyear
        # supports hourly ERA5. Count-based source support selection is not
        # allowed to inspect solar-direction effect magnitudes.
        choices,selection_counts=original_directional_grid_years(tracks[taxon])
        result["source_taxa"][0]["original_source_gridyear_support"]=selection_counts
        tracks[taxon].clear()
        if len(choices)>2:
            raise ValueError("More than two predeclared original source weather contexts selected")
        result["source_weather_gridyear_attempts"]=len(choices)

        for ordinal,(gridyear,source_subset) in enumerate(choices,1):
            context={
                "source_taxon_modal_original_gridyear_rank":ordinal,
                "original_gridyear_source_n_tagged_animals":len(source_subset["animal_ids"]),
                "original_gridyear_source_n_steps":len(source_subset["steps"]),
                "original_gridyear_source_n_solar_dates":len(source_subset["dates"]),
                "geographic_latitude_band_not_coordinate":latitude_band(gridyear[0]),
                "original_UTC_observation_year":gridyear[2],
                "source_weather_hour_model":"era5",
                "weather_environmental_effect_status":"SOURCE_WEATHER_HOLD"
            }
            try:
                params=year_request_parameters(*gridyear)
                raw=get_original_hourly_response(params)
                weather,receipt=validate_and_parse_weather(raw,gridyear[2])
                context.update(source_siteyear_environment_response(
                    gridyear,source_subset["steps"],weather))
                result["original_weather_source_receipts"].append(
                    {"request_order":ordinal,**receipt})
            except Exception as exc:
                context.update({
                    "weather_environmental_effect_status":"SOURCE_WEATHER_HOLD",
                    "environmental_group_means":None,
                    "within_animal_clock_month_weather_associations":None,
                    "reason":"Frozen selected source hourly ERA5 unverified or unavailable"})
                result["original_weather_source_receipts"].append(
                    {"request_order":ordinal,"status":"SOURCE_WEATHER_HOLD",
                     "error_type":type(exc).__name__})
            result["source_taxa"][0]["source_gridyear_weather_contexts"].append(context)

        result["source_status"]="ORIGINAL_SOURCE_FIRST_GPS_AND_ERA5_OBSERVATIONS_COMPLETED"
    except Exception as exc:
        result["source_status"]="SOURCE_HOLD"
        result["source_taxa"][0]["source_gridyear_weather_contexts"]=[]
        result["failure_type"]=type(exc).__name__
        result["failure_stage"]="ORIGINAL_SOURCE_MD5_OR_ORIGINAL_GPS_OR_MODEL"
    finally:
        private.unlink(missing_ok=True)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--shard",required=True,type=int,choices=range(6))
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    contract,sources=verify_external_frozen_frame()
    records=[]
    for i,entry in enumerate(sources):
        if i%6!=args.shard:
            continue
        result=source_original_analysis(entry,args.out)
        records.append(result)
        print("SOLAR_RADIATION_EXTERNAL_FIRST_SOURCE "+
              json.dumps(result,sort_keys=True,ensure_ascii=False),flush=True)
    if len(records)!=4:
        raise ValueError("Original heldout source shard requires four frozen source UUIDs")
    contexts=[
        c for s in records for t in s["source_taxa"]
        for c in t.get("source_gridyear_weather_contexts",[])
    ]
    report={
        "version":"external-24-original-GPS-solar-radiation-validation-v0",
        "original_source_shard":args.shard,
        "new_unobserved_source_archives_in_shard":4,
        "original_provider_MD5_verified_sources":sum(
            s["source_status"]=="ORIGINAL_SOURCE_FIRST_GPS_AND_ERA5_OBSERVATIONS_COMPLETED"
            for s in records),
        "original_source_HOLD":sum(s["source_status"]=="SOURCE_HOLD" for s in records),
        "original_GPS_study_taxon_effect_supported":sum(
            s["source_original_GPS_first_directional_result"] is not None and
            s["source_original_GPS_first_directional_result"]["status"]==
                "descriptive_source_estimated" for s in records),
        "source_weather_selected_contexts":len(contexts),
        "source_weather_contexts_admitted":sum(
            c.get("weather_environmental_effect_status")==
             "SOURCE_GROUP_OBSERVED_ENVIRONMENT_DESCRIPTION" for c in contexts),
        "all_external_source_original_results":records,
        "nonclaim":"This source was completely unexposed to the prior solar-weather direction results, but public archives/individual field studies are not random independent world biomes. No causal shade avoidance or sunlight orientation inference."
    }
    (args.out/("heldout_original_24_source_shard_"+str(args.shard)+".json")).write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SOLAR_RADIATION_EXTERNAL_SHARD_SUMMARY "+
          json.dumps({k:v for k,v in report.items() if k!="all_external_source_original_results"},
                     sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
