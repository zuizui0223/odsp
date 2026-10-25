"""Source-locked, post-outcome exploratory matching of GPS diel movement and ERA5 seasonal context.

Replays the ORIGINAL v0 movement outcome before reading any climate values.
Regional reference locations are predeclared and coarse; no individual GPS locations,
IDs, times or event-level behavior are exported. No causal ecological claims.
"""
import csv, hashlib, json, math, statistics, time
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from scripts.movebank_native_ecology_20261019 import (
    PILOT, HERE, original_files, checksum_and_download, daylength
)
from scripts.movebank_solar_movement_20261019 import (
    load_events,valid_interval,analyze_file
)

CONTRACT=HERE/"research/MOVEBANK_REGIONAL_ERA5_MOVEMENT_LINK_V0_20261019.json"
API="https://archive-api.open-meteo.com/v1/archive"
FIELDS=("temperature_2m_mean","precipitation_sum","et0_fao_evapotranspiration")

def fixed_timezone(longitude):
    offset=math.floor(longitude/15+0.5)
    return "Etc/GMT"+(f"{-offset:+d}" if offset else "")

def source_read(url,attempts=3):
    for i in range(attempts):
        try:
            with urlopen(Request(url,headers={"User-Agent":"ODSP source-backed comparative ecology/1.0","Accept":"application/json"}),timeout=110) as f:
                raw=f.read(5000000)
            if len(raw)>=5000000:raise ValueError("Oversized weather response")
            return raw
        except (HTTPError,URLError,TimeoutError) as e:
            if i>=attempts-1 or isinstance(e,HTTPError) and e.code in (400,401,403,404):
                raise
            time.sleep(2**i)

def read_weather(ref,first_day,last_day):
    start=first_day-timedelta(days=29)
    end=last_day
    output={}
    receipts=[]
    for yr in range(start.year,end.year+1,4):
        lo=max(start,date(yr,1,1));hi=min(end,date(yr+3,12,31))
        if lo>hi:continue
        params={"latitude":ref["latitude"],"longitude":ref["longitude"],
                "start_date":lo.isoformat(),"end_date":hi.isoformat(),
                "daily":",".join(FIELDS),"models":"era5","timezone":fixed_timezone(ref["longitude"]),
                "elevation":"nan","cell_selection":"nearest"}
        url=API+"?"+urlencode(params)
        raw=source_read(url)
        obj=json.loads(raw)
        daily=obj.get("daily") or {}
        dates=daily.get("time") or []
        unit=obj.get("daily_units") or {}
        if unit.get("temperature_2m_mean")!="°C" or unit.get("precipitation_sum")!="mm" or unit.get("et0_fao_evapotranspiration")!="mm":
            raise ValueError(f"Unexpected ERA5 daily units {unit}")
        if not dates or any(len(daily.get(f,[]))!=len(dates) for f in FIELDS):
            raise ValueError("Incomplete ERA5 daily response")
        for i,d in enumerate(dates):
            day=date.fromisoformat(d)
            if day in output:raise ValueError("Duplicate weather date")
            values=tuple(daily[f][i] for f in FIELDS)
            if any(v is None or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values) or values[1]<0 or values[2]<0:
                output[day]=None
            else:output[day]=values
        receipts.append({"source_url":url,"sha256":hashlib.sha256(raw).hexdigest(),"returned_days":len(dates),"provider_grid_latitude":round(obj["latitude"],2),"provider_grid_longitude":round(obj["longitude"],2)})
    return output,receipts

def weather_rolling_30(days,day):
    a=days.get(day)
    if a is None:return None
    prior=[days.get(day-timedelta(days=k)) for k in range(30)]
    if any(x is None for x in prior):return None
    return (a[0],sum(x[1]-x[2] for x in prior))

def locked_pairs(source_path):
    """Reproduce frozen GPS day/hour filters and effect; preserve no identifiers externally."""
    tracked,n_rows,bad=load_events(source_path)
    daily=defaultdict(lambda:{"day":[],"night":[],"lat":[]})
    for ind,obs in tracked.items():
        obs.sort(key=lambda x:x[0])
        for a,b in zip(obs,obs[1:]):
            step=valid_interval(a[0],a[1],a[2],b[0],b[1],b[2])
            if step is None:continue
            d,part,speed,hours,lat=step
            daily[(ind,d)][part].append(speed)
            daily[(ind,d)]["lat"].append(lat)
    tracked.clear()
    good=defaultdict(dict)
    for (individual,d),vals in daily.items():
        if len(vals["day"])<3 or len(vals["night"])<3:continue
        good[(individual,d.year)][d]={"day":statistics.median(vals["day"]),
           "night":statistics.median(vals["night"]),
           "n_day":len(vals["day"]),"n_night":len(vals["night"]),
           "lat":statistics.mean(vals["lat"])}
    del daily
    by_animal=defaultdict(list)
    for (animal,year),obs in good.items():
        if not obs or statistics.mean(x["lat"] for x in obs.values())<=0:continue
        pivot=date(year,6,21)
        a_days=[d for d in obs if d<pivot]
        b_days=[d for d in obs if d>pivot]
        edges=[]
        for da in a_days:
            a=obs[da]
            for db in b_days:
                b=obs[db]
                if (db-da).days<30:continue
                gap=abs(daylength(a["lat"],da)-daylength(b["lat"],db))*60
                if gap>5:continue
                if any(not 0.5<=a["n_"+k]/b["n_"+k]<=2 for k in ("day","night")):continue
                edges.append((gap,da,db))
        da_used=set();db_used=set();pairs=[]
        for gap,da,db in sorted(edges):
            if da not in da_used and db not in db_used:
                a,b=obs[da],obs[db]
                dd=math.log1p(b["day"])-math.log1p(a["day"])
                dn=math.log1p(b["night"])-math.log1p(a["night"])
                pairs.append((da,db,dn-dd))
                da_used.add(da);db_used.add(db)
        if len(pairs)>=10:by_animal[animal].append(pairs)
    if not by_animal:return [],None,{"gps_rows":n_rows,"source_individuals":0,"included_individual_years":0}
    # Fully reproduce frozen within-animal equal-year/equal-individual v0 effect.
    main=statistics.mean(statistics.mean(statistics.mean(p[2] for p in year) for year in years) for years in by_animal.values())
    summary={"gps_rows":n_rows,"source_individuals":len(by_animal),
             "included_individual_years":sum(len(years) for years in by_animal.values()),
             "included_calendar_pairs":sum(len(year) for years in by_animal.values() for year in years)}
    return list(by_animal.values()),main,summary

