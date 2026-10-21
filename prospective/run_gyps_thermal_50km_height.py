#!/usr/bin/env python3
"""One-shot Gyps 2026 source Wstar conditioned 50km height profile study test.

Cross-check the exact previous pre-height reference BEFORE reading numeric
native heights. No study/species/year/cell threshold is outcome-selected.
"""
from __future__ import annotations

import argparse,csv,gzip,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np

from .scacco_point_xy_thermal_support import (
  selected_points,summarize,PROJECTOR,finite
)
from .gyps_thermal_height_kernel import (
  HEIGHT_EDGES,pack_profiles,score,permute_day_states,calibrate
)

PANEL_SPECS={
  ("122120597","Gyps fulvus"):{"points":220988,"birds":25,"sha":"641e9c766867a641c70c7210d37a3a514c35b79d1e57d592d5c4a40b512b8cc2"},
  ("352166254","Gyps africanus"):{"points":126543,"birds":11,"sha":"a77803e14681c30d8094c603b832d7d24801d6eb31bf5abfa6be40d079b3ba36"},
  ("44080734","Gyps fulvus"):{"points":295889,"birds":26,"sha":"9402923502706e60aa5a207d5df28840a97fc3b98975d2b9af95e64306264001"},
  ("972560688","Gyps coprotheres"):{"points":164126,"birds":14,"sha":"5148de3f1d25aef1fc5cadcb2bf1fe776cd4c9c54fa8239864a1a69b67373559"},
}
FIXED_CANDIDATES=4
ARCHIVE_MD5="e1f116e6576cf20e54dad16d2c91a26d"
PREHEIGHT_RUN=39545718549
SEED=20261021
N_PERM=999
MIN_VALID_PERM=950
MIN_BIRDS=10
ALT_LO,ALT_HI=-500.,7000.


def md5_file(path):
    m=hashlib.md5()
    with path.open("rb") as f:
        for data in iter(lambda:f.read(1048576),b""):
            m.update(data)
    return m.hexdigest()


def validate_preheight(metadata_earliest,original_ids,receipt):
    if receipt["numerical_altitude_values_accessed_for_screen"] is not False:
        raise ValueError("Original source 4-study roster was not altitude-blind")
    if receipt["source_study_species_panels"]!=72:
        raise ValueError("Source panel universe was changed after freeze")
    candidates=summarize(metadata_earliest,Counter(),original_ids)["catalog_panels"]
    eligible={}
    for item in candidates:
        key=(item["study_id"],item["species"])
        if key not in PANEL_SPECS:
            raise ValueError("Unexpected native source study selected: "+repr(key))
        spec=PANEL_SPECS[key]
        st=item["thermal_50000"]
        if (item["source_5min_point_fixes"]!=spec["points"] or
            st["birds_with_two_qualifying_low_and_high_days"]!=spec["birds"] or
            st["bird_id_fingerprint"]!=spec["sha"] or
            not st["context_screen_admitted"]):
            raise ValueError("Pre-outcome study×species climate/XY roster fingerprint changed: "+repr(key))
        old=next((p for p in receipt["catalog_panels"]
                if p["study_id"]==key[0] and p["species"]==key[1]),None)
        if old is None or old["thermal_50000"]!=st:
            raise ValueError("Previously recorded climate regime thresholds/roster differ")
        for fld in ("flap_probability","thermal_uplift"):
            if old["environment_completeness"][fld]<.8:
                raise ValueError("Source predictor incompleteness invalidates fixed source")
        eligible[key]=item
    if set(eligible)!=set(PANEL_SPECS):
        raise ValueError("A frozen Gyps source study is missing")
    return eligible


