"""Source-locked Wyoming original day-level diel GPS displacement × ERA5 environment.

Registered distinct DAILY climate ecological estimand after MONTHLY sources had
insufficient within-animal seasons; monthly failure remains immutable.
Original GPS source effects MUST replay exactly before fetching climate.
Outputs taxon group statistics, never GPS positions, dates or tagged animal IDs.
"""
import argparse,hashlib,json,math
from collections import defaultdict
from datetime import timedelta,date
from pathlib import Path
from statistics import mean

from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download
from scripts.movebank_wyoming_two_ungulates_20261022 import (
    CONTRACT as WYOMING_SOURCE,streaming_time_selected_csv
)
from scripts.movebank_utah_diel_photoperiod_20261019 import one_taxon
from scripts.movebank_utah_shared_spatial_20261019 import cluster_interval
from scripts.movebank_utah_era5_climate_20261019 import (
    API,FIELDS,get_bytes,timezone_name
)
from scripts.movebank_utah_calendar_condition_20261022 import partial_slope
from scripts.movebank_wyoming_individual_era5_20261023 import (
    source_admitted_daily,exposure_frame
)

CONTRACT=HERE/"research/WYOMING_DAILY_ERA5_DAYLIGHT_V1_20261023.json"

def daily_source_era5(cell,days):
    """Fetch full original source period (including 30d lookback), fail closed."""
    lat,lon=cell
    start=min(days)-timedelta(days=29)
    end=max(days)
    from urllib.parse import urlencode
    params={
        "latitude":lat+.5,"longitude":lon+.5,
        "start_date":start.isoformat(),"end_date":end.isoformat(),
        "daily":",".join(FIELDS),"models":"era5",
        "timezone":timezone_name(lon+.5),
        "elevation":"nan","cell_selection":"nearest"
    }
    raw=get_bytes(API+"?"+urlencode(params))
    s=json.loads(raw)
    day=s.get("daily") or {};units=s.get("daily_units") or {}
    for field,unit in [
        ("temperature_2m_mean","°C"),("temperature_2m_max","°C"),
        ("precipitation_sum","mm"),("et0_fao_evapotranspiration","mm")
    ]:
        if units.get(field)!=unit:raise ValueError("ERA5 original source units not validated")
    rows=day.get("time") or []
    if not rows or any(len(day.get(field,[]))!=len(rows) for field in FIELDS):
        raise ValueError("Missing source ERA5 daily data or inconsistent fields")
    out={}
    for i,strdate in enumerate(rows):
        d=date.fromisoformat(strdate)
        if d in out:raise ValueError("Duplicate source climate day")
        values=[day[field][i] for field in FIELDS]
        valid=(all(isinstance(v,(int,float)) and math.isfinite(v) for v in values) and
            values[1]>=values[0] and values[2]>=0 and values[3]>=0)
        out[d]=tuple(values) if valid else None
    if min(out)>start or max(out)<end:raise ValueError("ERA5 response does not cover original GPS observation days and lag")
    return out,{"source_response_sha256":hashlib.sha256(raw).hexdigest(),
                "total_daily_rows":len(rows),
                "valid_weather_days":sum(v is not None for v in out.values())}

def climate_at_gps_day(weather,day):
    """Tmean, Tmax, full 30-day past climatic P minus FAO ET0; NO future dates."""
    today=weather.get(day)
    if today is None:return None
    window=[weather.get(day-timedelta(days=i)) for i in range(30)]
    if any(v is None for v in window):return None
    pminus=sum(v[2]-v[3] for v in window)
    return (today[0],today[1],pminus/100)

def group_effect(values):
    """Repeated source individual years reduced to one value per source animal."""
    from collections import defaultdict
    v=defaultdict(list)
    for animal,year,slope in values:v[animal].append(slope)
    vals=[mean(y) for y in v.values()]
    if len(vals)<5:
        return {"status":"INSUFFICIENT_IDENTIFIABLE_SOURCE_ANIMALS",
                "admitted_animals":len(vals),"admitted_animal_years":len(values),
                "mean":None,"animal_bootstrap_95":None,
                "positive_animals":sum(x>0 for x in vals),"negative_animals":sum(x<0 for x in vals)}
    return {"status":"descriptive_within_original_animal_year",
            "admitted_animals":len(vals),"admitted_animal_years":len(values),
            "mean":mean(vals),"animal_bootstrap_95":cluster_interval(vals),
            "positive_animals":sum(x>0 for x in vals),"negative_animals":sum(x<0 for x in vals)}

