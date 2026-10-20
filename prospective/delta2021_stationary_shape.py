#!/usr/bin/env python3
"""DELTATRACK 2021 low-speed stationary-altitude shape negative control (post-outcome).

The frozen 2021 flight-identity kernel is imported UNCHANGED for 100m-cell
stationary records. This is not a new independent biological confirmation.
"""
from __future__ import annotations

import argparse, csv, gzip, hashlib, json, math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from pyproj import Transformer

from . import medgull_sensitivity as engine

MD5="1a3145234cccd1a48b280b0fb485d679"
EXPECTED_NAME="DELTATRACK-gps-2021.csv.gz"
TAXA=("Larus argentatus","Larus fuscus")
EDGES=np.array([-np.inf,-200,-100,-50,-25,0,25,50,100,200,np.inf])
SEED=20261022
DRAW_N=999


def verify(path: Path):
    h=hashlib.md5();sha=hashlib.sha256()
    with path.open("rb") as stream:
        for b in iter(lambda:stream.read(1048576),b""):
            h.update(b);sha.update(b)
    if path.name!=EXPECTED_NAME or h.hexdigest()!=MD5:
        raise ValueError("Source version/name/checksum does not match frozen 2021")
    return {"md5":h.hexdigest(),"sha256":sha.hexdigest()}


