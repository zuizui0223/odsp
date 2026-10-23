"""Exploratory, source-MD5-qualified equal-photoperiod GPS displacement contrasts.

This is NOT continuous animal activity, thermoregulation, environmental causation,
or independent across-species generality. No coordinates or animal IDs are exported.
"""
from collections import defaultdict
import csv
from datetime import datetime, date
import json
import math
from pathlib import Path
import random
from statistics import mean, median
from scripts.movebank_native_ecology_20261019 import (
    PILOT,HERE, original_files,checksum_and_download,parse_time,solar_period,daylength
)

CONTRACT=HERE/"research/MOVEBANK_SOLAR_MOVEMENT_V0_20261019.json"
R_KM=6371.0088

def great_circle_km(a,b,c,d):
    f1,f2=math.radians(a),math.radians(c)
    df,dl=math.radians(c-a),math.radians(d-b)
    h=math.sin(df/2)**2+math.cos(f1)*math.cos(f2)*math.sin(dl/2)**2
    return 2*R_KM*math.asin(math.sqrt(max(0,min(1,h))))

def valid_interval(t1,lat1,lon1,t2,lat2,lon2):
    hours=(t2-t1).total_seconds()/3600
    if not 0.5<=hours<=2.0:return None
    midpoint=t1+(t2-t1)/2
    lat=(lat1+lat2)/2;lon=(lon1+lon2)/2
    a=solar_period(t1,lat1,lon1);b=solar_period(t2,lat2,lon2)
    m=solar_period(midpoint,lat,lon)
    if a!=b or a!=m:return None
    speed=great_circle_km(lat1,lon1,lat2,lon2)/hours
    if not math.isfinite(speed) or speed>60:return None
    return m[0],m[1],speed,hours,lat

def load_events(path):
    events=defaultdict(list);source_n=bad=0
    with path.open("r",encoding="utf-8-sig",newline="") as fd:
        reader=csv.DictReader(fd);cols=reader.fieldnames or []
        def field(*options):return next((x for x in cols if x.lower().strip() in options),None)
        ti=field("timestamp","event-date","eventdate")
        ident=field("individual-local-identifier","individual-id","animal-id")
        la=field("location-lat","location-latitude","latitude")
        lo=field("location-long","location-longitude","longitude")
        if None in (ti,ident,la,lo):raise ValueError("GPS schema lacks required tracking columns")
        for row in reader:
            source_n+=1;ts=parse_time(row.get(ti,""))
            individual=(row.get(ident) or "").strip()
            try:lat=float(row[la]);lon=float(row[lo])
            except (ValueError,TypeError):lat=float("nan");lon=float("nan")
            if ts is None or not individual or not (math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180):
                bad+=1;continue
            events[individual].append((ts,lat,lon))
    return events,source_n,bad

