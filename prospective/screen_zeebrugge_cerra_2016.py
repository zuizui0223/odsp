#!/usr/bin/env python3
"""Altitude-blind 2016 Zeebrugge GPS/CERRA wind x-y-time support gate.

Do NOT access height-above-msl, barometric pressure, or derived animal altitude.
Bird-site mapping comes from archived reference metadata only. CERRA winds are
regional conditions near each tagged bird's colony, not exact flight-site wind.
"""
from __future__ import annotations

import argparse,csv,gzip,hashlib,json,math,statistics,urllib.parse,urllib.request,time
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
import numpy as np
from pyproj import Transformer

SRC_MD5="8789e188f1b33af9d4d8c810cded005a"
REF_MD5="76c5b0c8a3a17f7bdd7f589b3d87014c"
SRC_NAME="LBBG_ZEEBRUGGE-gps-2016.csv.gz"
REF_NAME="LBBG_ZEEBRUGGE-reference-data.csv"
STUDY_YEAR=2016
CELL_M=5000
MIN_FLY_DAY=20
MIN_OWN_OTHER=10
MIN_OTHER_OTHER=10
MIN_SCORABLE_FLY_DAY=50
MIN_STATE_FLY_DAY=20
MIN_BIRD_DAYS_PER_WIND_STATE=2
MIN_BIRDS=10
WEATHER_ENDPOINT="https://archive-api.open-meteo.com/v1/archive"


def ensure_md5(path:Path,expected:str,filename:str)->str:
    h=hashlib.md5()
    with path.open("rb") as stream:
        for b in iter(lambda:stream.read(1<<20),b""):
            h.update(b)
    if path.name!=filename or h.hexdigest()!=expected:
        raise ValueError(f"Frozen archived source checksum/name invalid for {filename}")
    return h.hexdigest()


def num(value):
    try:
        x=float(value)
        return x if math.isfinite(x) else None
    except (TypeError,ValueError):
        return None


def reference_meta(records:list[dict])->dict:
    sources=defaultdict(list)
    all_sites=defaultdict(list)
    for r in records:
        site=(r.get("study-site") or "").strip()
        lat=num(r.get("deploy-on-latitude"))
        lon=num(r.get("deploy-on-longitude"))
        if site and lat is not None and lon is not None and -90<=lat<=90 and -180<=lon<=180:
            all_sites[site].append((lat,lon))
            if (r.get("deploy-on-date") or "").startswith("2016"):
                sources[site].append((lat,lon))
    centers={}
    for site,ls in sources.items():
        if len(ls)<3:continue
        centers[site]={"latitude":float(statistics.median(x for x,y in ls)),
                       "longitude":float(statistics.median(y for x,y in ls)),
                       "new_deployments_2016":len(ls)}
    return {"site_centers":dict(sorted(centers.items())),
            "all_reference_rows":len(records),
            "unique_reference_animals":len({r.get("animal-id") for r in records}),
            "reference_sites":dict(sorted((s,len(r)) for s,r in all_sites.items()))}


def safe_crosswalk(ref:list[dict],observed:dict[str,set[tuple[str,str]]])->dict:
    """Resolve only source-provided exact identifiers, never fuzzy bird aliases."""
    identities=[
        ("animal_local","animal-id",0),
        ("animal_local","animal-ring-id",0),
        ("tag_local","tag-id",1),
        ("tag_local","tag-serial-no",1),
    ]
    output={}
    all_birds=set(observed)
    for name,ref_field,which in identities:
        rev=defaultdict(set)
        for r in ref:
            key=(r.get(ref_field) or "").strip()
            site=(r.get("study-site") or "").strip()
            if key and site:rev[key].add(site)
        mapped={}
        ambiguous=0
        for bird,pairs in observed.items():
            labels={p[which] for p in pairs if p[which]}
            sites=set()
            for label in labels:sites.update(rev.get(label,set()))
            if len(sites)==1:mapped[bird]=next(iter(sites))
            elif len(sites)>1:ambiguous+=1
        output[name+"__"+ref_field]={
            "mapped":len(mapped),"fraction":len(mapped)/len(all_birds) if all_birds else 0,
            "ambiguous":ambiguous,"site_map":mapped
        }
    # deterministic algorithm fixed before GPS altitude, no manual alias edits.
    eligible=sorted(output,key=lambda k:(-output[k]["mapped"],output[k]["ambiguous"],k))
    best=eligible[0] if eligible else None
    accepted=(best is not None and output[best]["fraction"]>=.95 and output[best]["ambiguous"]==0)
    return {
        "accepted":accepted,"best_mapping":best if accepted else None,
        "methods":{k:{"mapped":v["mapped"],"fraction":v["fraction"],"ambiguous":v["ambiguous"]}
                   for k,v in sorted(output.items())},
        "site_by_bird":output[best]["site_map"] if accepted else {},
        "observed_distinct_birds":len(all_birds),
    }


