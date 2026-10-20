#!/usr/bin/env python3
"""Metadata-only gate: source-annotated wind x behavior x shared horizontal cell.

Must not read numeric altitude, altitude_adl or altitude_agl values. Each native
project is a separate independent panel and every GPS fix is selected before
availability of wind or height fields is evaluated.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime
import numpy as np
from pyproj import Transformer

SOURCE_FILE="Data_table_per_GPS_points.csv"
SOURCE_MD5="e321f09953b8ce80ed878a4810be3dee"
MODES={"flap","soar"}
UTM="EPSG:32631"
MIN_FLIGHT_DAY=20
MIN_EVAL_EVENTS_PER_MODE_DAY=20
CELL_M=5000
MIN_TRAIN_STATE=10
MIN_PER_BIRD_EVAL_DAYS_EACH_STATE=2
MIN_SPECIES_BIRDS=10


def number(raw):
    try:
        x=float(raw)
        return x if math.isfinite(x) else None
    except (ValueError,TypeError):
        return None


def safe_stamp(text):
    try:
        d=datetime.fromisoformat((text or "").strip().replace("Z","+00:00"))
    except (ValueError,TypeError):
        return None
    return d


def source_metadata_gate(rows)->dict:
    first={}
    audit=Counter()
    seen_years=defaultdict(Counter)
    for row in rows:
        audit["source_rows"]+=1
        study=(row.get("project") or "").strip()
        bird=(row.get("device_info_serial") or "").strip()
        stamp=safe_stamp(row.get("date_time"))
        mode=(row.get("class_name") or "").strip().lower()
        if not study or not bird or stamp is None or stamp.year not in (2015,2016,2017):
            audit["missing_project_id_or_date"]+=1
            continue
        seen_years[study][stamp.year]+=1
        if mode not in MODES:
            audit["excluded_class"]+=1
            continue
        speed=number(row.get("speed_2d"))
        lon=number(row.get("longitude"));lat=number(row.get("latitude"))
        if speed is None or speed <5 or speed>55 or lon is None or lat is None or not(-180<=lon<=180 and -90<=lat<=90):
            audit["missing_or_bad_xy_speed"]+=1
            continue
        day=stamp.date().isoformat()
        bin5=stamp.hour*12+stamp.minute//5
        key=(study,bird,day,bin5)
        prev=first.get(key)
        if prev is None or stamp<prev[0]:
            first[key]=(stamp,lon,lat,mode,row.get("wspeed"))
        audit["eligible_raw_flight_events"]+=1
    audit["selected_5min_bins"]=len(first)
    transformer=Transformer.from_crs("EPSG:4326",UTM,always_xy=True)
    by_day=defaultdict(list)
    for (project,bird,day,b),(_,lon,lat,mode,wraw) in first.items():
        ws=number(wraw)
        if ws is None or ws<0:
            audit["selected_missing_wind"]+=1
        xx,yy=transformer.transform(lon,lat)
        if not(math.isfinite(xx) and math.isfinite(yy)):
            audit["bad_projected_xy"]+=1
            continue
        cell=(math.floor(xx/CELL_M),math.floor(yy/CELL_M))
        by_day[project,bird,day].append((mode,ws,cell))
    all_projects=sorted(seen_years)
    per_project={}
    for proj in all_projects:
        panel_days={k:v for k,v in by_day.items() if k[0]==proj and len(v)>=MIN_FLIGHT_DAY}
        medians={}
        by_year_medians=defaultdict(list)
        for (project,bird,day),events in panel_days.items():
            w=[z for mode,z,cell in events if z is not None]
            if not w:continue
            mid=float(statistics.median(w))
            medians[project,bird,day]=mid
            by_year_medians[int(day[:4])].append(mid)
        quartiles={}
        for year, vals in sorted(by_year_medians.items()):
            q25,q75=np.quantile(vals,[.25,.75])
            quartiles[year]={"q25":float(q25),"q75":float(q75),
                              "qualifying_bird_days":len(vals)}
        labelled={}
        for key,ws in medians.items():
            q=quartiles[int(key[2][:4])]
            if ws<=q["q25"]:labelled[key]="low"
            elif ws>=q["q75"]:labelled[key]="high"
            else:labelled[key]="middle"
        counted=Counter()
        date_cells=Counter()
        by_bird=Counter()
        days_per_state=Counter()
        for key,events in panel_days.items():
            state=labelled.get(key)
            if state not in ("low","high"):continue
            _,bird,day=key
            for mode,ws,cell in events:
                if ws is None:continue
                counted[bird,mode,cell,state,day]+=1
                by_bird[bird,mode,cell,state]+=1
                date_cells[day,mode,cell,state]+=1
        scored=Counter()
        for (bird,mode,cell,state,day),n in counted.items():
            own_other_state=by_bird[bird,mode,cell,state]-n
            if own_other_state>=MIN_TRAIN_STATE:
                scored[bird,mode,state,day]+=n
        individual_mode_states=defaultdict(Counter)
        for (bird,mode,state,day),n in scored.items():
            if n>=MIN_EVAL_EVENTS_PER_MODE_DAY:
                individual_mode_states[bird,mode][state]+=1
        eligible={m:set() for m in MODES}
        for (bird,mode),n in individual_mode_states.items():
            if n["low"]>=MIN_PER_BIRD_EVAL_DAYS_EACH_STATE and n["high"]>=MIN_PER_BIRD_EVAL_DAYS_EACH_STATE:
                eligible[mode].add(bird)
        per_project[proj]={
            "source_rows_by_year":dict(sorted(seen_years[proj].items())),
            "source_distinct_birds":len({a for p,a,d in by_day if p==proj}),
            "bird_days_ge20":len(panel_days),
            "median_weather_bird_days":len(medians),
            "wind_quartiles_by_year":quartiles,
            "flight_modes":{
                mode:{
                    "candidate_birds":len(eligible[mode]),
                    "admitted":len(eligible[mode])>=MIN_SPECIES_BIRDS,
                    "eligible_id_sha256":hashlib.sha256("\n".join(sorted(eligible[mode])).encode()).hexdigest(),
                    "birds_with_both_wind_regimes_any_day":sum(
                        z["low"]>0 and z["high"]>0
                        for (bird,mo),z in individual_mode_states.items() if mo==mode
                    ),
                    "scorable_day_mode_wind_groups":sum(
                        n>=MIN_EVAL_EVENTS_PER_MODE_DAY for (b,mo,st,d),n in scored.items() if mo==mode
                    ),
                    "scorable_fixes_for_eligible_birds":sum(
                        n for (b,mo,st,d),n in scored.items()
                        if mo==mode and b in eligible[mode] and n>=MIN_EVAL_EVENTS_PER_MODE_DAY
                    )
                } for mode in sorted(MODES)
            }
        }
    return {
        "phase":"PRE_OUTCOME_XY_WIND_AND_BEHAVIOR_ONLY",
        "height_or_shape_values_read":False,
        "source_file":SOURCE_FILE,
        "fixed_gates":{
            "flight_mode":sorted(MODES),
            "speed_ms":[5,55],"min_day_flight_fixes":MIN_FLIGHT_DAY,
            "min_heldout_day_mode_fixes":MIN_EVAL_EVENTS_PER_MODE_DAY,
            "min_state_same_bird_other_day_cell":MIN_TRAIN_STATE,
            "min_days_per_wind_regime_each_bird":MIN_PER_BIRD_EVAL_DAYS_EACH_STATE,
            "min_birds":MIN_SPECIES_BIRDS,
            "wind_quantiles":[.25,.75],
            "grid_m":CELL_M
        },
        "counts":dict(audit),
        "projects":per_project,
        "support_note":"This gate only requires same bird/mode/cell prior state >=10 in other days, not the wind-pooled baseline; check baseline with identical evaluation later.",
        "project_taxonomy_unverified":True
    }


def _md5(path):
    md5=hashlib.md5()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            md5.update(b)
    if path.name!=SOURCE_FILE or md5.hexdigest()!=SOURCE_MD5:
        raise ValueError("Archive input or published checksum mismatch")
    return md5.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    digest=_md5(args.csv)
    with args.csv.open("r",newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        mandatory={"project","device_info_serial","date_time","longitude","latitude","speed_2d","class_name","wspeed"}
        if not mandatory<=set(reader.fieldnames or []):
            raise ValueError("Source lacks mandatory native metadata columns "+str(mandatory-set(reader.fieldnames or [])))
        result=source_metadata_gate(reader)
        result["source_schema_has_height_fields"]={k:k in set(reader.fieldnames or []) for k in ("altitude","altitude_adl","altitude_agl")}
    result["source_md5"]=digest
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({p:{m:r["candidate_birds"] for m,r in obj["flight_modes"].items()} for p,obj in result["projects"].items()},sort_keys=True))


if __name__=="__main__":
    main()
