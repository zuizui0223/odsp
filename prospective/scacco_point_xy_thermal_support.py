#!/usr/bin/env python3
"""Pointwise OUTCOME-BLIND source and airflow support for 38 flight taxa.

Input: 14 nonvertical fields extracted from the frozen Scacco et al 2026 RDS.
Outputs study×species×bird-day eligibility, same-cell cross-day support,
pointwise thermal/wind/flight-mode annotation coverage, and low/high thermal
state recurrence. Does NOT read GPS altitude values.
"""
from __future__ import annotations

import argparse,csv,gzip,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np
from pyproj import Transformer

FIELDS={
    "study_id","study_name","species","animal_id","timestamp",
    "lon","lat","segment_id","data_source","flap_probability","vedba",
    "wind_speed_1000m","orographic_uplift","thermal_uplift"
}
PREDICTORS=("thermal_uplift","orographic_uplift",
            "wind_speed_1000m","flap_probability","vedba")
OVERLAPS={
    "150450794":"Rotics 2013 stork source",
    "332044860":"Flack 2014 stork source",
    "21231406":"LifeTrack white-stork broad parent / possible Flack overlap",
    "985143423":"Zeebrugge gull previously opened",
    "404939825":"BATTER Eidolon previously tested"
}
PROJECTOR=Transformer.from_crs("EPSG:4326","EPSG:6933",always_xy=True)
GRIDS=(5000,50000)
MIN_DAY=20
MIN_OTHER=10
MIN_SELF=10
MIN_BIRD_DAYS=2
MIN_BIRDS=10


def finite(v):
    try:a=float(v)
    except(ValueError,TypeError):return None
    return a if math.isfinite(a) else None


def normalized_source(row):
    study=(row.get("study_id") or "").strip()
    label=(row.get("study_name") or "").strip()
    source=(row.get("data_source") or "").strip() or "unknown"
    if study.upper() in {"NA","NAN","NULL","NONE",""}:
        if not label or label.upper() in {"NA","NAN","NULL","NONE"}:
            return source,"UNRESOLVED-STUDY",False
        return source,"NAME-ONLY:"+label,False
    return source,study,True


