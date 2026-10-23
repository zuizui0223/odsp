#!/usr/bin/env python3
"""Outcome-blind daily CERRA weather/source repetition for French Gyps 2019-21.

This is NEW meteorological context after an older, different source-height
identity result was already opened. No NEW height value or height missingness
is used. Any subsequent climate-height result must be called exploratory.
"""
from __future__ import annotations
import argparse,csv,io,zipfile,json,math,statistics,hashlib,urllib.request,urllib.parse
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from .france_griffon_2019_xytime_preflight import select_rows,PATTERN,PROJECTOR

SITE_LAT,SITE_LON=44.2,3.25  # published Cassagne colony station
YEAR_RANGE=(2019,2020,2021)
DAYLIGHT_HOURS=tuple(range(9,16))
CALIBRATION_LABEL="Test géodésie ornitela"
EXPECTED_RAW_FIRST_BINS=742423
EXPECTED_BIO_FIRST_BINS=742078
EXPECTED_5KM_BIRDS=28
EXPECTED_5KM_HASH="031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928"
MIN_FIX=20
MIN_DONOR=10


def finite(value):
    try:z=float(value)
    except (TypeError,ValueError):return None
    return z if math.isfinite(z) else None


def fetch_CERRA(year):
    args={"latitude":f"{SITE_LAT:.6f}","longitude":f"{SITE_LON:.6f}",
          "start_date":f"{year}-01-01","end_date":f"{year}-12-31",
          "hourly":"shortwave_radiation,wind_speed_100m,temperature_2m",
          "timezone":"UTC","wind_speed_unit":"ms","models":"cerra"}
    request=urllib.request.Request(
        "https://archive-api.open-meteo.com/v1/archive?"+urllib.parse.urlencode(args),
        headers={"User-Agent":"ODSP-outcome-blind-CERRA-source-audit/1.0",
                 "Accept":"application/json"})
    with urllib.request.urlopen(request,timeout=120) as f: obj=json.load(f)
    if obj.get("error") or obj.get("utc_offset_seconds")!=0:
        raise ValueError("CERRA unavailable or non-UTC: "+str(obj.get("reason")))
    units=obj.get("hourly_units",{})
    if units.get("shortwave_radiation")!="W/m²" or units.get("wind_speed_100m")!="m/s":
        raise ValueError("CERRA independent weather units changed")
    hourly=obj["hourly"]
    fields={"solar":"shortwave_radiation","wind":"wind_speed_100m",
            "temperature":"temperature_2m"}
    per_day=defaultdict(lambda:defaultdict(list))
    for ix,stamp in enumerate(hourly["time"]):
        if not stamp.startswith(str(year)+"-"):
            raise ValueError("CERRA returned date outside original year")
        if int(stamp[11:13]) not in DAYLIGHT_HOURS:continue
        for name,field in fields.items():
            z=finite(hourly[field][ix])
            if z is not None:per_day[stamp[:10]][name].append(z)
    daily={}
    for day,values in per_day.items():
        if all(len(values[name])>=6 for name in fields):
            daily[day]={name:float(statistics.mean(values[name])) for name in fields}
    return {"grid":[float(obj["latitude"]),float(obj["longitude"])],
            "units":{name:units[field] for name,field in fields.items()},
            "query":args,"daily":daily}


def regime_labels(weather_by_year):
    all_days={day:values for entry in weather_by_year.values()
              for day,values in entry["daily"].items()}
    by_month=defaultdict(lambda:defaultdict(list))
    for day,values in all_days.items():
        for metric in ("solar","wind"):by_month[day[:7]][metric].append(values[metric])
    thresholds={}
    for month,d in sorted(by_month.items()):
        if not 20<=len(d["solar"])<=31:
            raise ValueError("CERRA monthly coverage insufficient: "+month)
        thresholds[month]={}
        for metric,z in d.items():
            a,b=np.quantile(z,[.25,.75])
            thresholds[month][metric]={
                "q25":float(a),"q75":float(b),"n_calendar_days":len(z)}
    labels={}
    for metric in ("solar","wind"):
        labels[metric]={}
        for day,values in all_days.items():
            q=thresholds[day[:7]][metric]
            labels[metric][day]=(
                "low" if values[metric]<=q["q25"] else
                "high" if values[metric]>=q["q75"] else "middle")
    return all_days,thresholds,labels


def original_source_fixes(archive):
    first={};aud=Counter();tags=defaultdict(set);studies=defaultdict(set)
    with zipfile.ZipFile(archive) as zf:
        members=[v for v in zf.infolist() if PATTERN.search(v.filename)
                 and v.filename.endswith(".csv") and not v.filename.startswith("__MACOSX/")]
        if len(members)!=9:raise ValueError("Nine original source seasons required")
        for member in sorted(members,key=lambda x:x.filename):
            year=int(PATTERN.search(member.filename).group(2))
            with zf.open(member) as raw:
                with io.TextIOWrapper(raw,encoding="utf-8-sig",errors="replace",newline="") as f:
                    select_rows(csv.reader(f),first,aud,tags,studies,year)
            print("No-height native source",member.filename,len(first),flush=True)
    if len(first)!=EXPECTED_RAW_FIRST_BINS or len({k[0] for k in first})!=30:
        raise ValueError("Original altitude-blind source GPS 5min selection changed")
    if CALIBRATION_LABEL not in {k[0] for k in first}:
        raise ValueError("Original geodesy test device label changed")
    first={k:v for k,v in first.items() if k[0]!=CALIBRATION_LABEL}
    if len(first)!=EXPECTED_BIO_FIRST_BINS or len({k[0] for k in first})!=29:
        raise ValueError("Original 29 biological birds source changed")
    return first


