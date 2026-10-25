#!/usr/bin/env python3
"""External regional ERA5: does seasonal environmental history differ at matched photoperiod?

FROZEN ecology question in research/SERENGETI_ERA5_EQUAL_PHOTOPERIOD_ENVIRONMENT_V0_CONTRACT.json.
This is a climate-context study at ONE public coarse regional grid, not an animal-response
model, never a camera location, field measurement, detector-q correction or causal test.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import math
import statistics
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE_URL = "https://archive-api.open-meteo.com/v1/archive"
LAT, LON = -2.5, 34.75
START, END = "2010-01-01", "2013-06-30"
TZ = "Africa/Dar_es_Salaam"
SERIES = (
    "temperature_2m_mean", "temperature_2m_max",
    "precipitation_sum", "shortwave_radiation_sum",
)
SOLSTICE_YEARS = (2010, 2011, 2012)
K_RANGE = range(7, 181)
TRAILING_DAYS = 30
REQUIRED_DAY_COUNT = (dt.date.fromisoformat(END) - dt.date.fromisoformat(START)).days + 1
EXPECTED_MIRROR_PAIRS = 3 * len(K_RANGE)
MAX_RESPONSE_BYTES = 1_500_000

def url() -> str:
    query = urllib.parse.urlencode({
        "latitude": str(LAT), "longitude": str(LON),
        "start_date": START, "end_date": END,
        "daily": ",".join(SERIES), "timezone": TZ, "models": "era5",
    })
    return f"{SOURCE_URL}?{query}"

def fetch() -> tuple[dict, str]:
    request=urllib.request.Request(
        url(),
        headers={"User-Agent": "ODSP/0.11 ecological-climate-reanalysis-source-check",
                 "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload=response.read(MAX_RESPONSE_BYTES+1)
    if len(payload)>MAX_RESPONSE_BYTES:
        raise ValueError("HOLD_ERA5_PAYLOAD_ABOVE_LIMIT")
    obj=json.loads(payload)
    return obj, hashlib.sha256(payload).hexdigest()

def calendar_pairs() -> list[tuple[int,str,str]]:
    result=[]
    for year in SOLSTICE_YEARS:
        anchor=dt.date(year, 12, 21)
        for k in K_RANGE:
            result.append((year, (anchor-dt.timedelta(days=k)).isoformat(),
                           (anchor+dt.timedelta(days=k)).isoformat()))
    if len(result)!=EXPECTED_MIRROR_PAIRS:
        raise ValueError("FROZEN_DATEPAIR_COUNT_DRIFT")
    return result

def verify_source(source:dict) -> dict[str,dict[str,float]]:
    if source.get("timezone") != TZ or source.get("utc_offset_seconds") != 10800:
        raise ValueError("HOLD_SOURCE_TIMEZONE_MISMATCH")
    if abs(float(source["latitude"]) - LAT) > .3 or abs(float(source["longitude"]) - LON) > .3:
        raise ValueError("HOLD_ERA5_GRID_COORDINATE_DRIFT")
    daily=source.get("daily", {})
    dates=daily.get("time")
    if not isinstance(dates,list) or len(dates)!=REQUIRED_DAY_COUNT:
        raise ValueError("HOLD_ERA5_DATE_COUNT_MISMATCH")
    expected=[(dt.date.fromisoformat(START)+dt.timedelta(days=i)).isoformat()
              for i in range(REQUIRED_DAY_COUNT)]
    if dates != expected:
        raise ValueError("HOLD_ERA5_NONCONSECUTIVE_OR_DUPLICATE_DATES")
    result={}
    for key in SERIES:
        values=daily.get(key)
        if not isinstance(values,list) or len(values)!=len(dates):
            raise ValueError("HOLD_ERA5_MISSING_VARIABLE_"+key)
    for i, date_str in enumerate(dates):
        fields={}
        for key in SERIES:
            x=daily[key][i]
            if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x):
                raise ValueError("HOLD_ERA5_NULL_NONFINITE_DAILY_VALUE")
            fields[key]=float(x)
        if fields["precipitation_sum"] < 0:
            raise ValueError("HOLD_ERA5_NEGATIVE_PRECIPITATION")
        result[date_str]=fields
    return result

def quantile(data:list[float], q:float)->float:
    xs=sorted(data)
    ix=(len(xs)-1)*q
    i=int(ix)
    return xs[i] + (xs[min(i+1,len(xs)-1)]-xs[i])*(ix-i)

def summarize(values:list[float])->dict:
    if not values: raise ValueError("NO_DELTA_VALUES")
    return {
        "mean":round(statistics.mean(values),4),
        "median":round(statistics.median(values),4),
        "p10":round(quantile(values,.1),4),
        "p90":round(quantile(values,.9),4),
        "positive_fraction":round(sum(v>0 for v in values)/len(values),4),
        "negative_fraction":round(sum(v<0 for v in values)/len(values),4),
    }

def paired_context(grid:dict[str,dict[str,float]])->tuple[dict,list]:
    items=[]
    for year, rising, falling in calendar_pairs():
        def rain30(target:str)->float:
            date=dt.date.fromisoformat(target)
            return sum(grid[(date-dt.timedelta(days=d)).isoformat()]["precipitation_sum"]
                       for d in range(TRAILING_DAYS))
        a=grid[rising];b=grid[falling]
        items.append({
            "year":year,
            "max_temperature_delta_c":b["temperature_2m_max"]-a["temperature_2m_max"],
            "mean_temperature_delta_c":b["temperature_2m_mean"]-a["temperature_2m_mean"],
            "precipitation_antecedent30_delta_mm":rain30(falling)-rain30(rising),
            "radiation_delta_MJm2":b["shortwave_radiation_sum"]-a["shortwave_radiation_sum"],
        })
    fields=[
        "max_temperature_delta_c","mean_temperature_delta_c",
        "precipitation_antecedent30_delta_mm","radiation_delta_MJm2",
    ]
    reports=[]
    for year in (*SOLSTICE_YEARS,"all"):
        rows=[row for row in items if year=="all" or row["year"]==year]
        if len(rows) != (EXPECTED_MIRROR_PAIRS if year=="all" else len(K_RANGE)):
            raise ValueError("SOURCE_MIRROR_COVERAGE_MISMATCH")
        reports.append({
            "year":year, "date_pair_count":len(rows),
            "delta_falling_minus_rising":{
                k:summarize([x[k] for x in rows]) for k in fields
            },
        })
    return {"yearwise_and_all":reports},items

def run(source:dict, raw_digest:str="UNAVAILABLE_IN_MEMORY")->dict:
    grid=verify_source(source)
    report,_=paired_context(grid)
    d=source["daily"]
    only_data={k:d[k] for k in ("time",*SERIES)}
    digest=hashlib.sha256(json.dumps(only_data,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {
        "status":"EXTERNAL_ERA5_REGIONAL_CLIMATE_CONTEXT_ONLY",
        "source_url":url(),
        "original_API_response_sha256":raw_digest,
        "source_daily_arrays_sha256":digest,
        "source_returned_grid":{
            "latitude":source["latitude"],"longitude":source["longitude"],
            "elevation_m":source.get("elevation"),"timezone":source["timezone"],
        },
        "source_available_day_count":len(grid),
        "paired_calendar_design":{
            "solstice_years":list(SOLSTICE_YEARS),
            "pair_days_each_year":len(K_RANGE),
            "environmental_date_pairs_total":EXPECTED_MIRROR_PAIRS,
            "unit":"one regional reanalysis grid, three annual cycles, autocorrelated mirror days"
        },
        "results":report,
        "serengeti_original_animal_record_linked":False,
        "identifies_thermal_avoidance_or_precipitation_causation":False,
        "source_camera_hours_or_individual_behavior_identified":False,
        "note":"Original photo-detection seasons are descriptive. This independent same-daylength regional weather context cannot by itself estimate animal environmental response."
    }

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--input-json",type=Path,default=None)
    args=parser.parse_args()
    try:
        if args.input_json:
            raw=args.input_json.read_bytes()
            data=json.loads(raw)
            digest=hashlib.sha256(raw).hexdigest()
        else:
            data,digest=fetch()
        receipt=run(data,digest)
    except (OSError,KeyError,ValueError,TypeError,IndexError,urllib.error.URLError) as exc:
        receipt={
            "status":"HOLD_SOURCE_NOT_RETRIEVED_OR_MISSING_COVERAGE",
            "exception_type":type(exc).__name__,
            "causal_or_animal_results_claimed":False
        }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":receipt["status"],
        "yearwise":receipt.get("results",{}).get("yearwise_and_all"),
        "source_daily_arrays_sha256":receipt.get("source_daily_arrays_sha256")
    },sort_keys=True))
    if receipt["status"].startswith("HOLD"): raise SystemExit(2)

if __name__=="__main__":
    main()
