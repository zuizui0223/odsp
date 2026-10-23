"""Independent Wyoming public GPS × monthly ERA5 seasonal ecology.

Post-outcome ecological test: Is source mule deer daylength association
conditionally identifiable after thermal and climatic water states?
Replays two locked original GPS source q/daylength means BEFORE climate lookups.
All output group-only; no GPS location, ID, timestamp or cell coordinates exported.
"""
import argparse,json,math
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean

from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download,daylength
from scripts.movebank_wyoming_two_ungulates_20261022 import (
    CONTRACT as ORIGINAL_SOURCE,streaming_time_selected_csv
)
from scripts.movebank_utah_diel_photoperiod_20261019 import one_taxon
from scripts.movebank_solar_movement_20261019 import valid_interval
from scripts.movebank_utah_era5_climate_20261019 import get_monthly_era5
from scripts.movebank_utah_calendar_condition_20261022 import partial_slope
from scripts.movebank_utah_shared_spatial_20261019 import cluster_interval

CONTRACT=HERE/"research/WYOMING_INDIVIDUAL_ERA5_DAYLIGHT_V0_20261023.json"

def source_admitted_daily(animals):
    """Recreate EXACT previous 10-valid-source-days/year admission before weather."""
    admitted=[]
    for _animal_id,selected_hour in animals.items():
        original=sorted(selected_hour.values())
        daily=defaultdict(lambda:{"day":[],"night":[],"lat":[],"lon":[]})
        for a,b in zip(original,original[1:]):
            v=valid_interval(a[0],a[1],a[2],b[0],b[1],b[2])
            if v is None:continue
            d,part,kmph,hours,lat=v
            z=daily[d];z[part].append(kmph);z["lat"].append(lat);z["lon"].append((a[2]+b[2])/2)
        by_year=defaultdict(list)
        for d,parts in daily.items():
            if len(parts["day"])<3 or len(parts["night"])<3:continue
            lat=mean(parts["lat"]);lon=mean(parts["lon"])
            q=math.log1p(__import__("statistics").median(parts["night"]))-math.log1p(__import__("statistics").median(parts["day"]))
            by_year[d.year].append((d,daylength(lat,d),q,(math.floor(lat),math.floor(lon)),(d.year,d.month)))
        for year,days in by_year.items():
            if len(days)>=10:
                admitted.append((_animal_id,year,days))
    return admitted

def exposure_frame(admitted):
    sources=defaultdict(set)
    for _animal,year,days in admitted:
        for day,daylight,q,cell,ym in days:
            sources[cell].add(ym)
    return sources

def monthly_observations(days,weather,minimum_days=4):
    """Collapse repeated daily fixes into ONE source animal-year-month response."""
    by_month=defaultdict(list)
    without_weather=0
    for d,light,q,cell,ym in days:
        w=weather.get((*cell,*ym))
        if w is None:
            without_weather+=1;continue
        by_month[ym].append((light,q,w["temperature_mean"],w["precip_minus_et0"]/100))
    rows=[]
    for ym,items in sorted(by_month.items()):
        if len(items)<minimum_days:continue
        rows.append((mean(v[2] for v in items),mean(v[3] for v in items),
                     mean(v[0] for v in items),mean(v[1] for v in items),ym[0],ym[1]))
    return rows,without_weather

def source_animal_slopes(admitted,weather):
    """Annual OLS with solar-calendar and hydroclimate; animal is inference unit."""
    keys={
      "monthly_unadjusted_daylight":(2,[],6,.2),
      "daylight_given_temperature":(2,[0],6,.2),
      "daylight_given_water_balance":(2,[1],6,.2),
      "daylight_given_temperature_and_water":(2,[0,1],8,.2),
      "temperature_given_daylight_and_water":(0,[2,1],8,.25),
      "water_given_daylight_and_temperature":(1,[2,0],8,.05)
    }
    slopes={k:defaultdict(list) for k in keys}
    total_days=sum(len(days) for _animal,year,days in admitted)
    no_era5_days=0;qualified_months=0;calendar_years=0
    months_available=[]
    for animal,year,days in admitted:
        months,missing=monthly_observations(days,weather)
        no_era5_days+=missing
        qualified_months+=len(months)
        months_available.append(len(months))
        if len(months)<6:continue
        if max(v[2] for v in months)-min(v[2] for v in months)<1.0:continue
        calendar_years+=1
        for key,(predictor,controls,minmonths,minstd) in keys.items():
            result=partial_slope(months,predictor,controls,minimum_n=minmonths,
                                 residual_sd=minstd,minimum_daylength_sd=.2)
            if result is not None:
                slopes[key][animal].append(result)
    outcomes={}
    for name,data in slopes.items():
        values=[mean(v) for v in data.values()]
        outcomes[name]={
            "individuals_with_identifiable_association":len(values),
            "qualified_individual_years":sum(len(z) for z in data.values()),
            "equal_animal_mean_association":mean(values) if len(values)>=5 else None,
            "independent_individual_bootstrap_95_interval":cluster_interval(values) if len(values)>=5 else None,
            "positive_animals":sum(v>0 for v in values),
            "negative_animals":sum(v<0 for v in values),
            "status":"exploratory_source_association" if len(values)>=5 else "INSUFFICIENT_IDENTIFIABLE_ANIMALS"
        }
    return {"source_eligible_animal_years":len(admitted),
            "source_eligible_observation_days":total_days,
            "individual_years_with_at_least_six_months_and_one_hour_daylength_range":calendar_years,
            "source_animal_months_with_four_days_and_weather":qualified_months,
            "source_days_without_era5_month":no_era5_days,
            "source_animal_years_ge6_complete_months":sum(n>=6 for n in months_available),
            "environment_adjusted_associations":outcomes,
            "measurement_boundary":"Single original field-study population per species; q is GPS displacement speed, not active time. ERA5 month is modeled coarse regional climate, P−ET0 not soil water/forage, and daylight controls cannot establish direct light causality."}