def selected_points(rows):
    earliest={}
    source_c=Counter()
    original_ids=defaultdict(set)
    for r in rows:
        source_c["all_rows"]+=1
        source,study,identified=normalized_source(r)
        bird=(r.get("animal_id") or "").strip()
        species=(r.get("species") or "").strip()
        stamp=(r.get("timestamp") or "").strip()
        segment=(r.get("segment_id") or "").strip()
        if not (bird and species and segment and len(stamp)>=16):
            source_c["missing_id_time"]+=1;continue
        if (stamp[4:5],stamp[7:8])!=("-","-"):
            source_c["bad_timestamp"]+=1;continue
        try:yy,mm,dd,hh,minute=(int(stamp[:4]),int(stamp[5:7]),int(stamp[8:10]),int(stamp[11:13]),int(stamp[14:16]))
        except (ValueError,TypeError):
            source_c["bad_timestamp"]+=1;continue
        if not(2007<=yy<=2024 and 1<=mm<=12 and 1<=dd<=31 and 0<=hh<24 and 0<=minute<60):
            source_c["outside_declared_year_or_bad_time"]+=1;continue
        lon=finite(r.get("lon"));lat=finite(r.get("lat"))
        if lon is None or lat is None or not(-180<=lon<=180 and -85<=lat<=85):
            source_c["missing_or_invalid_xy"]+=1;continue
        original_ids[source,study,species].add(bird)
        k=(source,study,species,bird,stamp[:10],hh*12+minute//5)
        p=(stamp,lon,lat,
           finite(r.get("thermal_uplift")),
           finite(r.get("orographic_uplift")),
           finite(r.get("wind_speed_1000m")),
           finite(r.get("flap_probability")),
           finite(r.get("vedba")))
        if k not in earliest or stamp<earliest[k][0]:
            earliest[k]=p
        source_c["time_xy_valid_rows"]+=1
    source_c["selected_5min_unique_fixes"]=len(earliest)
    return earliest,source_c,original_ids


def shared_cells(records,scale):
    # records are (bird, UTC date, x, y, environment...).
    daycell=Counter();owncell=Counter();totalcell=Counter();datecell=Counter()
    for bird,day,x,y,env in records:
        cell=(math.floor(x/scale),math.floor(y/scale))
        daycell[bird,day,cell]+=1
    for (bird,day,cell),n in daycell.items():
        owncell[bird,cell]+=n
        totalcell[cell]+=n
        datecell[day,cell]+=n
    scorable=Counter()
    for (bird,day,cell),n in daycell.items():
        own_other=owncell[bird,cell]-n
        others_on_other_dates=totalcell[cell]-owncell[bird,cell]-datecell[day,cell]+n
        if own_other>=MIN_SELF and others_on_other_dates>=MIN_OTHER:
            scorable[bird,day]+=n
    eligible_bird_days=Counter()
    for (bird,day),n in scorable.items():
        if n>=MIN_DAY:
            eligible_bird_days[bird]+=1
    eligible={bird for bird,n in eligible_bird_days.items() if n>=MIN_BIRD_DAYS}
    return {
        "scale_m":scale,
        "raw_bird_days":len({(b,d) for b,d,x,y,e in records}),
        "cells_with_fixes":len(totalcell),
        "scorable_birds":len(eligible),
        "scorable_bird_days":sum(eligible_bird_days[b] for b in eligible),
        "scored_5min_fix_records":sum(v for (b,d),v in scorable.items()
                                     if b in eligible and v>=MIN_DAY),
        "admitted_identity_source":len(eligible)>=MIN_BIRDS,
        "scorable_bird_id_hash":hashlib.sha256("\n".join(sorted(eligible)).encode()).hexdigest(),
        "daycell":daycell,
        "owncell":owncell,
        "totalcell":totalcell,
        "datecell":datecell,
    }


def climate_context_gate(records,shared,scale):
    # This is eligibility ONLY, not vertical identity or observed uplift response.
    monthly=defaultdict(list)
    daythermal=defaultdict(list)
    for bird,day,x,y,env in records:
        thermal=env[0]
        if thermal is not None and thermal>=0:
            daythermal[bird,day].append(thermal)
    for (bird,day),v in daythermal.items():
        if len(v)>=MIN_DAY:
            monthly[day[:7]].append(float(np.median(v)))
    thresholds={
        m:[float(x) for x in np.quantile(v,[.25,.75])]
        for m,v in monthly.items() if len(v)>=4
    }
    assigned={}
    for (bird,day),values in daythermal.items():
        if len(values)<MIN_DAY:continue
        q=thresholds.get(day[:7])
        if q is None:continue
        med=float(np.median(values))
        assigned[bird,day]=0 if med<=q[0] else (1 if med>=q[1] else -1)
    by_id_cell_state=Counter()
    for (bird,day,cell),n in shared["daycell"].items():
        state=assigned.get((bird,day),-1)
        if state in (0,1):by_id_cell_state[bird,cell,state]+=n
    scored=Counter()
    for (bird,day,cell),n in shared["daycell"].items():
        state=assigned.get((bird,day),-1)
        if state not in (0,1):continue
        own_same_state_other_day=by_id_cell_state[bird,cell,state]-n
        opposite_state_events=by_id_cell_state[bird,cell,1-state]
        others_other_dates=(
            shared["totalcell"][cell]-shared["owncell"][bird,cell]
            -shared["datecell"][day,cell]+n
        )
        if (own_same_state_other_day>=MIN_SELF and
            opposite_state_events>=MIN_SELF and others_other_dates>=MIN_OTHER):
            scored[bird,day,state]+=n
    by_bird_state=Counter()
    for (bird,day,state),n in scored.items():
        if n>=MIN_DAY:by_bird_state[bird,state]+=1
    birds={bird for bird,state in by_bird_state
           if by_bird_state[bird,0]>=2 and by_bird_state[bird,1]>=2}
    return {
       "wind_uplift_regime":"bird-day median of source ERA5 thermal uplift potential; monthly 25th/75th quartiles, not GPS altitude",
       "thresholds_by_month":dict(sorted(thresholds.items())),
       "bird_days_with_valid_thermal":len(daythermal),
       "bird_days_labeled_extreme_thermal":sum(s in (0,1) for s in assigned.values()),
       "birds_with_two_qualifying_low_and_high_days":len(birds),
       "bird_id_fingerprint":hashlib.sha256("\n".join(sorted(birds)).encode()).hexdigest(),
       "context_screen_admitted":len(birds)>=MIN_BIRDS,
       "ecological_outcome_tested":False
    }


def summarize(earliest,counters,original_ids):
    per_panel=defaultdict(list)
    for (source,study,species,bird,day,bin5),(_,lon,lat,*env) in earliest.items():
        x,y=PROJECTOR.transform(lon,lat)
        if not(math.isfinite(x) and math.isfinite(y)):continue
        per_panel[source,study,species].append((bird,day,x,y,tuple(env)))
    panels=[]
    for (source,study,species),data in sorted(per_panel.items()):
        coverage={name:sum(p[4][i] is not None for p in data)/len(data)
                  for i,name in enumerate(("thermal_uplift","orographic_uplift",
                      "wind_speed_1000m","flap_probability","vedba"))}
        d={"data_source":source,"study_id":study,"species":species,
           "original_unique_birds_with_any_timestamp_xy":len(original_ids[source,study,species]),
           "source_distinct_birds_with_5min_points":len({x[0] for x in data}),
           "source_5min_point_fixes":len(data),
           "environment_completeness":coverage,
           "identified_numeric_study":not study.startswith(("NAME-ONLY:","UNRESOLVED")),
           "previous_source_overlap":OVERLAPS.get(study),
           "independent_new_parent_candidate":(study not in OVERLAPS and not study.startswith(("NAME-ONLY:","UNRESOLVED"))),
        }
        for scale in GRIDS:
            shared=shared_cells(data,scale)
            d["horizontal_"+str(scale)]={k:v for k,v in shared.items()
                if k not in ("daycell","owncell","totalcell","datecell")}
            d["thermal_"+str(scale)]=climate_context_gate(data,shared,scale)
        d["primary_study_species_screen"]={
            "5km_identity_eligible":d["horizontal_5000"]["admitted_identity_source"],
            "5km_thermal_context_eligible":d["thermal_5000"]["context_screen_admitted"],
            "both_thermal_and_flap_probability_80pct":(
                coverage["thermal_uplift"]>=.8 and coverage["flap_probability"]>=.8
            ),
            "new_independent_source_eligible":(
                d["independent_new_parent_candidate"]
                and d["horizontal_5000"]["admitted_identity_source"]
                and d["thermal_5000"]["context_screen_admitted"]
                and coverage["thermal_uplift"]>=.8 and coverage["flap_probability"]>=.8
            )
        }
        panels.append(d)
    return {
        "stage":"ALTIUDE_BLIND_POINT_XY_AND_ENVIRONMENT_COVERAGE_ONLY",
        "scacco_source_record":"10.5281/zenodo.21915776",
        "source_GPS_rows_selected_time_XY":dict(counters),
        "source_species":len({v["species"] for v in panels}),
        "source_study_species_panels":len(panels),
        "source_id_studies":len({v["study_id"] for v in panels}),
        "studies_with_at_least_10_birds_same_5km_cell":sum(
            v["horizontal_5000"]["admitted_identity_source"] for v in panels),
        "studies_with_at_least_10_birds_same_50km_cell":sum(
            v["horizontal_50000"]["admitted_identity_source"] for v in panels),
        "study_species_panels_with_5km_uplift_context":sum(
            v["thermal_5000"]["context_screen_admitted"] for v in panels),
        "panels_new_independent_5km_thermal_eligible":sum(
            v["primary_study_species_screen"]["new_independent_source_eligible"]
            for v in panels),
        "candidate_new_independent_species":sorted({
            v["species"] for v in panels
            if v["primary_study_species_screen"]["new_independent_source_eligible"]
        }),
        "catalog_panels":panels,
        "RDS_deserialized_no_height_columns_selected_for_export":True,
        "numerical_altitude_values_accessed_for_screen":False,
        "altitude_completeness_or_shape_computed":False,
        "instrument_calibration_performed":False,
        "biological_outcomes_computed":False,
        "rights":"Zenodo 10.5281/zenodo.21915776 CC BY 4.0; cite Scacco et al and source study owners.",
        "environment_limit":"Thermal Wstar varies with animal-chosen position and UTC time, an observational opportunity proxy, not airborne uplift actually encountered."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--nonvertical-tsv-gz",required=True,type=str)
    p.add_argument("--out",required=True,type=str)
    args=p.parse_args()
    with gzip.open(args.nonvertical_tsv_gz,"rt",encoding="utf-8-sig",newline="") as f:
        rows=csv.DictReader(f,delimiter="\t")
        if not FIELDS.issubset(set(rows.fieldnames or [])):
            raise ValueError("source RDS metadata exporter did not supply required nonheight fields")
        earliest,counters,ids=selected_points(rows)
    result=summarize(earliest,counters,ids)
    dest=Path(args.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps({
        "raw_taxa":result["source_species"],
        "study_species_panels":result["source_study_species_panels"],
        "5km_identity_panels":result["studies_with_at_least_10_birds_same_5km_cell"],
        "5km_thermal_context_panels":result["study_species_panels_with_5km_uplift_context"],
        "50km_identity_panels":result["studies_with_at_least_10_birds_same_50km_cell"],
        "new_independent_thermal_panels":result["panels_new_independent_5km_thermal_eligible"],
        "new_independent_species":result["candidate_new_independent_species"],
        "altitude_used":False
    },sort_keys=True))


if __name__=="__main__":
    main()
