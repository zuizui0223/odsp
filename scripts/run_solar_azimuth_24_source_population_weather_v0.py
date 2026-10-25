"""Source-primary solar-direction ecology in weather contexts across ALL 24 frozen GPS archives.

All source files, statuses and native taxa are retained. Observations never expose
original GPS coordinates, original individual IDs, exact UTC times, grid centers
or per-animal coefficients. Every prior v2 GPS directional result must replay
exactly BEFORE any new ERA5 hourly weather request is made.

Weather slopes are observational single-predictor within-animal fixed
month × four-hour apparent-solar-time associations, NOT causal estimands.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime,timedelta
import json
import math
from pathlib import Path
from statistics import mean
from scripts.movebank_native_ecology_20261019 import (
    HERE,original_files,checksum_and_download
)
from scripts.global_solar_azimuth_12_new_original_events_v1 import (
    load_source_taxa
)
from scripts.solar_azimuth_macro_v0 import (
    analyze_taxon,directional_step,_bootstrap
)
from scripts.solar_azimuth_era5_wind_v0 import (
    year_request_parameters,get_original_hourly_response,validate_and_parse_weather,
    wind_flow_to,wrap_cos_degrees
)

CONTRACT=HERE/"research/SOLAR_AZIMUTH_24_SOURCE_MULTI_POPULATION_ERA5_V0_CONTRACT.json"
SOURCE=HERE/"research/GLOBAL_SOLAR_AZIMUTH_NEW24_PROVIDER_FROZEN_SOURCE_FILE_MANIFEST_20261025.json"
REFERENCE=HERE/"research/GLOBAL_SOLAR_AZIMUTH_NEW24_ORIGINAL_GPS_FIRST_V2_RESULT_20261025.json"
SLOPE_VARS={
    "wind_sun_cos":(0,0.12,1.0),
    "windspeed_ms":(1,0.8,1.0),
    "shortwave_Wm2":(2,60.0,100.0),
    "temperature_C":(3,2.0,5.0)
}
RESPONSE_NAMES=("sunward_cos","windflow_cos","wind_sun_cos",
                "wind_speed_100m_ms","shortwave_Wm2","temperature_2m_C")


class WeatherSourceHold(ValueError):
    pass


def check_24_original_source_contract():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    m=json.loads(SOURCE.read_text(encoding="utf-8"))
    r=json.loads(REFERENCE.read_text(encoding="utf-8"))
    if c["version"]!="original-gps-solar-population-weather-v0":
        raise WeatherSourceHold("Wrong preregistered ecological weather route")
    files=m["source_file_entries"]
    originals=r["all_preselected_source_originals"]
    if len(files)!=24 or len(originals)!=24:
        raise WeatherSourceHold("Fixed 24 original source files incomplete")
    if [x["package_uuid"] for x in files]!=[x["package_uuid"] for x in originals]:
        raise WeatherSourceHold("Previous GPS source roster and weather source frame disagree")
    if len({x["package_uuid"] for x in files})!=24:
        raise WeatherSourceHold("Source UUID repeated")
    for f,g in zip(files,originals):
        if f["status"]!="ORIGINAL_FILE_METADATA_ADMISSIBLE" or f["original_file"] is None:
            raise WeatherSourceHold("Original file not provider metadata-qualified")
        if g["source_state"]!="original_MD5_verified_source_analyzed":
            raise WeatherSourceHold("Original v2 first source GPS did not pass source MD5")
        if set(f["original_species_labels"])!=set(g["registry_species_labels"]):
            raise WeatherSourceHold("Original source native taxon roster changed")
    return c,files,{x["package_uuid"]:x for x in originals}


def _original_source_replay(tracks,coverage,previous):
    """No new weather calls until every original native GPS group is reproduced."""
    refs={x["taxon"]:x for x in previous["source_taxa"]}
    if set(refs)!=set(tracks):
        raise WeatherSourceHold("Frozen previous native species roster changed")
    replayed=0
    per_taxon={}
    for taxon in sorted(tracks):
        old=refs[taxon]
        if old["result_status"]=="NO_SOURCE_TAXON_RECORDS":
            if coverage[taxon]["original_taxon_rows"]!=0:
                raise WeatherSourceHold("Original taxonomy unmatched-roster changed")
            per_taxon[taxon]="NO_SOURCE_TAXON_RECORDS"
            continue
        observed=analyze_taxon({
            animal:list(fixes.values()) for animal,fixes in tracks[taxon].items()
        })
        if observed["status"]!=old["result_status"]:
            raise WeatherSourceHold("Frozen original GPS taxon status changed")
        if observed["supported_individuals"]!=old["qualified_individuals"]:
            raise WeatherSourceHold("Frozen GPS source animal count no longer replays")
        prior=old["analysis"]
        if observed["daylight_directional_qualified_steps"]!=prior["daylight_directional_qualified_steps"]:
            raise WeatherSourceHold("Frozen original GPS solar step count differs")
        if old["result_status"]=="descriptive_source_estimated":
            for key in ("raw_toward_sun_mean_cos","clock_adjusted_excess_cos",
                        "compass_independence_excess_cos"):
                now=observed["results"][key]["mean"]
                reference=prior["results"][key]["mean"]
                if now is None or reference is None or abs(now-reference)>1e-12:
                    raise WeatherSourceHold("Frozen original GPS sun direction mean did not reproduce")
        per_taxon[taxon]=observed["status"]
        replayed+=1
    return {"original_GPS_first_source_taxa_replayed":len(refs),
            "original_GPS_first_source_analyzable_taxa_replayed":replayed,
            "prior_original_GPS_taxon_statuses":per_taxon}


def original_directional_grid_years(hour_fixes):
    """Only signed-direction-INDEPENDENT animal count/step coverage selects cells.

    Input fixed original source GPS fixes in ephemeral memory. Every qualifying
    interval is kept until deterministic support selection is complete.
    """
    cells=defaultdict(lambda:{"animal_ids":set(),"dates":set(),"steps":[]})
    for animal,fixes in hour_fixes.items():
        obs=sorted(fixes.values())
        for a,b in zip(obs,obs[1:]):
            step=directional_step(a,b)
            if step is None:
                continue
            middle=a[0]+(b[0]-a[0])/2
            if not 1940<=middle.year<=2025:
                continue
            lat=(a[1]+b[1])/2
            lon=((a[2]+((b[2]-a[2]+180)%360-180)/2+180)%360)-180
            key=(math.floor(lat),math.floor(lon),middle.year)
            v=cells[key]
            v["animal_ids"].add(animal)
            v["dates"].add(step.solar_date)
            v["steps"].append((
                animal,middle.replace(minute=0,second=0,microsecond=0),
                step.solar_date,step.solar_hour,
                step.bearing,step.sun_azimuth
            ))
    candidates=[
        (key,value) for key,value in cells.items()
        if len(value["animal_ids"])>=3 and len(value["steps"])>=30
        and len(value["dates"])>=3
    ]
    candidates.sort(key=lambda item:(
        -len(item[1]["animal_ids"]),-len(item[1]["steps"]),item[0]))
    return candidates[:2],{
        "original_directional_gridyears":len(cells),
        "support_qualified_gridyears":len(candidates),
        "selected_top_two_gridyears":min(2,len(candidates)),
        "selection_is_heading_sign_blind":True
    }


def latitude_band(lat_floor):
    band=(abs(lat_floor+0.5)//15)*15
    band=int(min(band,75))
    return {"hemisphere":"N" if lat_floor>=0 else "S",
            "absolute_latitude_band_degrees":[band,band+15]}


def within_animal_weather_slope(observations,predictor):
    ix,sdmin,unit=SLOPE_VARS[predictor]
    groups=defaultdict(list)
    for o in observations:
        groups[(o["utc_hour"].month,int(o["solar_hour"]//4))].append(o)
    n_valid_blocks=0
    n_valid_steps=0
    numerator=denominator=0.0
    for rows in groups.values():
        if len(rows)<8 or len({x["solar_day"] for x in rows})<3:
            continue
        xs=[x["variables"][ix+2] for x in rows]
        ys=[x["variables"][0] for x in rows]
        mx,my=mean(xs),mean(ys)
        xx=sum((x-mx)**2 for x in xs)
        if xx/len(rows)<sdmin*sdmin:
            continue
        numerator+=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
        denominator+=xx
        n_valid_blocks+=1
        n_valid_steps+=len(rows)
    if n_valid_blocks<2 or n_valid_steps<20 or denominator<=1e-12:
        return None
    return numerator/denominator*unit


def summary_from_animal_values(values):
    return {
      "original_tagged_animals":len(values),
      "mean":mean(values) if len(values)>=5 else None,
      "source_animal_bootstrap95":_bootstrap(values) if len(values)>=5 else None,
      "animals_positive":sum(x>0 for x in values),
      "animals_negative":sum(x<0 for x in values),
      "status":"descriptive_within_tagged_source_animals"
            if len(values)>=5 else "INSUFFICIENT_ANIMAL_OR_ENVIRONMENT_VARIATION"
    }


def source_siteyear_environment_response(key,original_rows,weather):
    """Same original GPS steps for solar/wind/exposure; time-block x-y slopes."""
    rows=[]
    original_count=len(original_rows)
    for animal,utc_hour,solar_day,solar_hour,bearing,sun_azimuth in original_rows:
        hourly=weather.get(utc_hour)
        if hourly is None:
            continue
        speed,wind_from,shortwave,temperature=hourly
        to=wind_flow_to(wind_from)
        cols=(
            wrap_cos_degrees(bearing,sun_azimuth),
            wrap_cos_degrees(bearing,to),
            wrap_cos_degrees(to,sun_azimuth),
            speed,shortwave,temperature
        )
        rows.append({"animal":animal,"utc_hour":utc_hour,
                     "solar_day":solar_day,"solar_hour":solar_hour,
                     "variables":cols})
    fraction=len(rows)/original_count if original_count else 0
    output={
        "original_GPS_qualified_sunlight_steps_in_gridyear":original_count,
        "weather_matched_same_original_GPS_steps":len(rows),
        "original_GPS_hourly_weather_join_fraction":fraction,
        "weather_environmental_effect_status":"SOURCE_WEATHER_HOLD",
        "environmental_group_means":None,
        "within_animal_clock_month_weather_associations":None
    }
    if fraction<.9:
        output["reason"]="Frozen weather coverage below 90 percent original GPS steps"
        return output
    by_animal=defaultdict(list)
    for x in rows:
        by_animal[x["animal"]].append(x)
    admitted={
        animal:sample for animal,sample in by_animal.items()
        if len(sample)>=10 and len({x["solar_day"] for x in sample})>=3
    }
    output["observed_weather_qualified_original_tagged_animals"]=len(admitted)
    if len(admitted)<5:
        output["reason"]="Fewer than five original tagged animals meet weather sampling support"
        return output
    individuals=[
        tuple(mean(r["variables"][i] for r in sample) for i in range(len(RESPONSE_NAMES)))
        for sample in admitted.values()
    ]
    output["environmental_group_means"]={
        k:{"mean":mean(x[i] for x in individuals),
           "source_animal_bootstrap95":_bootstrap([x[i] for x in individuals]),
           "units":("W/m²" if k=="shortwave_Wm2" else
                    "m/s" if k=="wind_speed_100m_ms" else
                    "°C" if k=="temperature_2m_C" else "cosine")}
        for i,k in enumerate(RESPONSE_NAMES)
    }
    associations={}
    for pred in SLOPE_VARS:
        slopes=[v for v in (within_animal_weather_slope(sample,pred)
                             for sample in admitted.values()) if v is not None]
        associations[pred]=summary_from_animal_values(slopes)
    output["within_animal_clock_month_weather_associations"]=associations
    output["weather_environmental_effect_status"]="SOURCE_GROUP_OBSERVED_ENVIRONMENT_DESCRIPTION"
    return output


def _one_study_source(source,previous,out):
    uuid=source["package_uuid"]
    entry={
        "source_package_uuid":uuid,"source_dois":source["original_dois"],
        "source_study_ids":source["source_study_ids"],
        "source_taxa":[],
        "original_source_status":"SOURCE_HOLD",
        "source_original_replay_success":False,
        "source_weather_model":"era5_hourly",
        "source_climate_request_count":0,
        "weather_requests_checksum_receipts":[]
    }
    original=source["original_file"]
    private=out/("private_original_"+uuid+".csv")
    try:
        matches=[x for x in original_files(uuid)
                 if x["bitstream_uuid"]==original["bitstream_uuid"]]
        if len(matches)!=1 or (matches[0]["bytes"]!=original["bytes"]
            or matches[0]["checksum"]!=original["checksum"]):
            raise WeatherSourceHold("Original Movebank provider UUID/bytes/checksum changed")
        entry["original_source_checksum_receipt"]=checksum_and_download(matches[0],private)
        tracks,coverage,original_counts=load_source_taxa(
            private,original["filename"],source["original_species_labels"])
        entry["source_original_validated_native_rows"]=original_counts["original_total_rows"]
        entry["previous_source_results_replayed"]=_original_source_replay(
            tracks,coverage,previous)
        entry["source_original_replay_success"]=True

        # Select every native taxon grid-year BEFORE ANY NEW ERA5 request.
        source_choices={}
        taxon_roster={}
        for taxon in source["original_species_labels"]:
            selection,counts=original_directional_grid_years(tracks[taxon])
            source_choices[taxon]=selection
            taxon_roster[taxon]={"taxon":taxon,"original_source_gridyear_support":counts,
                "source_gridyear_weather_contexts":[]}
            tracks[taxon].clear()
        weather_keys=sorted({key for selections in source_choices.values()
                             for key,value in selections})
        if len(weather_keys)>8:
            raise WeatherSourceHold("More than eight original support-ranked source weather grids")
        weather={}
        for key in weather_keys:
            lat,lon,year=key
            try:
                params=year_request_parameters(lat,lon,year)
                raw=get_original_hourly_response(params)
                record,receipt=validate_and_parse_weather(raw,year)
                weather[key]=record
                entry["weather_requests_checksum_receipts"].append(
                    {"source_gridyear_request_number":
                     len(entry["weather_requests_checksum_receipts"])+1,
                     **receipt})
            except Exception as exc:
                weather[key]=None
                entry["weather_requests_checksum_receipts"].append({
                    "source_gridyear_request_number":
                    len(entry["weather_requests_checksum_receipts"])+1,
                    "status":"SOURCE_WEATHER_HOLD",
                    "error_type":type(exc).__name__})
        entry["source_climate_request_count"]=len(weather_keys)
        # Do not substitute different year/cell for failed weather or weak effects.
        for taxon in source["original_species_labels"]:
            result=taxon_roster[taxon]
            for order,(key,subset) in enumerate(source_choices[taxon],1):
                sample={
                    "source_taxon_modal_original_gridyear_rank":order,
                    "original_gridyear_source_n_tagged_animals":len(subset["animal_ids"]),
                    "original_gridyear_source_n_steps":len(subset["steps"]),
                    "original_gridyear_source_n_solar_dates":len(subset["dates"]),
                    "geographic_latitude_band_not_coordinate":latitude_band(key[0]),
                    "original_UTC_observation_year":key[2],
                    "source_weather_hour_model":"era5"
                }
                if weather.get(key) is None:
                    sample.update(weather_environmental_effect_status="SOURCE_WEATHER_HOLD",
                                  reason="Original ERA5 hourly weather source unavailable",
                                  original_GPS_hourly_weather_join_fraction=0,
                                  environmental_group_means=None,
                                  within_animal_clock_month_weather_associations=None)
                else:
                    sample.update(source_siteyear_environment_response(
                        key,subset["steps"],weather[key]))
                result["source_gridyear_weather_contexts"].append(sample)
            entry["source_taxa"].append(result)
        entry["original_source_status"]="ORIGINAL_GPS_REPLAYED_WEATHER_SCREENED"
    except Exception as exc:
        entry["source_taxa"]=[{"taxon":taxon,"original_source_status":"SOURCE_HOLD",
             "source_gridyear_weather_contexts":[]} for taxon in source["original_species_labels"]]
        entry["original_source_status"]="SOURCE_HOLD"
        entry["failure_type"]=type(exc).__name__
        entry["failure_stage"]="original_integrity_OR_preweather_replay_OR_source_weather"
    finally:
        private.unlink(missing_ok=True)
    return entry


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--shard",type=int,choices=range(6),required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    contract,files,previous=check_24_original_source_contract()
    all_sources=[]
    for i,original in enumerate(files):
        if i%6!=args.shard:
            continue
        result=_one_study_source(original,previous[original["package_uuid"]],args.out)
        all_sources.append(result)
        print("SOLAR_ORIGINAL_SOURCE_POPULATION_WEATHER "+
              json.dumps(result,sort_keys=True,ensure_ascii=False),flush=True)
    if len(all_sources)!=4:
        raise WeatherSourceHold("Frozen source frame six shards must each contain four sources")
    outcomes=[
       context
       for source in all_sources for taxon in source["source_taxa"]
       for context in taxon["source_gridyear_weather_contexts"]
    ]
    summary={
        "version":"original-gps-solar-population-weather-v0",
        "source_shard":args.shard,
        "fixed_original_source_archives_in_shard":4,
        "source_MD5_and_original_first_outcomes_replayed":sum(
            source["source_original_replay_success"] for source in all_sources),
        "original_source_HOLDs":sum(
            source["original_source_status"]=="SOURCE_HOLD" for source in all_sources),
        "source_environmental_modal_gridyear_contexts_attempted":len(outcomes),
        "source_ERA5_observed_contexts":sum(
            x.get("weather_environmental_effect_status")==
            "SOURCE_GROUP_OBSERVED_ENVIRONMENT_DESCRIPTION" for x in outcomes),
        "source_modal_gridyear_environment_HOLDs":sum(
            x.get("weather_environmental_effect_status")!="SOURCE_GROUP_OBSERVED_ENVIRONMENT_DESCRIPTION" for x in outcomes),
        "modelled_ERA5_original_gridyear_API_requests":sum(
            source["source_climate_request_count"] for source in all_sources),
        "source_groups":all_sources,
        "nonclaim":"Study and site-years NOT independent biomes; slopes are weather observational univariate within month/solar clock, not solar/wind mechanisms, and wind at 100m is not observed animal-flight altitude."
    }
    (args.out/("original_source_population_weather_shard_"+str(args.shard)+".json")).write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SOLAR_SOURCE_POP_WEATHER_SUMMARY "+json.dumps(
        {k:v for k,v in summary.items() if k!="source_groups"},
        sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