def main():
    cli=argparse.ArgumentParser();cli.add_argument("--out",required=True,type=Path)
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    freeze=json.loads(CONTRACT.read_text())
    if freeze["version"]!="wyoming-independent-individual-environment-daylight-v0":
        raise ValueError("The original-only environmental analysis was not source-frozen")
    src=json.loads(ORIGINAL_SOURCE.read_text())["source"]
    if src["original_md5"]!=freeze["original_source"]["md5"]:
        raise ValueError("Original source MD5 contract mismatch")
    result={"source":"Wyoming original mule deer and bighorn source, independent of Utah",
            "source_doi":src["doi"],"all_taxa":[],"original_GPS_effects_replayed":False,
            "source_exploratory_not_causal":True}
    path=args.out/"source_original_wyoming.csv"
    try:
        candidates=[f for f in original_files(src["package_uuid"]) if f["bitstream_uuid"]==src["original_bitstream_uuid"]]
        if len(candidates)!=1 or candidates[0]["checksum"]["value"].lower()!=src["original_md5"].lower() or candidates[0]["bytes"]!=src["original_bytes"]:
            raise ValueError("Original Movebank provider MD5/bitstream/bytes changed")
        result["provider_original_MD5_verified"]=checksum_and_download(candidates[0],path)
        species,counts,unknown=streaming_time_selected_csv(path,src["published_species"])
        admitted_by_species={}
        for taxon in src["published_species"]:
            outcome,_sourcecells=one_taxon(taxon,species[taxon])
            reference=next(x for x in freeze["prior_effects_to_replay"] if x["taxon"]==taxon)
            observed=outcome["day_night_speed_contrast"]
            daylight=outcome["daylength_association"]
            if observed is None or daylight is None:
                raise ValueError("Previously qualified source species lost support")
            if observed["n_individuals"]!=reference["source_animals"] or abs(observed["mean"]-reference["baseline_mean_q"])>1e-12:
                raise ValueError("Original individual/group diel GPS source q failed replay")
            if daylight["n_individuals"]!=reference["source_daylight_animals"] or abs(daylight["mean"]-reference["source_daylight_slope"])>1e-12:
                raise ValueError("Original individual source daylight slope failed replay")
            admitted_by_species[taxon]=source_admitted_daily(species[taxon])
            result["all_taxa"].append({"taxon":taxon,"original_day_night_movement_q":observed["mean"],
                "original_daily_source_daylight_slope":daylight["mean"],
                "original_qualified_animals":observed["n_individuals"],
                "original_qualified_daylight_animals":daylight["n_individuals"]})
        result["original_GPS_effects_replayed"]=True
        scope=defaultdict(set)
        for admitted in admitted_by_species.values():
            for cell,months in exposure_frame(admitted).items():scope[cell].update(months)
        result["predeclared_source_observed_one_degree_climate_grids"]=len(scope)
        if len(scope)>120:
            raise ValueError("Too many source grids for source-locked climate original scope; retain source_hold, do not select outcome-beneficial grid")
        weather={};receipts=[];holds=0
        for cell,months in sorted(scope.items()):
            try:
                climate,receipt=get_monthly_era5(cell,months)
                for (year,month),value in climate.items():
                    weather[(*cell,year,month)]=value
                receipts.append({"source_sha256":receipt["sha256"],
                    "requested_months":receipt["requested_months"],
                    "admitted_months":receipt["admitted_months"]})
            except Exception as ex:
                receipts.append({"status":"SOURCE_HOLD","error_type":type(ex).__name__})
                holds+=1
        result["source_ERA5_grid_receipts"]=receipts
        result["ERA5_source_grid_holds"]=holds
        result["ERA5_admitted_grid_months"]=len(weather)
        for group in result["all_taxa"]:
            group.update(source_animal_slopes(admitted_by_species[group["taxon"]],weather))
            print("WYOMING_ORIGINAL_ENVIRONMENT_DAYLIGHT "+json.dumps(group,sort_keys=True),flush=True)
        result["status"]="completed_independent_source_environment_calendar_ecology"
    except Exception as ex:
        result.update(status="SOURCE_HOLD",error=f"{type(ex).__name__}: {ex}")
    finally:
        path.unlink(missing_ok=True)
    (args.out/"wyoming_individual_climate_daylight.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("WYOMING_ENVIRONMENT_DAYLIGHT_SUMMARY "+json.dumps({
        "status":result["status"],"source_replay":result["original_GPS_effects_replayed"],
        "ERA5_grids":result.get("predeclared_source_observed_one_degree_climate_grids"),
        "ERA5_holds":result.get("ERA5_source_grid_holds"),
        "taxa":len(result["all_taxa"])
    },sort_keys=True))
if __name__=="__main__":
    main()
