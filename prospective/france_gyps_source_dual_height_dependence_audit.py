#!/usr/bin/env python3
"""Source-pinned, POST-OUTCOME French Gyps two-height measurement audit.

Only reads the previously archived GitHub Actions ZIP's summary JSON and
two immutable 999-null CSV files. Never opens original native GPS heights or
changes birds, years, tag IDs, horizontal cell, age, or D1 null rules.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,zipfile
from collections import defaultdict
from pathlib import Path
import numpy as np

ZIP_SHA="4e73b15038ba45e025f21a2b1bd951d3f063b8dc4148bed8bbdd9473f07f4864"
RESULT="FRANCE_GYPS_2019_2021_GPS_BARO_DUAL_HEIGHT_RESULT_V1.json"
RESULT_SHA="02fb090bfb94343a6635f2f0ca5d12bf734fbde1ee9422b18fe57bbde19d2b7d"
NULL_FILES={
 "GPS":("GPS_native_height_D1_day_null.csv","a8919aedaef1bb1dcb01b98a5bbcc2946e58a48183e1352d195492819d6328e1"),
 "BAROMETRIC":("BAROMETRIC_native_height_D1_day_null.csv","c6bbf5cd47608712ded599d63df522cedc71f02476d6139627013faa81194e09")}
BOOT=5000
SEED=20261024

def checksum(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):h.update(part)
    return h.hexdigest()

def rank_average(values):
    x=np.asarray(values,float)
    order=np.argsort(x,kind="mergesort")
    ranks=np.zeros(len(x),float)
    i=0
    while i<len(x):
        j=i+1
        while j<len(x) and x[order[j]]==x[order[i]]:j+=1
        ranks[order[i:j]]=(i+1+j)/2
        i=j
    return ranks

def rho(x,y):
    if len(x)!=len(y) or len(x)<3:return None
    a,b=rank_average(x),rank_average(y)
    if not a.std() or not b.std():return None
    return float(np.corrcoef(a,b)[0,1])

def interval(x):
    return [float(v) for v in np.quantile(np.asarray(x,dtype=float),[.025,.975])]

def summarize(result):
    if result["terminal"]!="paired_sensor_robust_individual_height_shape":
        raise ValueError("Historical result not native paired positive")
    if result["native_sensor_independence_proven"] is not False:
        raise ValueError("Historical device independence source boundary changed")
    sensors=result["sensor_results"]
    if set(sensors)!={"GPS","BAROMETRIC"}:raise ValueError("Unexpected sensor outcome family")
    gp=sensors["GPS"]["observed"]["per_bird"]
    bp=sensors["BAROMETRIC"]["observed"]["per_bird"]
    if set(gp)!=set(bp) or len(gp)!=27:
        raise ValueError("Same original 27 birds must be scored in both sensors")
    ids=sorted(gp)
    if any(gp[k]["days"]!=bp[k]["days"] or gp[k]["bins"]!=bp[k]["bins"] for k in ids):
        raise ValueError("One height modality scored a different bird/day/fix set")
    x=np.asarray([gp[k]["gain"] for k in ids],float)
    y=np.asarray([bp[k]["gain"] for k in ids],float)
    days=result["source_altitude_quality"]["per_day_sensor_agreement_descriptive"]
    if len(days)!=5854 or len({r["bird"] for r in days})!=28:
        raise ValueError("Historical paired source bird-days changed")
    perbird=defaultdict(list);peryear=defaultdict(list)
    for r in days:
        perbird[r["bird"]].append(r)
        peryear[r["day"][:4]].append(r)
    corr=np.asarray([r["GPS_and_baro_same_fix_pearson"] for r in days
                     if r["GPS_and_baro_same_fix_pearson"] is not None],float)
    delta=np.asarray([r["GPS_and_baro_centered_median_abs_difference_m"] for r in days],float)
    hdop=np.asarray([r["median_hdop_when_both"] for r in days],float)
    med_corr=np.asarray([np.median([r["GPS_and_baro_same_fix_pearson"] for r in perbird[k]
                                   if r["GPS_and_baro_same_fix_pearson"] is not None])
                         for k in sorted(perbird)],float)
    med_delta=np.asarray([np.median([r["GPS_and_baro_centered_median_abs_difference_m"] for r in perbird[k]])
                           for k in sorted(perbird)],float)
    rng=np.random.default_rng(SEED)
    gains_corr=[];mean_gain_diff=[];med_c=[];med_d=[]
    for iteration in range(BOOT):
        s=rng.integers(0,len(x),len(x))
        rc=rho(x[s],y[s])
        if rc is not None:gains_corr.append(rc)
        mean_gain_diff.append(float(np.mean((x-y)[s])))
        ss=rng.integers(0,len(med_corr),len(med_corr))
        med_c.append(float(np.median(med_corr[ss])))
        med_d.append(float(np.median(med_delta[ss])))
    return {
      "source_birds_paired":28,"scored_birds_both":27,
      "source_bird_days_paired":len(days),
      "bird_day_Pearson_available":len(corr),
      "bird_day_Pearson_unavailable":len(days)-len(corr),
      "bird_day_centered_GPS_baro_Pearson_median":float(np.median(corr)),
      "bird_equal_median_of_bird_day_Pearson_medians":float(np.median(med_corr)),
      "bird_bootstrap95_bird_equal_Pearson_median":interval(med_c),
      "bird_day_median_absolute_centered_GPS_baro_delta_m_median":float(np.median(delta)),
      "bird_equal_median_of_centered_absolute_delta_medians_m":float(np.median(med_delta)),
      "bird_bootstrap95_bird_equal_median_centered_height_delta_m":interval(med_d),
      "GPS_positive_birds":int(np.sum(x>0)),"BARO_positive_birds":int(np.sum(y>0)),
      "positive_both":int(np.sum((x>0)&(y>0))),
      "nonpositive_both":int(np.sum((x<=0)&(y<=0))),
      "bird_level_GPS_vs_BARO_gain_pearson":float(np.corrcoef(x,y)[0,1]),
      "bird_level_GPS_vs_BARO_gain_spearman":rho(x,y),
      "bird_bootstrap95_bird_gain_spearman":interval(gains_corr),
      "GPS_vs_BARO_mean_gain_diff_nats_per_record":float(np.mean(x-y)),
      "bird_bootstrap95_mean_gain_difference_nats":interval(mean_gain_diff),
      "bird_level_median_absolute_gain_difference_nats":float(np.median(abs(x-y))),
      "bird_day_HDOP_vs_height_sensor_disagreement_spearman_descriptive":rho(hdop,delta),
      "year_specific_descriptive":{
        year:{"bird_days":len(group),
              "median_day_Pearson":float(np.median([r["GPS_and_baro_same_fix_pearson"] for r in group
                                                     if r["GPS_and_baro_same_fix_pearson"] is not None])),
              "median_day_centered_absolute_difference_m":float(np.median(
                 [r["GPS_and_baro_centered_median_abs_difference_m"] for r in group]))}
        for year,group in sorted(peryear.items())
      },
      "source_representations_physically_independent":False,
      "source_same_birds_same_tags_same_GPS_fix_set":True
    }

def validate_original_nulls(source_zip,original):
    out={}
    for sensor,(filename,expected_sha) in NULL_FILES.items():
        data=source_zip.read(filename)
        if hashlib.sha256(data).hexdigest()!=expected_sha:
            raise ValueError("Original immutable source null distribution changed")
        values=[]
        for r in csv.DictReader(io.StringIO(data.decode("utf-8"))):
            val=(r.get("gain") or "").strip()
            if val:values.append(float(val))
        if len(values)!=999:raise ValueError("Source valid shuffles must remain 999")
        original_result=original["sensor_results"][sensor]
        gain=float(original_result["observed"]["mean_gain"])
        p=(1+sum(v>=gain-1e-14 for v in values))/1000
        if not np.isclose(p*2,original_result["holm_p_upper"]):
            raise ValueError("Independent recalculation disagrees with Holm/source conclusion")
        out[sensor]={
            "n_valid_99null":999,
            "raw_score":gain,
            "null_mean":float(np.mean(values)),
            "observed_minus_null_mean":float(gain-np.mean(values)),
            "p_unadjusted":p,
            "p_Holm_2_modality":float(original_result["holm_p_upper"])
        }
    return out

def audit(path):
    if checksum(path)!=ZIP_SHA:raise ValueError("Original artifact ZIP SHA changed")
    with zipfile.ZipFile(path) as z:
        data=z.read(RESULT)
        if hashlib.sha256(data).hexdigest()!=RESULT_SHA:
            raise ValueError("Original JSON content hash changed")
        original=json.loads(data)
        s=summarize(original)
        nulls=validate_original_nulls(z,original)
    return {
      "analysis":"FRENCH_GYPS_NATIVE_TWO_HEIGHT_MEASUREMENT_DEPENDENCE_POSTOUTCOME_V1",
      "mode":"POST_OUTCOME_SOURCE_QUALITY_ONLY",
      "date":"2026-10-24",
      "source_DOI":"10.48579/PRO/IOSZNM",
      "original_GitHub_run":39716885648,
      "original_artifact_id":12399538915,
      "original_artifact_sha256":ZIP_SHA,
      "source_native_height_outcomes_recomputed":False,
      "source_original_sample_and_999_nulls_changed":False,
      "species":"Gyps fulvus",
      "agreement":s,
      "verified_original_nulls":nulls,
      "biological_interpretation":{
        "supported":"Two distinctly varying numerical height series yield remarkably concordant individual-ID signal on identical native GPS fixes.",
        "not_supported":[
          "Two biological replications or two independent tag deployments (both heights attach to same bird/tag/UTC fixes).",
          "Barometric altitude calibration is independent of GPS height or meteorological reference (device manufacturer pipeline not documented in archived source).",
          "Intrinsic individual behavioural altitude specialization independent of tag, fine horizontal terrain and shared time/flight-mode mixture.",
          "Causal bird-specific thermal/wind reaction or universal flight law."
        ],
        "quality_bound":"Median per-bird-day Pearson and within-day centered absolute discrepancy are descriptive measurement diagnostics; cannot act as test of true sensor error against externally known height.",
        "further_experiment":"Independently calibrate both measurements at geodetic known-height stationary locations; test exact fine-route, flight-state and external atmosphere matching in an unused study."
      }
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=audit(a.original_zip)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    s=result["agreement"]
    print(json.dumps({
       "scored_birds":s["scored_birds_both"],
       "positive_in_both":s["positive_both"],
       "gain_spearman":s["bird_level_GPS_vs_BARO_gain_spearman"],
       "median_same_bird_day_Pearson":s["bird_day_centered_GPS_baro_Pearson_median"],
       "median_day_centered_height_disagreement_m":s["bird_day_median_absolute_centered_GPS_baro_delta_m_median"],
       "physical_independence_confirmed":False,
    },sort_keys=True))

if __name__=="__main__":
    main()
