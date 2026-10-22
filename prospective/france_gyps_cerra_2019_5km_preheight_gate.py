#!/usr/bin/env python3
"""Independent CERRA colony-wind source-support gate, zero altitude access.

A separately declared post-outcome ecological extension: original GPS/baro
identity effects already opened. This script DOES NOT score any height.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,statistics,time,urllib.parse,urllib.request,zipfile
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from . import france_griffon_2019_xytime_preflight as gps

YEARS=(2019,2020,2021)
COLONY=(44.2,3.25) # Sassi et al. study independent Cassagne feeding site
SOURCE_5MIN=742078
SOURCE_5KM_SHA="031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928"
TAG_ALIAS="182208"
MIN_STATE_FIXES=10
MIN_DAY_FIXES=20
MIN_OTHER_BIRDS=2
MIN_BIRDS=10
MIN_BIRD_REGIME_DAYS=2


def get_cerra():
    daily={}
    grid=None
    calendar_years={}
    for year in YEARS:
        params=dict(latitude=str(COLONY[0]),longitude=str(COLONY[1]),
            start_date=f"{year}-01-01",end_date=f"{year}-12-31",
            hourly="wind_speed_100m",wind_speed_unit="ms",timezone="UTC",models="cerra")
        url="https://archive-api.open-meteo.com/v1/archive?"+urllib.parse.urlencode(params)
        for trial in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url,headers={
                    "User-Agent":"ODSP-research-frozen-CERRA-colony-wind/1.0"}),timeout=90) as response:
                    x=json.load(response)
                break
            except Exception:
                if trial==2:raise
                time.sleep(4*(trial+1))
        if x.get("utc_offset_seconds")!=0 or x["hourly_units"].get("wind_speed_100m")!="m/s":
            raise ValueError("CERRA source time or wind units changed")
        loc=(float(x["latitude"]),float(x["longitude"]))
        if grid and any(abs(a-b)>1e-5 for a,b in zip(grid,loc)):
            raise ValueError("Study CERRA grid location changed between years")
        grid=loc
        hourly=defaultdict(list)
        for t,w in zip(x["hourly"]["time"],x["hourly"]["wind_speed_100m"]):
            z=gps.numeric(w)
            if z is not None and z>=0:hourly[t[:10]].append(z)
        means={d:float(statistics.mean(v)) for d,v in hourly.items() if len(v)>=20}
        daily.update(means)
        calendar_years[str(year)]={"complete_days":len(means),
            "finite_hourly_wind":sum(map(len,hourly.values()))}
    if len(daily)<1050:raise ValueError("Insufficient independent historical CERRA calendar")
    by_month=defaultdict(list)
    for d,v in daily.items():by_month[d[:7]].append(v)
    thresholds={}
    for m,v in sorted(by_month.items()):
        if len(v)<20:raise ValueError("CERRA source month <20 valid days: "+m)
        q25,q75=np.quantile(v,[.25,.75])
        thresholds[m]={"q25":float(q25),"q75":float(q75),"valid_calendar_days":len(v)}
    states={d:(0 if v<=thresholds[d[:7]]["q25"] else
               1 if v>=thresholds[d[:7]]["q75"] else -1)
            for d,v in daily.items()}
    manifest=dict(source="Open-Meteo CERRA 100m regional wind, UTC m/s",
        published_site_lat=COLONY[0],published_site_lon=COLONY[1],
        returned_grid_lat=grid[0],returned_grid_lon=grid[1],
        year_coverage=calendar_years,n_calendar_days=len(states),
        monthly_quartiles=thresholds,
        per_calendar_day_state_sha256=hashlib.sha256(
            json.dumps(states,sort_keys=True).encode()).hexdigest())
    return states,manifest


def source_meta(path):
    gps.source_digest(path)
    first={};tags=defaultdict(set);studies=defaultdict(set);audit=Counter()
    with zipfile.ZipFile(path) as z:
        members=[f for f in z.infolist() if not f.is_dir() and
                 not f.filename.startswith("__MACOSX/") and gps.PATTERN.search(f.filename)]
        if len(members)!=9:raise ValueError("Original GPS source has not exactly 9 seasonal CSVs")
        for f in sorted(members,key=lambda item:item.filename):
            source_year=int(gps.PATTERN.search(f.filename).group(2))
            with z.open(f) as raw,io.TextIOWrapper(raw,encoding="utf-8-sig",
                         errors="replace",newline="") as text:
                gps.select_rows(csv.reader(text),first,audit,tags,studies,source_year)
    quality=gps.analyze(first,audit,tags,studies)
    if (len(first)!=SOURCE_5MIN or quality["selected_biological_animals"]!=29
        or quality["horizontal_day_eligibility_by_cell_m"]["5000"]["source_bird_ID_sha256"]!=SOURCE_5KM_SHA):
        raise ValueError("Independent source QA roster changed before CERRA wind context")
    tagowners=defaultdict(set)
    for bird,ids in tags.items():
        for native_tag in ids:tagowners[native_tag].add(bird)
    conflicts={t:sorted(b) for t,b in tagowners.items() if len(b)>1}
    if set(conflicts)!={TAG_ALIAS}:
        raise ValueError("Native GPS tag aliases no longer match preheight QA receipt")
    quarantine={b for birds in conflicts.values() for b in birds}
    clean={key:v for key,v in first.items() if key[0] not in quarantine}
    return clean,dict(
        prior_GPS_first5min_fix_count=len(first),
        source_first5min_after_tag_quarantine=len(clean),
        prior_preheight_5km_bird_sha=SOURCE_5KM_SHA,
        tag_collision_by_native_id=conflicts,
        excluded_bird_count=len(quarantine),
        distinct_biological_bird_ids_after_quarantine=len({b for b,d,k in clean}),
        native_height_parsed=False)


def score_structural(first,regime):
    daycell=Counter();own=Counter();whole=Counter();datecell=Counter()
    monthbirdstate=Counter();monthbirddate=Counter()
    birdyear=defaultdict(set)
    for (bird,day,bin5),(_,lon,lat,hdop,sat,tag) in first.items():
        x,y=gps.PROJECTOR.transform(lon,lat)
        if not(math.isfinite(x) and math.isfinite(y)):raise ValueError("Failed original XY projection")
        cell=(math.floor(x/5000),math.floor(y/5000))
        daycell[bird,day,cell]+=1
        birdyear[day[:4]].add(bird)
        state=regime.get(day,-1)
        if state>=0:
            monthbirdstate[cell,day[:7],bird,state]+=1
            monthbirddate[cell,day[:7],bird,state,day]+=1
    for (bird,day,cell),n in daycell.items():
        own[bird,cell]+=n;whole[cell]+=n;datecell[day,cell]+=n
    bycellmonth=defaultdict(set)
    for cell,month,bird,state in monthbirdstate:
        bycellmonth[cell,month].add(bird)
    usual=Counter();own_state=Counter();pop_same_month=Counter()
    for (bird,day,cell),n in daycell.items():
        self_ref=own[bird,cell]-n
        other_ref=whole[cell]-own[bird,cell]-datecell[day,cell]+n
        if self_ref<10 or other_ref<10:continue
        usual[bird,day]+=n
        state=regime.get(day,-1)
        if state<0:continue
        month=day[:7]
        own_same=(monthbirdstate[cell,month,bird,state]-
                  monthbirddate[cell,month,bird,state,day])
        own_opp=monthbirdstate[cell,month,bird,1-state]
        if own_same<MIN_STATE_FIXES or own_opp<MIN_STATE_FIXES:continue
        own_state[bird,day,state]+=n
        other_birds=0
        for candidate in bycellmonth[cell,month]:
            if candidate==bird:continue
            low=(monthbirdstate[cell,month,candidate,0]-
                 monthbirddate[cell,month,candidate,0,day])
            high=(monthbirdstate[cell,month,candidate,1]-
                  monthbirddate[cell,month,candidate,1,day])
            if low>=MIN_STATE_FIXES and high>=MIN_STATE_FIXES:
                other_birds+=1
        if other_birds>=MIN_OTHER_BIRDS:
            pop_same_month[bird,day,state]+=n

    def summarize(counters):
        days=Counter();state_days=Counter()
        for key,n in counters.items():
            if n<MIN_DAY_FIXES:continue
            bird,day=key[:2]
            days[bird]+=1
            if len(key)==3:state_days[bird,key[2]]+=1
        if state_days:
            birds={b for b in days if state_days[b,0]>=MIN_BIRD_REGIME_DAYS
                   and state_days[b,1]>=MIN_BIRD_REGIME_DAYS}
        else:birds={b for b in days if days[b]>=2}
        return dict(
            birds=len(birds),bird_days=sum(days[b] for b in birds),
            selected_GPS_fixes=sum(n for key,n in counters.items()
                if key[0] in birds and n>=MIN_DAY_FIXES),
            admitted=len(birds)>=MIN_BIRDS,
            bird_IDs_sha256=hashlib.sha256("\n".join(sorted(birds)).encode()).hexdigest(),
            bird_IDs=sorted(birds),
            low_bird_days=sum(state_days[b,0] for b in birds),
            high_bird_days=sum(state_days[b,1] for b in birds))
    return {
       "raw_nonheight_birds_by_year":{k:len(v) for k,v in sorted(birdyear.items())},
       "ordinary_5km_bird_identity_support":summarize(usual),
       "5km_own_low_high_regional_wind_support":summarize(own_state),
       "5km_shared_species_wind_reference_support":summarize(pop_same_month),
       "source_n_bird_day_5km_cells":len(daycell),
       "regional_wind_is_exposure_proxy":True,
       "height_values_read":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    opt=p.parse_args()
    wind,weather=get_cerra()
    first,src_info=source_meta(opt.source)
    population=score_structural(first,wind)
    answer={
      "analysis":"FRANCE_GYPS_2019_2021_CERRA_WIND_5KM_SOURCE_ADMISSION_V1",
      "stage":"POST_PRIOR_HEIGHT_BUT_CURRENT_WIND_OUTCOME_BLIND_SOURCE_GATE",
      "source_original_DOI":"10.48579/PRO/IOSZNM",
      "source_zip_md5":gps.SOURCE_MD5,
      "source_preheight_reinspection":src_info,
      "independent_CERRA_regional_wind":weather,
      "population":population,
      "no_altitude_values_accessed_this_analysis":True,
      "wind_and_flight_mechanisms_tested":False,
      "original_GPS_baro_5km_identity_effect_changed":False,
      "interpretation":"Only source population feasibility for a NEW shared response baseline. Regional colony CERRA wind is not each bird's experienced air flow; main GPS/baro identity effect was opened earlier and this extension is exploratory."
    }
    opt.out.parent.mkdir(parents=True,exist_ok=True)
    opt.out.write_text(json.dumps(answer,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    p=population
    print(json.dumps({
      "wild_source_birds_after_tag_collision_quarantine":src_info["distinct_biological_bird_ids_after_quarantine"],
      "wind_calendar_days":weather["n_calendar_days"],
      "ordinary_5km_birds":p["ordinary_5km_bird_identity_support"]["birds"],
      "own_bird_low_high_5km_birds":p["5km_own_low_high_regional_wind_support"]["birds"],
      "shared_species_wind_5km_birds":p["5km_shared_species_wind_reference_support"]["birds"],
      "shared_species_wind_5km_admitted":p["5km_shared_species_wind_reference_support"]["admitted"],
      "height_opened_in_this_gate":False
    },sort_keys=True))


if __name__=="__main__":main()
