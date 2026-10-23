#!/usr/bin/env python3
"""2019–2021 French Gyps original GPS + independent CERRA wind opportunity gate.

HEIGHT-BLIND. Uses native ID, UTC date, lon/lat, native ground-speed and
archived quality flags, and independent regional reanalysis wind ONLY.
Does NOT read any native GPS/barometric height numbers or outcome missingness.

After the previously published D1 dual-sensor shape result this is an
EXPLORATORY new-weather design, not retrospectively confirmatory.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,statistics,time,urllib.parse,urllib.request,zipfile
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np
from pyproj import Transformer

from . import france_griffon_2019_xytime_preflight as src

SOURCE_SHA="b18cc8004d311d19ff24060f655178bf"
SOURCE_N=742423
SOURCE_ANIMALS=30
FROZEN_IDS=28
FROZEN_IDS_HASH="031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928"
CELL_M=5000
MIN_EVENT_DONORS=10
MIN_SCORED_DAY=20
MIN_BIRD_DAYS_STATE=2
MIN_BIRDS=10
PROJECTOR=Transformer.from_crs("EPSG:4326","EPSG:6933",always_xy=True)
WEATHER_API="https://archive-api.open-meteo.com/v1/archive"
YEARS=(2019,2020,2021)


def original_selected_birds(preheight):
    if (preheight.get("numeric_native_GPS_height_values_read") is not False
        or preheight.get("selected_native_GPS_five_minute_events")!=SOURCE_N
        or preheight.get("selected_biological_animals")!=SOURCE_ANIMALS):
        raise ValueError("Prior outcome-blind source GPS eligibility changed")
    source=preheight["horizontal_day_eligibility_by_cell_m"]["5000"]
    birds=set(source.get("admitted_bird_ids",[]))
    checksum=hashlib.sha256("\n".join(sorted(birds)).encode()).hexdigest()
    if (len(birds)!=FROZEN_IDS or
        source.get("source_bird_ID_sha256")!=FROZEN_IDS_HASH or
        checksum!=FROZEN_IDS_HASH or not source.get("admitted")):
        raise ValueError("Source 28-bird 5km cohort/ID hash changed")
    return birds


def original_first_xy(zip_path):
    src.source_digest(zip_path)
    first={};c=Counter();tags=defaultdict(set);study_names=defaultdict(set)
    with zipfile.ZipFile(zip_path) as archive:
        members=[f for f in archive.infolist() if not f.is_dir()
                 and src.PATTERN.search(f.filename)
                 and not f.filename.startswith("__MACOSX/")]
        if len(members)!=9:
            raise ValueError("Original ZIP must contain all nine native year-season source GPS files")
        for member in sorted(members,key=lambda x:x.filename):
            year=int(src.PATTERN.search(member.filename).group(2))
            with archive.open(member) as raw,io.TextIOWrapper(
                raw,encoding="utf-8-sig",errors="replace",newline=""
            ) as text:
                src.select_rows(csv.reader(text),first,c,tags,study_names,year)
            print("Source season",member.filename.rsplit("/",1)[-1],
                  "unique original XY bins",len(first),flush=True)
    if (len(first)!=SOURCE_N or len({bird for bird,day,bin5 in first})!=SOURCE_ANIMALS):
        raise ValueError("Source first-eligible 742,423/30 metadata cohort differs")
    return first


def source_center(first,eligible):
    # A bird with more GPS fixes must not determine the regional ERA5 grid.
    by_bird=defaultdict(lambda: [[],[]])
    for (bird,day,bin5),(timestamp,lon,lat,hdop,satellites,tag) in first.items():
        if bird in eligible:
            by_bird[bird][0].append(lon)
            by_bird[bird][1].append(lat)
    if set(by_bird)!=eligible:
        raise ValueError("Original 28 birds not all represented in weather source")
    per_bird_median={
        bird:[float(statistics.median(x[0])),float(statistics.median(x[1]))]
        for bird,x in by_bird.items()
    }
    lon=float(statistics.median(z[0] for z in per_bird_median.values()))
    lat=float(statistics.median(z[1] for z in per_bird_median.values()))
    center={"longitude":round(lon,6),"latitude":round(lat,6),
            "n_equal_weighted_birds":len(per_bird_median),
            "formula":"Median of each source bird's native nonvertical 5minute event-coordinate median, then median across original 28 bird medians"}
    return center


def fetch_cerra(year,center,opener=None):
    params={
        "latitude":f"{center['latitude']:.6f}",
        "longitude":f"{center['longitude']:.6f}",
        "start_date":f"{year}-01-01","end_date":f"{year}-12-31",
        "hourly":"wind_speed_100m,shortwave_radiation",
        "wind_speed_unit":"ms",
        "timezone":"UTC","models":"cerra",
    }
    url=WEATHER_API+"?"+urllib.parse.urlencode(params)
    response=None
    if opener is not None:
        response=opener(url)
    else:
        for attempt in range(3):
            try:
                req=urllib.request.Request(url,headers={
                    "User-Agent":"source-verified-independent-ecology-Gyps-CERRA/1.0",
                    "Accept":"application/json"
                })
                with urllib.request.urlopen(req,timeout=120) as stream:
                    response=json.load(stream)
                break
            except (TimeoutError,urllib.error.URLError,ValueError):
                if attempt==2:raise
                time.sleep(4*(attempt+1))
    if response.get("utc_offset_seconds")!=0:
        raise ValueError("CERRA expected exact UTC hourly source")
    if response.get("hourly_units",{}).get("wind_speed_100m")!="m/s":
        raise ValueError("CERRA 100m wind must be in m/s")
    h=response.get("hourly") or {}
    if not len(h.get("time",[]))==len(h.get("wind_speed_100m",[])):
        raise ValueError("Weather hourly dates and wind row count mismatch")
    by_day=defaultdict(list)
    solar_by_day=defaultdict(list)
    for i,stamp in enumerate(h["time"]):
        if not stamp.startswith(str(year)+"-"):raise ValueError("CERRA queried year label mismatch")
        wind=src.numeric(h["wind_speed_100m"][i])
        solar=src.numeric(h.get("shortwave_radiation",[None]*len(h["time"]))[i])
        if wind is not None and wind>=0:by_day[stamp[:10]].append(wind)
        if solar is not None and solar>=0:solar_by_day[stamp[:10]].append(solar)
    daily={d:float(statistics.mean(v)) for d,v in by_day.items() if len(v)>=20}
    # Calendar-day quantile among all dates in the month, independently of
    # GPS bird movements or sensor height correctness.
    month=defaultdict(list)
    for d,v in daily.items():month[d[:7]].append(v)
    thresholds={}
    for m,vs in sorted(month.items()):
        if len(vs)<20:continue
        q25,q75=np.quantile(vs,[.25,.75])
        thresholds[m]={"low_max":float(q25),"high_min":float(q75),
                       "n_valid_climate_calendar_days":len(vs)}
    states={}
    for day,v in daily.items():
        limits=thresholds.get(day[:7])
        if limits is None:continue
        states[day]="low" if v<=limits["low_max"] else (
            "high" if v>=limits["high_min"] else "middle")
    metadata={
        "year":year,
        "query":params,
        "grid_latitude":response.get("latitude"),
        "grid_longitude":response.get("longitude"),
        "hourly_source_values":len(h["time"]),
        "valid_daily_winds":len(daily),
        "daily_mean_wind_100m_by_date":dict(sorted(daily.items())),
        "monthly_wind_quantile_thresholds":thresholds,
        "calendar_wind_regime_by_date":dict(sorted(states.items())),
        "days_low":sum(s=="low" for s in states.values()),
        "days_high":sum(s=="high" for s in states.values()),
        "days_middle":sum(s=="middle" for s in states.values()),
        "daily_mean_solar_Wm2_dates":{
            d:float(statistics.mean(v)) for d,v in sorted(solar_by_day.items())
            if len(v)>=20
        }
    }
    return metadata


def wind_opportunity(first,source_birds,states):
    daycell=Counter();perbird_weather=Counter()
    # Restrict original source to 28 height-blind spatially eligible birds.
    for (bird,day,bucket),(timestamp,lon,lat,hdop,sat,tag) in first.items():
        if bird not in source_birds:continue
        regime=states.get(day)
        if regime not in ("low","high","middle"):continue
        perbird_weather[bird,day]+=1
        x,y=PROJECTOR.transform(lon,lat)
        if not(math.isfinite(x) and math.isfinite(y)):
            raise ValueError("Previously validated source GPS projected invalid")
        cell=(math.floor(x/CELL_M),math.floor(y/CELL_M))
        daycell[bird,day,cell]+=1

    owncell=Counter();totalcell=Counter();datecell=Counter()
    own_state=Counter()
    month_state=Counter()
    month_day_state=Counter()
    by_cell_month_bird=defaultdict(set)
    for (bird,day,cell),n in daycell.items():
        owncell[bird,cell]+=n;totalcell[cell]+=n;datecell[day,cell]+=n
        state=states[day]
        if state in ("low","high"):
            own_state[bird,cell,state]+=n
            key=(day[:7],cell,bird,state)
            month_state[key]+=n
            month_day_state[day,cell,bird,state]+=n
            by_cell_month_bird[day[:7],cell].add(bird)

    candidate_day_state=Counter()
    shared_day_state=Counter()
    source_groups=Counter()
    for (bird,day,cell),n in daycell.items():
        state=states[day]
        if state not in ("low","high"):continue
        own_other=own_state[bird,cell,state]-n
        opposite=own_state[bird,cell,"high" if state=="low" else "low"]
        other_otherdate=totalcell[cell]-owncell[bird,cell]-datecell[day,cell]+n
        if own_other<10 or opposite<10 or other_otherdate<10:
            continue
        candidate_day_state[bird,day,state]+=n

        # Species-shared thermal odds are defined using independent birds
        # with observations in BOTH regimes in this same year-month/cell.
        nindependent=0
        for other in by_cell_month_bird[day[:7],cell]:
            if other==bird:continue
            donors={
                st:month_state[day[:7],cell,other,st]
                -month_day_state[day,cell,other,st]
                for st in ("low","high")
            }
            if donors["low"]>=10 and donors["high"]>=10:
                nindependent+=1
        if nindependent>=2:
            shared_day_state[bird,day,state]+=n
            source_groups[bird,day,state]+=nindependent*n

    def qualify(daystates):
        days=Counter()
        total_events=Counter()
        for (bird,day,state),n in daystates.items():
            if n>=MIN_SCORED_DAY:
                days[bird,state]+=1
                total_events[bird,state]+=n
        birds={bird for bird in source_birds
               if days[bird,"low"]>=MIN_BIRD_DAYS_STATE
               and days[bird,"high"]>=MIN_BIRD_DAYS_STATE}
        return {
            "n_individuals":len(birds),
            "individual_bird_ids":sorted(birds),
            "individual_ids_sha256":hashlib.sha256("\n".join(sorted(birds)).encode()).hexdigest(),
            "scorable_bird_days":sum(days[b,s] for b in birds for s in ("low","high")),
            "scorable_first_5min_fixes":sum(total_events[b,s] for b in birds for s in ("low","high")),
            "n_bird_days_low":sum(days[b,"low"] for b in birds),
            "n_bird_days_high":sum(days[b,"high"] for b in birds),
            "admitted":len(birds)>=MIN_BIRDS
        }
    potential=qualify(candidate_day_state)
    shared=qualify(shared_day_state)
    return {
        "study_source_first_5min_weather_labeled_fix_count":sum(daycell.values()),
        "original_28_source_birds_with_wind_labeled_fixes":len({b for b,d in perbird_weather}),
        "source_bird_days_with_wind_labeled_fixes":len(perbird_weather),
        "weather_label_source_fraction_of_28_bird_5min_fix_count":
            sum(daycell.values())/sum(
                1 for (b,d,k) in first if b in source_birds),
        "raw_day_cell_support_groups":len(daycell),
        "original_bird_own_wind_same_cell":potential,
        "shared_species_other_bird_same_yearmonth_wind_context":shared,
        "shared_reference_min_two_other_birds_each_both_regimes":True,
        "native_GPS_height_used":False,
        "barometric_height_used":False,
        "GPS_device_quality_dropped_on_value":False
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip",required=True,type=Path)
    p.add_argument("--preheight",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    pre=json.loads(args.preheight.read_text())
    selected=original_selected_birds(pre)
    source=original_first_xy(args.zip)
    center=source_center(source,selected)
    years={}
    for year in YEARS:
        years[str(year)]=fetch_cerra(year,center)
        print("CERRA source year:",year,
              "wind-calendar-days",years[str(year)]["valid_daily_winds"],flush=True)
    locs={(v["grid_latitude"],v["grid_longitude"]) for v in years.values()}
    if len(locs)!=1:
        raise ValueError("Same regional CERRA site must resolve to one grid for all years")
    regimes={}
    for year,weather in years.items():
        regimes.update(weather["calendar_wind_regime_by_date"])
    potential=wind_opportunity(source,selected,regimes)
    days_weather=sum(len(x["calendar_wind_regime_by_date"]) for x in years.values())
    if days_weather/sum(366 if y%4==0 else 365 for y in YEARS)<.8:
        raise ValueError("CERRA calendar source coverage below frozen 80 percent")
    out={
        "analysis":"FRENCH_GYPS_2019_2021_OUTCOME_BLIND_REGIONAL_CERRA_WIND_SOURCE_SUPPORT_V1",
        "source_study":"Eurasian griffon vulture in France (Grands Causses 2018) ID_PROG 961",
        "source_ZIP_MD5":SOURCE_SHA,
        "source_original_5km_birds":len(selected),
        "source_original_5km_bird_sha256":FROZEN_IDS_HASH,
        "source_first5min_5to55ms_gps":SOURCE_N,
        "source_equal_bird_median_centroid":center,
        "weather_model":"cerra",
        "weather_station_grid_long_lat":list(next(iter(locs))[::-1]),
        "weather_data_source":"https://archive-api.open-meteo.com/v1/archive",
        "weather_source_years":years,
        "calendar_days_with_wind_labels":days_weather,
        "source_wind_eligibility":potential,
        "environmental_regional_wind_not_local_updraft":True,
        "ALTITUDE_VALUES_OPENED_IN_THIS_SOURCE_GATE":False,
        "preexisting_height_D1_result_ALREADYPUBLISHED":True,
        "future_environment_analysis_post_outcome_exploratory":True,
        "source_overlap_evidence":"FRANCE_GYPS_ORIGINAL_STUDY_INDEPENDENCE_EVIDENCE_V1.json: different archived study name/zero literal birdID overlap, numeric Movebank source ID and original tag re-use not fully verified",
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "original_birds":len(selected),
        "wind_eligible_birds":potential["original_bird_own_wind_same_cell"]["n_individuals"],
        "shared_species_wind_eligible_birds":potential["shared_species_other_bird_same_yearmonth_wind_context"]["n_individuals"],
        "shared_species_days":potential["shared_species_other_bird_same_yearmonth_wind_context"]["scorable_bird_days"],
        "shared_species_first5min_fixes":potential["shared_species_other_bird_same_yearmonth_wind_context"]["scorable_first_5min_fixes"],
        "climate_calendar_days":days_weather,
        "source_coordinate":center,
        "original_dual_sensor_height_values_parsed":False
    },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