def link_weather(animal_years,weather):
    by_animal=[]
    missing_pairs=0
    for years in animal_years:
        yearly=[]
        for pairs in years:
            valid=[]
            for a,b,effect in pairs:
                ea=weather_rolling_30(weather,a)
                eb=weather_rolling_30(weather,b)
                if ea is None or eb is None:
                    missing_pairs+=1
                    continue
                valid.append((eb[0]-ea[0],eb[1]-ea[1],effect))
            if valid:
                # Equal pair weight within each animal-year, retaining missingness.
                yearly.append(tuple(statistics.mean(x[i] for x in valid) for i in (0,1,2)))
        if yearly:by_animal.append(tuple(statistics.mean(x[i] for x in yearly) for i in (0,1,2)))
    if not by_animal:return {"status":"weather_join_unavailable","missing_weather_pairs":missing_pairs}
    temp=[x[0] for x in by_animal];water=[x[1] for x in by_animal];behavior=[x[2] for x in by_animal]
    return {"status":"descriptive_coarse_region_weather_link",
        "individuals_with_complete_weather_and_displacement":len(by_animal),
        "mean_falling_minus_rising_regional_temperature_c":statistics.mean(temp),
        "mean_falling_minus_rising_regional_p_minus_et0_30d_mm":statistics.mean(water),
        "individuals_with_warmer_falling_weather":sum(v>0 for v in temp),
        "individuals_with_drier_falling_proxy":sum(v<0 for v in water),
        "mean_observed_falling_minus_rising_relative_log1p_night_day_speed":statistics.mean(behavior),
        "missing_weather_date_pairs":missing_pairs,
        "limitation":"One coarse grid per source, individual-year temperature not locally experienced microclimate; source cohort and geography entirely confounded; no causal associations estimated."}

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert c["version"]=="movement-region-climate-link-v0"
    sources=json.loads(PILOT.read_text())["sources"]
    rows=[]
    for src in sources:
        tag=src["label"]
        rec={"source":tag,"taxon":src["taxon"],"doi":src["doi"],"status":"source_hold"}
        dest=args.out/(tag+".csv")
        try:
            files=original_files(src["package_uuid"])
            fs=[x for x in files if x["bitstream_uuid"]==src["original_csv_bitstream_uuid"]]
            if len(fs)!=1 or fs[0]["checksum"]["value"]!=src["original_csv_md5"]:
                raise ValueError("Original source digest changed")
            checksum_and_download(fs[0],dest)
            pairs,actual,counts=locked_pairs(dest)
            expected=c["expected_source_means"][tag]
            if actual is None or abs(actual-expected)>1e-10:
                raise ValueError(f"Previously frozen original movement result mismatch: {actual}")
            dates=[d for year in pairs for batch in year for a,b,_ in batch for d in (a,b)]
            values,receipts=read_weather(c["coarse_weather_reference_sites"][tag],min(dates),max(dates))
            rec.update(counts)
            rec["frozen_movement_result_reproduced"]=True
            rec["coarse_region"]=c["coarse_weather_reference_sites"][tag]["name"]
            rec["source_receipts"]=receipts
            rec.update(link_weather(pairs,values))
        except Exception as e:
            rec.update({"status":"source_hold","error":f"{type(e).__name__}: {e}"})
        finally:
            dest.unlink(missing_ok=True)
        rows.append(rec)
        print("GPS_ERA5_SAME_DATE",json.dumps(rec,sort_keys=True),flush=True)
    report={"scope":"Post-outcome exploratory regional climate context, not environmental causation",
      "climate":"ERA5 regional fixed coarse reference grids, observed matched GPS dates, native source checksums verified",
      "sources":rows}
    (args.out/"gps_regional_climate_joint_summary.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
if __name__=="__main__":main()