def source_support(first,target_ids,date_regimes):
    counts=Counter()
    for (bird,day,tbin),(_,lon,lat,hdop,sat,tag) in first.items():
        x,y=PROJECTOR.transform(lon,lat)
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("Invalid WGS84 to equal area projection")
        counts[bird,day,(math.floor(x/5000),math.floor(y/5000))]+=1
    own=Counter();total=Counter();datecell=Counter();stateown=Counter()
    for (bird,day,cell),n in counts.items():
        own[bird,cell]+=n
        total[cell]+=n
        datecell[day,cell]+=n
        state=date_regimes.get(day)
        if state in ("low","high"):stateown[bird,cell,state]+=n
    scorable=Counter()
    for (bird,day,cell),n in counts.items():
        if bird not in target_ids:continue
        state=date_regimes.get(day)
        if state not in ("low","high"):continue
        opp="high" if state=="low" else "low"
        self_other=stateown[bird,cell,state]-n
        self_opp=stateown[bird,cell,opp]
        other_other=total[cell]-own[bird,cell]-datecell[day,cell]+n
        if self_other>=MIN_DONOR and self_opp>=MIN_DONOR and other_other>=MIN_DONOR:
            scorable[bird,day,state]+=n
    bird_state_days=Counter()
    for (bird,day,state),n in scorable.items():
        if n>=MIN_FIX:bird_state_days[bird,state]+=1
    good={bird for bird in target_ids
          if bird_state_days[bird,"low"]>=2 and bird_state_days[bird,"high"]>=2}
    return {
        "n_eligible_birds":len(good),
        "eligible_bird_days":sum(bird_state_days[b,s] for b in good for s in ("low","high")),
        "eligible_scored_5min_fixes":sum(n for (b,day,s),n in scorable.items()
                                       if b in good and n>=MIN_FIX),
        "admitted_min10_birds":len(good)>=10,
        "bird_ids":sorted(good),
        "bird_ids_sha256":hashlib.sha256("\n".join(sorted(good)).encode()).hexdigest(),
        "n_original_scored_5km_cells":len(total),
        "native_altitude_read":False
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--preheight",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    receipt=json.loads(args.preheight.read_text())
    if receipt["numeric_native_GPS_height_values_read"] is not False:
        raise ValueError("Source roster no longer altitude-blind")
    if receipt.get("quarantined_nonbiological_animal_IDs")!=[CALIBRATION_LABEL]:
        raise ValueError("Explicit nonanimal source-quality filter missing")
    gate=receipt["horizontal_day_eligibility_by_cell_m"]["5000"]
    original=set(gate["admitted_bird_ids"])
    if len(original)!=EXPECTED_5KM_BIRDS or gate["source_bird_ID_sha256"]!=EXPECTED_5KM_HASH:
        raise ValueError("Frozen 28-bird source population changed")
    climate={str(y):fetch_CERRA(y) for y in YEAR_RANGE}
    days,thresholds,labels=regime_labels(climate)
    first=original_source_fixes(args.source)
    if not original<=set(b for b,d,k in first):
        raise ValueError("Original biological target IDs absent from source")
    support={field:source_support(first,original,labels[field])
             for field in ("solar","wind")}
    result={
      "analysis":"FRANCE_GYPS_2019_2021_CERRA_DAY_CONTEXT_XY_NO_HEIGHT_V1",
      "source_DOI":"10.48579/PRO/IOSZNM",
      "source_original_GPS_zip_md5":"b18cc8004d311d19ff24060f655178bf",
      "prior_5km_biological_roster_hash":EXPECTED_5KM_HASH,
      "original_biological_5min_events":len(first),
      "location_WGS84":[SITE_LAT,SITE_LON],
      "climate_source":"Open-Meteo 5km CERRA colony Cassagne annual hourly archive",
      "daytime_UTC_hours":list(DAYLIGHT_HOURS),
      "model_grid_by_year":{y:x["grid"] for y,x in climate.items()},
      "weather_query_by_year":{y:x["query"] for y,x in climate.items()},
      "daily_climate":dict(sorted(days.items())),
      "thresholds_year_month":thresholds,
      "all_climate_labels":labels,
      "source_support":support,
      "solar_primary_source_admitted":support["solar"]["admitted_min10_birds"],
      "wind_secondary_source_admitted":support["wind"]["admitted_min10_birds"],
      "numeric_GPS_height_read":False,
      "numeric_baro_height_read":False,
      "height_missingness_consulted":False,
      "original_French_dualsensor_height_results_previously_opened":True,
      "future_thermal_height_test_scope":"POST_OUTCOME EXPLORATORY ONLY",
      "shared_environment_null_future":"Permute WHOLE CERRA calendar-date labels synchronously across ALL birds within same YYYY-MM; not independently within bird.",
      "claims_not_supported":"Site radiation is a thermal-availability proxy, not actual GPS-experienced uplift or causal bird-specific thermodynamic flight rule."
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "weather_dates":len(days),
      "solar_birds":support["solar"]["n_eligible_birds"],
      "solar_days":support["solar"]["eligible_bird_days"],
      "solar_fixes":support["solar"]["eligible_scored_5min_fixes"],
      "wind_birds":support["wind"]["n_eligible_birds"],
      "wind_days":support["wind"]["eligible_bird_days"],
      "wind_fixes":support["wind"]["eligible_scored_5min_fixes"],
      "altitude_used":False
    },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