def source_panels(rows):
    transformer=Transformer.from_crs("EPSG:4326","EPSG:32631",always_xy=True)
    first={}
    cnt={taxon:Counter() for taxon in TAXA}
    for r in rows:
        taxon=(r.get("individual-taxon-canonical-name") or "").strip()
        if taxon not in TAXA:continue
        c=cnt[taxon]
        c["raw_source_rows"]+=1
        if any((r.get(k) or "").strip().lower() in ("true","t","1","yes","y")
               for k in ("import-marked-outlier","manually-marked-outlier")):
            c["outliers"]+=1
            continue
        t=(r.get("timestamp") or "").strip()
        a=(r.get("individual-local-identifier") or "").strip()
        try:
            year,mo,hr,mi=int(t[:4]),int(t[5:7]),int(t[11:13]),int(t[14:16])
            lon,lat,speed=float(r["location-long"]),float(r["location-lat"]),float(r["ground-speed"])
        except (TypeError,ValueError,KeyError):
            continue
        if year!=2021 or mo not in (5,6,7) or not a:continue
        if not(0<=hr<24 and 0<=mi<60 and -180<=lon<=180 and -90<=lat<=90 and 0<=speed<=.5):
            continue
        if not all(math.isfinite(v) for v in (lon,lat,speed)):continue
        x,y=transformer.transform(lon,lat)
        if not(math.isfinite(x) and math.isfinite(y)):continue
        c["raw_stationary_proxy_events"]+=1
        cell=(math.floor(x/100),math.floor(y/100))
        key=(taxon,a,t[:10],hr*12+mi//5)
        if key not in first or t<first[key][0]:
            first[key]=(t,cell,r.get("height-above-msl",""))

    votes=defaultdict(Counter)
    for (taxon,bird,day,k),(_,cell,rawheight) in first.items():
        votes[taxon,bird,day][cell]+=1
    chosen={}
    for key,cells in votes.items():
        cell,n=sorted(cells.items(),key=lambda p:(-p[1],p[0]))[0]
        if n>=20:chosen[key]=cell

    selected=defaultdict(list)
    for (taxon,bird,day,k),(_,cell,rawheight) in first.items():
        key=(taxon,bird,day)
        if chosen.get(key)!=cell:continue
        selected[key].append(rawheight)
    panels={taxon:[] for taxon in TAXA}
    for taxon in TAXA:
        c=cnt[taxon]
        c["first_stationary_5minute_bins"]=sum(t==taxon for t,*_ in first)
        c["dominant_cell_bird_days_ge20"]=sum(t==taxon for t,*_ in chosen)
        c["selected_dominant_cell_bins"]=sum(len(v) for (t,bird,day),v in selected.items() if t==taxon)
        for (sp,bird,day),values in selected.items():
            if sp!=taxon:continue
            heights=[]
            for raw in values:
                try:z=float(raw)
                except (ValueError,TypeError):c["missing_height"]+=1;continue
                if not math.isfinite(z):c["missing_height"]+=1;continue
                if not -300<=z<=3000:c["bad_height"]+=1;continue
                heights.append(z)
                c["valid_height"]+=1
            if len(heights)<20:continue
            bins=np.searchsorted(EDGES,np.array(heights)-np.median(heights),side="right")-1
            hist=np.bincount(bins,minlength=10)
            if len(hist)!=10:raise AssertionError("Invalid fixed stationary height bins")
            panels[taxon].append({"animal":bird,"day":day,"hist":{chosen[sp,bird,day]:hist}})
        c["valid_day_sessions"]=len(panels[taxon])
    q={}
    for t in TAXA:
        v=dict(cnt[t])
        v["valid_fraction_modal_cells"]=(cnt[t]["valid_height"]/cnt[t]["selected_dominant_cell_bins"]) if cnt[t]["selected_dominant_cell_bins"] else 0.
        q[t]=v
    return panels,q


def serialize_summary(est):
    return {
        k:v for k,v in est.items()
        if k not in ("day_scored_bins","per_bird")
    }


def run_panel(sessions,quality,taxon,draws=DRAW_N):
    result={"taxon":taxon,"quality":quality,"terminal":"unavailable",
            "primary":"D1_balanced_at_100m_stationary_speed_le_0.5",
            "control_type":"post_outcome_instrument_or_perch_associated_identity",
            "excludes_true_stationarity_claim":True,"null_requested":draws}
    if quality["valid_fraction_modal_cells"] <.8 or not sessions:
        result["reason"]="native_height_quality_or_no_stationary_sessions";return result,[]
    x=engine.pack(sessions)
    pre=engine.support(x,1)
    obs=engine.evaluate(x,1,"balanced")
    if not np.array_equal(pre["day_scored_bins"],obs["day_scored_bins"]):
        raise AssertionError("Preflight/scorer use different support")
    result["observed"]=serialize_summary(obs)
    result["positive_bird_point_scores"]=sum(v["gain"]>0 for v in obs["per_bird"].values())
    if obs["eligible_birds"]<10:
        result["reason"]="minimum_ten_birds_for_comparator";return result,[]
    rng=np.random.default_rng(SEED)
    values=[];draw_metadata=[]
    for j in range(draws):
        labels=engine.permute_labels(x,rng)
        n,g=engine.kernel(x,1,labels,True)
        stat=engine.summarise(x,n,g[1],labels)
        accepted=(stat["eligible_birds"]>=10 and stat["mean_gain"] is not None and math.isfinite(stat["mean_gain"]))
        values.append(stat["mean_gain"] if accepted else None)
        draw_metadata.append({"draw":j+1,"eligible_birds":stat["eligible_birds"],
          "eligible_days":stat["eligible_days"],
          "gain":values[-1],
          "fraction_labels_changed":float(np.mean(labels!=x["labels"]))})
        if (j+1)%100==0:print(taxon,"stationary permutations",j+1,flush=True)
    cal=engine.calibrate(obs["mean_gain"],values,draws)
    result["calibration"]=cal
    result["null_support"]={
        "valid":cal["valid"],"requested":draws,
        "eligible_birds_min":min(z["eligible_birds"] for z in draw_metadata),
        "eligible_birds_max":max(z["eligible_birds"] for z in draw_metadata),
        "mean_fraction_labels_changed":float(np.mean([z["fraction_labels_changed"] for z in draw_metadata]))
    }
    if cal["valid"]<math.ceil(.95*draws) or result["null_support"]["mean_fraction_labels_changed"]<=0:
        result["reason"]="null_support_unavailable";return result,draw_metadata
    result["terminal"]="tested"
    result["upper_p"]=cal["p_upper"]
    return result,draw_metadata


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gps",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    ns=p.parse_args()
    ns.out.mkdir(parents=True,exist_ok=True)
    hashes=verify(ns.gps)
    with gzip.open(ns.gps,"rt",encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        cols=set(reader.fieldnames or [])
        required={"timestamp","individual-local-identifier","individual-taxon-canonical-name",
                  "location-long","location-lat","ground-speed","height-above-msl"}
        if not required<=cols:raise ValueError("Native columns unavailable")
        panels,quality=source_panels(reader)

    report={
        "study":"DELTATRACK_2021_STATIONARY_NEGATIVE_CONTROL_V1",
        "plan":"prospective/DELTATRACK_2021_STATIONARY_SHAPE_DIAGNOSTIC_PLAN_V1.json",
        "archive":"10.5281/zenodo.22102508","input_hashes":hashes,
        "flight_identity_retested":False,
        "scope":"post-outcome stationary negative control only; not a causal instrument test",
        "numerical_kernel_sha256":hashlib.sha256(Path(engine.__file__).read_bytes()).hexdigest(),
        "panels":{}
    }
    for taxon in TAXA:
        res,draws=run_panel(panels[taxon],quality[taxon],taxon,DRAW_N)
        report["panels"][taxon]=res
        if draws:
            with (ns.out/(taxon.replace(" ","_")+"_stationary_null.csv")).open("w",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=list(draws[0]))
                writer.writeheader();writer.writerows(draws)
    order=sorted(TAXA,key=lambda t:report["panels"][t].get("upper_p",1.0))
    running=0.
    for rank,taxon in enumerate(order):
        r=report["panels"][taxon]
        p=r.get("upper_p",1.0)
        running=max(running,min(1.0,(2-rank)*p))
        r["holm_upper_p"]=running
        if r["terminal"]=="tested":
            positive=r["calibration"]["observed_minus_valid_null_mean"]>0
            r["terminal"]="stationary_identity_present" if positive and running<.05 else "stationary_identity_not_supported"
    (ns.out/"STATIONARY_NEGATIVE_CONTROL_RESULT_V1.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({t:{"terminal":v["terminal"],"birds":v.get("observed",{}).get("eligible_birds"),
       "days":v.get("observed",{}).get("eligible_days"),
       "observed_gain":v.get("observed",{}).get("mean_gain"),
       "null_valid":v.get("calibration",{}).get("valid"),
       "holm_upper_p":v.get("holm_upper_p")}
       for t,v in report["panels"].items()},sort_keys=True))


if __name__=="__main__":
    main()