def wind_states_from_selected(meta,preheight):
    # EXACT SAME source state definition as the saved point-wise no-height
    # analyzer: median source point-wise Wstar per bird-day; Q25/Q75 within
    # native study × species × year-month across days with >=20 finite Wstar.
    by_panel_day=defaultdict(lambda:defaultdict(list))
    for (source,study,species,bird,day,bin5),info in meta.items():
        w=info[3]
        if w is not None and w>=0:
            by_panel_day[(study,species)][bird,day].append(w)
    result={}
    for panel,days in by_panel_day.items():
        prior=preheight[panel]["thermal_50000"]
        thresholds=prior["thresholds_by_month"]
        states={}
        for (bird,day),values in days.items():
            if len(values)<20:continue
            q=thresholds.get(day[:7])
            if q is None:continue
            w=float(np.median(values))
            state=0 if w<=q[0] else (1 if w>=q[1] else -1)
            states[bird,day]=state
        result[panel]=states
    return result


def original_metadata_source(path):
    with gzip.open(path,"rt",encoding="utf-8-sig",newline="") as f:
        header=set(csv.DictReader(f,delimiter="\t").fieldnames or ())
    required={
      "study_id","study_name","species","animal_id","timestamp",
      "lon","lat","segment_id","data_source","tag_id","height",
      "thermal_uplift","flap_probability"
    }
    if not required<=header:
        raise ValueError("Extracted Gyps source does not contain all expected columns")
    # First pass is source admission / Wstar without ANY numeric height.
    with gzip.open(path,"rt",encoding="utf-8-sig",newline="") as f:
        meta,counts,original_ids=selected_points(csv.DictReader(f,delimiter="\t"))
    return meta,original_ids,counts