def screen_fixes(source_rows)->tuple[dict,dict,dict]:
    first={}
    bird_labels=defaultdict(set)
    counters=Counter()
    seen_taxa=Counter()
    for row in source_rows:
        counters["raw_source_rows"]+=1
        taxon=(row.get("individual-taxon-canonical-name") or "").strip()
        seen_taxa[taxon]+=1
        if taxon not in {"Larus fuscus","Larus fuscus intermedius"}:
            counters["non_target_taxon"]+=1
            continue
        if any((row.get(k) or "").strip().lower() in {"true","t","1","yes","y"}
               for k in ("import-marked-outlier","manually-marked-outlier")):
            counters["provider_outliers"]+=1
            continue
        stamp=(row.get("timestamp") or "").strip()
        bird=(row.get("individual-local-identifier") or "").strip()
        tag=(row.get("tag-local-identifier") or "").strip()
        try:
            year,month,hour,minute=int(stamp[:4]),int(stamp[5:7]),int(stamp[11:13]),int(stamp[14:16])
        except (TypeError,ValueError):
            counters["invalid_time"]+=1;continue
        if year!=STUDY_YEAR or month not in (5,6,7) or not bird or not(0<=hour<24 and 0<=minute<60):
            counters["outside_frozen_window"]+=1;continue
        bird_labels[bird].add((bird,tag))
        lat=num(row.get("location-lat"));lon=num(row.get("location-long"))
        speed=num(row.get("ground-speed"))
        if lat is None or lon is None or speed is None or not(-90<=lat<=90 and -180<=lon<=180):
            counters["invalid_xy_or_speed"]+=1;continue
        if not 5<=speed<=55:
            counters["outside_flight_proxy"]+=1;continue
        counters["flight_proxy_events"]+=1
        key=(bird,stamp[:10],hour*12+minute//5)
        if key not in first or stamp<first[key][0]:
            first[key]=(stamp,lon,lat)
    counters["unique_flight_5min_bins"]=len(first)
    return first,bird_labels,{"counts":dict(counters),"native_taxa":dict(seen_taxa)}


def xysupport(first:dict,site_by_bird:dict,regimes:dict)->dict:
    project=Transformer.from_crs("EPSG:4326","EPSG:32631",always_xy=True)
    by_day_cell=Counter()
    for (bird,day,bin5),(t,lon,lat) in first.items():
        x,y=project.transform(lon,lat)
        if not(math.isfinite(x) and math.isfinite(y)):continue
        cell=(math.floor(x/CELL_M),math.floor(y/CELL_M))
        by_day_cell[bird,day,cell]+=1
    own=Counter();cell_total=Counter();day_cell=Counter()
    bird_day_total=Counter()
    for (bird,day,cell),n in by_day_cell.items():
        own[bird,cell]+=n
        cell_total[cell]+=n
        day_cell[day,cell]+=n
        bird_day_total[bird,day]+=n
    valid_eval=Counter()
    for (bird,day,cell),n in by_day_cell.items():
        own_other=own[bird,cell]-n
        other_other_date=cell_total[cell]-own[bird,cell]-day_cell[day,cell]+n
        if own_other>=MIN_OWN_OTHER and other_other_date>=MIN_OTHER_OTHER:
            valid_eval[bird,day]+=n
    days_by_bird=Counter()
    for (bird,day),n in valid_eval.items():
        if n>=MIN_SCORABLE_FLY_DAY:days_by_bird[bird]+=1
    baseline_birds={bird for bird,n in days_by_bird.items() if n>=2}

    # Weather support within identical visited cells, from bird's site-month label.
    by_bird_cell_regime=Counter()
    chosen_state={}
    missing_site=set()
    for (bird,day,cell),n in by_day_cell.items():
        site=site_by_bird.get(bird)
        if site is None:
            missing_site.add(bird);continue
        regime=regimes.get(site,{}).get(day)
        if regime not in ("low","high"):continue
        chosen_state[bird,day]=regime
        by_bird_cell_regime[bird,cell,regime]+=n
    state_day_score=Counter()
    for (bird,day,cell),n in by_day_cell.items():
        state=chosen_state.get((bird,day))
        if state not in ("low","high"):continue
        if by_bird_cell_regime[bird,cell,state]-n>=MIN_OWN_OTHER:
            state_day_score[bird,day,state]+=n
    eligible_days_by_bird_state=Counter()
    for (bird,day,state),n in state_day_score.items():
        if n>=MIN_STATE_FLY_DAY:
            eligible_days_by_bird_state[bird,state]+=1
    eligible_birds={bird for bird in site_by_bird if
         eligible_days_by_bird_state[bird,"low"]>=MIN_BIRD_DAYS_PER_WIND_STATE
         and eligible_days_by_bird_state[bird,"high"]>=MIN_BIRD_DAYS_PER_WIND_STATE}
    by_site=defaultdict(Counter)
    for bird in baseline_birds:by_site[site_by_bird.get(bird,"unmapped")]["baseline_birds"]+=1
    for bird in eligible_birds:by_site[site_by_bird.get(bird,"unmapped")]["wind_birds"]+=1
    return {
        "source_birds_with_any_flight_bin":len({b for b,d,i in first}),
        "distinct_bird_days_with_flight_bins":len(bird_day_total),
        "birds_ge2_flight_days_50bins":sum(
            sum(v>=MIN_SCORABLE_FLY_DAY for (a,d),v in bird_day_total.items() if a==bird)>=2
            for bird in {b for b,d,i in first}
        ),
        "baseline_shared_cell_birds":len(baseline_birds),
        "wind_both_regimes_birds":len(eligible_birds),
        "wind_gate_admitted":len(eligible_birds)>=MIN_BIRDS,
        "missing_reference_site_birds":len(missing_site),
        "site_counts":{s:dict(v) for s,v in sorted(by_site.items())},
        "matched_wind_eligible_birds_sha256":hashlib.sha256("\n".join(sorted(eligible_birds)).encode()).hexdigest(),
        "wind_eligible_observation_days":sum(
            n for (bird,state),n in eligible_days_by_bird_state.items() if bird in eligible_birds
        ),
        "height_values_accessed":False,
    }


def fetch_weather(sites:dict)->tuple[dict,dict]:
    sources={};regimes={}
    for site,meta in sorted(sites.items()):
        params={
            "latitude":f"{meta['latitude']:.6f}","longitude":f"{meta['longitude']:.6f}",
            "start_date":"2016-05-01","end_date":"2016-07-31",
            "hourly":"wind_speed_100m,wind_speed_10m","wind_speed_unit":"ms",
            "timezone":"UTC","models":"cerra"
        }
        url=WEATHER_ENDPOINT+"?"+urllib.parse.urlencode(params)
        response=None
        for attempt in range(3):
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"Open-ecology-archive-screen/1.0"})
                with urllib.request.urlopen(req,timeout=90) as fp:response=json.loads(fp.read())
                break
            except Exception:
                if attempt==2:raise
                time.sleep(4*(attempt+1))
        hourly=response["hourly"]
        assert response.get("utc_offset_seconds")==0
        assert response["hourly_units"]["wind_speed_100m"]=="m/s"
        wind=hourly["wind_speed_100m"]
        day=defaultdict(list)
        for ts,v in zip(hourly["time"],wind):
            vv=num(v)
            if vv is not None:day[ts[:10]].append(vv)
        daily={d:float(statistics.mean(v)) for d,v in day.items() if len(v)>=20}
        by_month=defaultdict(list)
        for d,v in daily.items():by_month[d[:7]].append(v)
        thresholds={}
        for month,values in sorted(by_month.items()):
            q25,q75=np.quantile(values,[.25,.75])
            thresholds[month]={"q25":float(q25),"q75":float(q75),"n_calendar_days":len(values)}
        label={}
        for d,v in daily.items():
            q=thresholds[d[:7]]
            label[d]="low" if v<=q["q25"] else ("high" if v>=q["q75"] else "middle")
        regimes[site]=label
        sources[site]={
            "query_parameters":params,
            "response_grid_latitude":response["latitude"],
            "response_grid_longitude":response["longitude"],
            "hourly_points":len(wind),"finite_hourly_wind_100m":sum(num(w) is not None for w in wind),
            "days_valid_20plus_hours":len(daily),
            "thresholds_by_month":thresholds,
            "low_days":sum(v=="low" for v in label.values()),
            "high_days":sum(v=="high" for v in label.values()),
        }
    return sources,regimes


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference",type=Path,required=True)
    p.add_argument("--gps",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    refmd=ensure_md5(args.reference,REF_MD5,REF_NAME)
    gpsmd=ensure_md5(args.gps,SRC_MD5,SRC_NAME)
    with args.reference.open("r",newline="",encoding="utf-8-sig") as f:
        ref=list(csv.DictReader(f))
    metadata=reference_meta(ref)
    with gzip.open(args.gps,"rt",newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        required={"timestamp","individual-local-identifier","tag-local-identifier",
                  "individual-taxon-canonical-name","location-long","location-lat","ground-speed"}
        if not required<=set(reader.fieldnames or ()):
            raise ValueError("GPS non-altitude reference columns missing "+str(required-set(reader.fieldnames or ())))
        first,labels,audit=screen_fixes(reader)
        gps_has_height="height-above-msl" in set(reader.fieldnames or ())
    linked=safe_crosswalk(ref,labels)
    weather,regimes=fetch_weather(metadata["site_centers"])
    support=xysupport(first,linked["site_by_bird"],regimes)
    result={
      "phase":"ZEELBRUGGE_2016_PREOUTCOME_CONTEXT_GATE",
      "source_reference_md5":refmd,"source_gps_md5":gpsmd,
      "reference":metadata,
      "gps":audit,
      "bird_to_site_mapping":{k:v for k,v in linked.items() if k!="site_by_bird"},
      "regional_cerra":weather,
      "structural":support,
      "source_has_altitude_column":gps_has_height,
      "height_or_biological_effect_opened":False,
      "claim_boundary":"2016 CERRA at four colony centroids, not exact birds' flight updraft; climate association not causal.",
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
       "mapping":{k:v for k,v in linked.items() if k!="site_by_bird"},
       "birdcounts":support,
       "wind_days":{site:{m:q["n_calendar_days"] for m,q in info["thresholds_by_month"].items()} for site,info in weather.items()}
    },sort_keys=True))


if __name__=="__main__":
    main()