def adjusted_daily_effects(admitted,weather):
    """Original date-level GPS responses paired only with original ERA5 admissible days."""
    route={
      "unadjusted_daylight_on_climate_days":(2,[],10,.1),
      "daylight_given_tmax":(2,[0],10,.1),
      "daylight_given_antecedent_water":(2,[1],10,.1),
      "daylight_given_tmax_and_water":(2,[0,1],15,.1),
      "tmax_given_daylight_and_water":(0,[2,1],15,.5),
      "water_given_daylight_and_tmax":(1,[2,0],15,.1)
    }
    sourcevalues={name:[] for name in route}
    missing=matched=0;eligyear=0
    for animal,year,original_days in admitted:
        obs=[]
        for d,L,q,cell,ym in original_days:
            climate=climate_at_gps_day(weather.get(cell,{}) ,d)
            if climate is None:
                missing+=1;continue
            tmean,tmax,water=climate
            # q index 3, first axis 0 Tmax and second 1 30d P−ET0/100.
            obs.append((tmax,water,L,q,tmean))
            matched+=1
        if len(obs)<10 or max(z[2] for z in obs)-min(z[2] for z in obs)<.5:
            continue
        eligyear+=1
        for name,(predictor,controls,minobs,residual_threshold) in route.items():
            y=partial_slope(obs,predictor,controls,
                            minimum_n=minobs,residual_sd=residual_threshold,
                            minimum_daylength_sd=.2)
            if y is not None:sourcevalues[name].append((animal,year,y))
    result={name:group_effect(values) for name,values in sourcevalues.items()}
    result["weather_complete_original_animal_days"]=matched
    result["source_dates_without_30day_complete_ERA5"]=missing
    result["animal_years_with_at_least_ten_climate_complete_source_days_and_solar_span"]=eligyear
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    frozen=json.loads(CONTRACT.read_text())
    if frozen["version"]!="wyoming-daily-original-gps-era5-daylight-v1":
        raise ValueError("Unregistered original daily ecology estimator")
    src=json.loads(WYOMING_SOURCE.read_text())["source"]
    report={"route":"original Wyoming telemetry, independent registered daily environment ecology",
       "study_doi":src["doi"],"source_replay_success":False,
       "daily_weather_evidence":"ERA5 modelled 1degree site-center daily temperature and 30d PminusET0",
       "two_species":[]}
    path=args.out/"source_original_wyoming.csv"
    try:
        fs=[x for x in original_files(src["package_uuid"]) if x["bitstream_uuid"]==src["original_bitstream_uuid"]]
        if len(fs)!=1 or fs[0]["checksum"]["value"].lower()!=src["original_md5"].lower() or fs[0]["bytes"]!=src["original_bytes"]:
            raise ValueError("Provider original GPS source MD5/byte/UUID mismatch")
        report["original_MD5_verified"]=checksum_and_download(fs[0],path)
        taxa,counts,unknown=streaming_time_selected_csv(path,src["published_species"])
        preadmitted={}
        for name in src["published_species"]:
            observed,_=one_taxon(name,taxa[name])
            fix=frozen["original_effect_replay"][name]
            if observed["day_night_speed_contrast"] is None or observed["daylength_association"] is None:
                raise ValueError("Original published source effect no longer supported")
            if observed["day_night_speed_contrast"]["n_individuals"]!=fix["n"] or abs(observed["day_night_speed_contrast"]["mean"]-fix["q"])>1e-12:
                raise ValueError("Original source q/diel effect did NOT replay")
            if observed["daylength_association"]["n_individuals"]!=fix["slope_n"] or abs(observed["daylength_association"]["mean"]-fix["slope"])>1e-12:
                raise ValueError("Original source daylight slope did NOT replay")
            preadmitted[name]=source_admitted_daily(taxa[name])
        report["source_replay_success"]=True
        wanted=defaultdict(set)
        for admitted in preadmitted.values():
            for animal,year,days in admitted:
                for d,L,q,cell,ym in days:
                    wanted[cell].add(d)
        report["source_original_one_degree_weather_cells"]=len(wanted)
        if len(wanted)>120:raise ValueError("Source-observed weather cells >120; cannot selectively prune based on q signs")
        weather={};receipts=[];held=0
        for cell,original_days in sorted(wanted.items()):
            try:
                data,receipt=daily_source_era5(cell,original_days)
                weather[cell]=data
                receipts.append(receipt)
            except Exception as exc:
                held+=1
                receipts.append({"status":"weather_source_hold","error_type":type(exc).__name__})
        report["ERA5_source_receipts"]=receipts
        report["weather_source_hold_cells"]=held
        for taxon in src["published_species"]:
            res={"taxon":taxon,
                 "source_original_qualified_animal_years":len(preadmitted[taxon])}
            res.update(adjusted_daily_effects(preadmitted[taxon],weather))
            report["two_species"].append(res)
            print("WYOMING_DAILY_CLIMATE_DAYLIGHT_TAXON "+json.dumps(res,sort_keys=True),flush=True)
        report["status"]="completed_source_original_daily_environment_daylight_ecology"
    except Exception as exc:
        report.update(status="SOURCE_HOLD",error=f"{type(exc).__name__}: {exc}")
    finally:path.unlink(missing_ok=True)
    (args.out/"wyoming_daily_ERA5_solar_gps_ecology.json").write_text(json.dumps(report,indent=2)+"\n")
    print("WYOMING_DAILY_CLIMATE_DAYLIGHT_SUMMARY "+json.dumps({
        "status":report["status"],"previous_GPS_source_replay":report["source_replay_success"],
        "source_weather_cells":report.get("source_original_one_degree_weather_cells"),
        "weather_holds":report.get("weather_source_hold_cells"),
        "taxa":len(report["two_species"])
    },sort_keys=True))
if __name__=="__main__":main()