def analyze_file(path):
    source,n_rows,bad=load_events(path)
    daily=defaultdict(lambda:{"day":[],"night":[],"lat":[]})
    n_intervals=n_valid=0
    for individual,obs in source.items():
        obs.sort(key=lambda x:x[0])
        for a,b in zip(obs,obs[1:]):
            n_intervals+=1
            v=valid_interval(a[0],a[1],a[2],b[0],b[1],b[2])
            if v is None:continue
            day,part,speed,hours,lat=v;n_valid+=1
            daily[(individual,day)][part].append(speed)
            daily[(individual,day)]["lat"].append(lat)
    ready=defaultdict(dict)
    for (individual,day),values in daily.items():
        if len(values["day"])<3 or len(values["night"])<3:continue
        ready[(individual,day.year)][day]={
           "day":median(values["day"]),"night":median(values["night"]),
           "n_day":len(values["day"]),"n_night":len(values["night"]),
           "lat":mean(values["lat"])}
    sizes=[]
    individual_years=defaultdict(list)
    for (individual,year),observations in ready.items():
        if not observations or mean(x["lat"] for x in observations.values())<=0:continue
        solstice=date(year,6,21)
        first=[d for d in observations if d<solstice]
        second=[d for d in observations if d>solstice]
        edges=[]
        for d1 in first:
            a=observations[d1]
            for d2 in second:
                if (d2-d1).days<30:continue
                b=observations[d2]
                mismatch=abs(daylength(a["lat"],d1)-daylength(b["lat"],d2))*60
                if mismatch>5:continue
                if any(not 0.5<=a["n_"+part]/b["n_"+part]<=2 for part in ("day","night")):continue
                edges.append((mismatch,d1,d2))
        used1=set();used2=set();pairs=[]
        for mismatch,d1,d2 in sorted(edges):
            if d1 not in used1 and d2 not in used2:
                pairs.append((d1,d2));used1.add(d1);used2.add(d2)
        sizes.append(len(pairs))
        if len(pairs)<10:continue
        diffs=[]
        for d1,d2 in pairs:
            a,b=observations[d1],observations[d2]
            daytime=math.log1p(b["day"])-math.log1p(a["day"])
            nighttime=math.log1p(b["night"])-math.log1p(a["night"])
            diffs.append((nighttime-daytime,daytime,nighttime))
        individual_years[individual].append(tuple(mean(x[j] for x in diffs) for j in range(3)))
    effects=[tuple(mean(x[j] for x in years) for j in range(3)) for years in individual_years.values()]
    out={"gps_rows":n_rows,"invalid_gps_rows":bad,"source_individuals":len(source),
         "adjacent_intervals":n_intervals,"qualified_same_solar_period_steps":n_valid,
         "individual_years_with_day_and_night_steps":len(sizes),
         "individual_years_ge10_matched_days":sum(x>=10 for x in sizes),
         "individuals_ge10_matched_days_some_year":len(effects)}
    if len(effects)<5:
        out.update(effect_status="insufficient_independent_animals",effect=None)
        return out
    rng=random.Random(20261019)
    samples=sorted(mean(effects[rng.randrange(len(effects))][0] for k in range(len(effects))) for _ in range(2000))
    out.update(effect_status="exploratory_population_description",effect={
        "n_individuals":len(effects),
        "n_positive":sum(x[0]>0 for x in effects),
        "n_negative":sum(x[0]<0 for x in effects),
        "n_zero":sum(x[0]==0 for x in effects),
        "mean_falling_minus_rising_log1p_night_over_day_kmh":mean(x[0] for x in effects),
        "mean_falling_minus_rising_day_log1p_kmh":mean(x[1] for x in effects),
        "mean_falling_minus_rising_night_log1p_kmh":mean(x[2] for x in effects),
        "individual_cluster_bootstrap_95_percentile": [samples[49],samples[1949]],
        "warning":"Within one recruitment population, observational GPS straight-line speed; not a taxon-general CI, circadian entrainment, human disturbance, or causal effect."})
    return out

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    contract=json.loads(CONTRACT.read_text())
    sources=json.loads(PILOT.read_text())["sources"]
    assert contract["version"]=="solar-movement-v0" and len(sources)==3
    results=[]
    for p in sources:
        result={"label":p["label"],"doi":p["doi"],"taxon":p["taxon"]}
        file=args.out/(p["label"]+".csv")
        try:
            match=[f for f in original_files(p["package_uuid"]) if f["bitstream_uuid"]==p["original_csv_bitstream_uuid"]]
            if len(match)!=1 or match[0]["checksum"]["value"]!=p["original_csv_md5"]:
                raise ValueError("Source bitstream identity/checksum changed")
            result["file"]=checksum_and_download(match[0],file)
            result.update(analyze_file(file))
        except Exception as exc:
            result.update(effect_status="source_hold",error=f"{type(exc).__name__}: {exc}")
        finally:file.unlink(missing_ok=True)
        results.append(result)
        print("SOURCE_SEASONAL_MOVEMENT "+json.dumps(result,sort_keys=True),flush=True)
    receipt={"estimand":"Exploratory within-individual matched-solar-date changes in reported minimum GPS straight-line displacement rate","sources":results}
    (args.out/"grouped_results.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("SEASONAL_MOVEMENT_FINISHED "+json.dumps({
        "sources":len(results),"sources_with_supported_effect":sum(x.get("effect_status")=="exploratory_population_description" for x in results)},sort_keys=True),flush=True)

if __name__=="__main__":main()