def selected_native_height(path,meta):
    expected={key:info[0] for key,info in meta.items()}
    chosen={}
    selected_tag=defaultdict(set)
    native_provenance=defaultdict(Counter)
    with gzip.open(path,"rt",encoding="utf-8-sig",newline="") as f:
        for record in csv.DictReader(f,delimiter="\t"):
            bird=(record.get("animal_id") or "").strip()
            study=(record.get("study_id") or "").strip()
            species=(record.get("species") or "").strip()
            stamp=(record.get("timestamp") or "").strip()
            if len(stamp)<16:continue
            try:
                hour,minute=int(stamp[11:13]),int(stamp[14:16])
            except (ValueError,TypeError):continue
            key=("Movebank",study,species,bird,stamp[:10],
                 hour*12+minute//5)
            if key not in expected or expected[key]!=stamp or key in chosen:
                continue
            tag=(record.get("tag_id") or "").strip()
            if tag and tag.upper() not in {"NA","NAN","NULL","NONE"}:
                selected_tag[(study,species,bird)].add(tag)
            # Historic 38-species point-wise product harmonizes GPS native
            # ellipsoid and MSL heights; do not infer AGL from this height.
            native_provenance[study,species]["native_ellipsoid_nonmissing"]+=(
                finite(record.get("height.above.ellipsoid")) is not None)
            native_provenance[study,species]["native_msl_nonmissing"]+=(
                finite(record.get("height.above.msl")) is not None)
            chosen[key]=finite(record.get("height"))
    if set(chosen)!=set(expected):
        raise ValueError("Native height source no longer corresponds to earliest selected metadata GPS rows")
    return chosen,selected_tag,native_provenance


def make_study_profiles(panel,meta,height,labels,tags,provenance):
    study,species=panel
    # QC is fixed over ALL original earliest GPS fixes, even those in middle
    # Wstar states. Never rescue by dropping incomplete bird-days.
    cohort=[
       (key,info,height[key]) for key,info in meta.items()
       if key[1]==study and key[2]==species
    ]
    valid=[(key,info,z) for key,info,z in cohort
           if z is not None and ALT_LO<=z<=ALT_HI]
    fraction=len(valid)/len(cohort) if cohort else 0.
    quality={
      "source_first_five_minute_bins":len(cohort),
      "native_height_valid":len(valid),
      "native_height_missing_nonfinite":sum(z is None for k,info,z in cohort),
      "native_height_outside_bounds":len(cohort)-len(valid)-sum(z is None for k,info,z in cohort),
      "height_valid_fraction":fraction,
      "height_unit":"native harmonized height_gener, ellipsoid or MSL, not AGL",
      "vertical_provenance":dict(provenance.get(panel,{})),
      "birds_with_two_native_tag_ids":sum(
         len(tags.get((study,species,bird),set()))>=2
         for bird in {key[3] for key,info,z in cohort}
      ),
      "n_birds_source":len({key[3] for key,info,z in cohort}),
    }
    if fraction<.8:
        return None,quality

    # Center each UTC bird-day after native height QC across ALL visited
    # 50km cells, including middle Wstar days. This is an OFFLINE
    # distribution-shape comparison, not an absolute-height forecast.
    by_birdday=defaultdict(list)
    for key,info,z in valid:
        source,st,sp,bird,day,bin5=key
        _,lon,lat,*climate=info
        x,y=PROJECTOR.transform(lon,lat)
        if not(math.isfinite(x) and math.isfinite(y)):
            raise ValueError("Original valid GPS becomes invalid under global equal-area projection")
        cell=(math.floor(x/50000),math.floor(y/50000))
        by_birdday[bird,day].append((cell,z))
    sessions=[]
    for (bird,day),vals in sorted(by_birdday.items()):
        alt=np.asarray([z for cell,z in vals],dtype=np.float64)
        bs=np.searchsorted(HEIGHT_EDGES,alt-np.median(alt),side="right")-1
        if np.any((bs<0)|(bs>9)):
            raise AssertionError("Frozen source altitude bins invalid")
        h=defaultdict(lambda:np.zeros(10,dtype=np.int64))
        for (cell,z),k in zip(vals,bs):
            h[cell][int(k)]+=1
        sessions.append({"bird":bird,"day":day,"hists":dict(h)})
    quality["height_valid_sessions"]=len(sessions)
    return sessions,quality


def fixed_four_panel_holm(result):
    members=sorted(PANEL_SPECS)
    order=sorted(members,key=lambda key:result[key].get("p_upper",1.))
    running=0.
    for idx,panel in enumerate(order):
        row=result[panel]
        p=row.get("p_upper",1.)
        running=max(running,min(1.,p*(len(members)-idx)))
        row["holm_p_upper"]=running
        if row["terminal"]!="unavailable":
            good=(row["calibration"]["observed_minus_null_mean"] is not None and
                  row["calibration"]["observed_minus_null_mean"]>0 and running<.05)
            row["terminal"]="supported_50km_thermal_height_shape" if good else "not_supported_50km_thermal_height_shape"
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-extract",type=Path,required=True)
    parser.add_argument("--preheight-result",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    prior=json.loads(args.preheight_result.read_text())
    args.out.mkdir(parents=True,exist_ok=True)
    meta,ids,counts=original_metadata_source(args.full_extract)
    frozen=validate_preheight(meta,ids,prior)
    windstates=wind_states_from_selected(meta,frozen)
    # Native altitude parsing is allowed ONLY from here after the exact
    # independent 4-study, 76-bird source roster was accepted.
    height,tags,provenance=selected_native_height(args.full_extract,meta)
    candidates={}
    all_draws={}
    for study,species in sorted(PANEL_SPECS):
        panel=(study,species)
        sessions,quality=make_study_profiles(panel,meta,height,
                                              windstates.get(panel,{}),tags,provenance)
        row={
          "panel":f"{study}/{species}",
          "study_id":study,"species":species,
          "source_height_quality":quality,
          "preheight_source_birds":PANEL_SPECS[panel]["birds"],
          "preheight_roster_hash":PANEL_SPECS[panel]["sha"],
          "terminal":"unavailable",
          "reason":None,
          "primary":"within-bird, within-50km, across-day Wstar-conditioned vs Wstar-pooled centered GPS altitude-bin prediction"
        }
        if sessions is None:
            row["reason"]="frozen_source_native_height_quality_gate"
            candidates[panel]=row
            continue
        pack=pack_profiles(sessions,windstates.get(panel,{}))
        original=score(pack)
        row["observed"]=original
        if original["eligible_birds"]<MIN_BIRDS:
            row["reason"]="fixed_minimum_ten_birds_not_met_after_height_QC"
            candidates[panel]=row
            continue
        rng=np.random.default_rng(SEED)
        draws=[]
        for i in range(N_PERM):
            randomized=permute_day_states(pack,rng)
            q=score(pack,randomized)
            valid=(q["eligible_birds"]>=MIN_BIRDS and q["mean_gain"] is not None)
            draws.append({
               "draw":i+1,
               "mean_gain":q["mean_gain"] if valid else None,
               "eligible_birds":q["eligible_birds"],
               "eligible_bird_days":q["eligible_bird_days"],
               "scored_fixes":q["scored_fixes"]
            })
            if (i+1)%200==0:
                print(study,species,"permutations",i+1,flush=True)
        calibration=calibrate(original,draws)
        row["calibration"]=calibration
        row["p_upper"]=calibration["p_upper"]
        if calibration["valid"]<MIN_VALID_PERM:
            row["reason"]="frozen_950_valid_permutation_gate"
        else:
            row["terminal"]="tested_prior_to_Holm_adjustment"
            row["reason"]=None
        candidates[panel]=row
        all_draws[panel]=draws

    fixed_four_panel_holm(candidates)
    summary={
        "analysis":"GYPS_3SPECIES_4STUDIES_50KM_THERMAL_CONTEXT_V1",
        "record_doi":"10.5281/zenodo.21915776",
        "source_archive_md5":ARCHIVE_MD5,
        "preheight_run":PREHEIGHT_RUN,
        "fixed_study_species_panels":4,
        "frozen_height_bins_m":[None,-200,-100,-50,-25,0,25,50,100,200,None],
        "source_records_meta_5min":counts["selected_5min_unique_fixes"],
        "year_source_universe": "2007-2024 preselected commuting flight segments",
        "randomizations_per_panel_requested":N_PERM,
        "seed_each_panel":SEED,
        "original_scacco_cost_of_transport_not_retested":True,
        "p_value_adjustment":"Holm across all four fixed study×species outcomes, unavailable p=1",
        "panels":{f"{st}/{species}":candidates[st,species]
                  for st,species in sorted(PANEL_SPECS)},
        "source_species_supported":sorted({sp for (st,sp),r in candidates.items()
              if r["terminal"]=="supported_50km_thermal_height_shape"}),
        "source_level_scientific_boundary":[
           "All panels are Gyps vultures, not broad bat/bird biological universality.",
           "ERA5 Wstar can encode geographic route and common seasonal weather conditions; observational source association is not causal uplift.",
           "Positive gain need not imply individual-specific reaction norms. A shared wind response can improve per-individual context-conditioned distributions.",
           "50km source corridor grain cannot be interpreted as the 5km original bat/gull spatial estimator.",
           "Mixed GPS ellipsoid/MSL source instrument altitudes cannot be pooled as absolute heights; median centering removes only additive shifts.",
           "GPS device error and within-50km topography, flock movement, and prior source selection are not causally separated.",
           "The 999 randomizations shuffle bird-month regimes and do not preserve day-level weather correlations across all birds."
        ]
    }
    (args.out/"GYPS_50KM_WSTAR_VERTICAL_SHAPE_RESULT_V1.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    )
    for (st,sp),ds in all_draws.items():
        with (args.out/(f"{st}_{sp.replace(' ','_')}_WSTAR_NULL.csv")).open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(ds[0]))
            writer.writeheader();writer.writerows(ds)
    print(json.dumps({
         "study_results":{key:{
             "terminal":v["terminal"],
             "n_birds":v.get("observed",{}).get("eligible_birds"),
             "n_bird_days":v.get("observed",{}).get("eligible_bird_days"),
             "n_fixes":v.get("observed",{}).get("scored_fixes"),
             "gain":v.get("observed",{}).get("mean_gain"),
             "null_valid":v.get("calibration",{}).get("valid"),
             "null_excess":v.get("calibration",{}).get("observed_minus_null_mean"),
             "p_holm_upper":v.get("holm_p_upper")
         } for key,v in summary["panels"].items()},
         "supported_species":summary["source_species_supported"]
     },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
