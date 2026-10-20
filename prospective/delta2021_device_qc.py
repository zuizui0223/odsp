#!/usr/bin/env python3
"""Post-outcome DELTATRACK 2021 measurement-channel / tag-identity audit.

No individual-versus-other altitude model, permutation, or ecological inference.
Preserves the frozen event-selection semantics used in the external 2021 test.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

TAXA=("Larus argentatus","Larus fuscus")
GPS_FILE="DELTATRACK-gps-2021.csv.gz"
EXPECTED_MD5="1a3145234cccd1a48b280b0fb485d679"
REF_FILE="DELTATRACK-reference-data.csv"
REF_MD5="f1dd2f8966b3748a24165b989c10095d"
QUALITY_FIELDS=("gps:hdop","gps:satellite-count","gps-time-to-fix")


def maybe_number(raw):
    try:
        number=float(raw)
    except (ValueError,TypeError):
        return None
    return number if math.isfinite(number) else None


def check_md5(path: Path, expected: str):
    md5=hashlib.md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1<<20),b""):
            md5.update(chunk)
    if md5.hexdigest()!=expected:
        raise ValueError(f"Checksum mismatch: {path.name}")
    return md5.hexdigest()


def qc_percentiles(values: list[float], n_total: int) -> dict:
    s=sorted(values)
    def quantile(q):
        if not s:return None
        at=q*(len(s)-1)
        lower=math.floor(at);upper=math.ceil(at)
        return float(s[lower]+(s[upper]-s[lower])*(at-lower))
    return {
        "count_finite":len(s), "n_total":n_total,
        "finite_fraction":len(s)/n_total if n_total else None,
        "p10":quantile(.1),"p50":quantile(.5),"p90":quantile(.9)
    }


def inspect_rows(rows) -> dict:
    first={},{}
    first_flight={}
    first_stationary={}
    counted={t:Counter() for t in TAXA}
    for r in rows:
        taxon=(r.get("individual-taxon-canonical-name") or "").strip()
        if taxon not in TAXA:continue
        c=counted[taxon]
        c["raw_rows"]+=1
        if any((r.get(k) or "").strip().lower() in ("true","t","1","yes","y")
               for k in ("import-marked-outlier","manually-marked-outlier")):
            c["outlier_rows"]+=1
            continue
        t=(r.get("timestamp") or "").strip()
        animal=(r.get("individual-local-identifier") or "").strip()
        try:
            year,month,hour,minute=int(t[:4]),int(t[5:7]),int(t[11:13]),int(t[14:16])
        except (TypeError,ValueError):
            c["bad_timestamp"]+=1
            continue
        if year!=2021 or month not in (5,6,7) or not animal:continue
        if not (0<=hour<24 and 0<=minute<60):continue
        lon=maybe_number(r.get("location-long"));lat=maybe_number(r.get("location-lat"))
        sp=maybe_number(r.get("ground-speed"))
        if lon is None or lat is None or sp is None or not(-180<=lon<=180 and -90<=lat<=90):
            c["invalid_xyspeed"]+=1
            continue
        day=t[:10]
        key=(taxon,animal,day,hour*12+minute//5)
        tag=(r.get("tag-local-identifier") or "").strip()
        meta={
            "tag":tag,"day":day,
            "height":r.get("height-above-msl"),"bar":r.get("bar:barometric-height"),
            **{k:r.get(k) for k in QUALITY_FIELDS},
        }
        if 5<=sp<=55:
            c["raw_flight_proxy_events"]+=1
            prev=first_flight.get(key)
            if prev is None or t<prev[0]:first_flight[key]=(t,meta)
        if 0<=sp<=.5:
            c["raw_stationary_proxy_events"]+=1
            prev=first_stationary.get(key)
            if prev is None or t<prev[0]:first_stationary[key]=(t,meta)

    panels={}
    for taxon in TAXA:
        flight=[(a,d,meta) for (t,a,d,bin5),(stamp,meta) in first_flight.items() if t==taxon]
        still=[(a,d,meta) for (t,a,d,bin5),(stamp,meta) in first_stationary.items() if t==taxon]
        bird_tags=defaultdict(set);tag_birds=defaultdict(set);tag_days=defaultdict(set)
        bird_days=defaultdict(set)
        unknown_tag_birds=set()
        valid_gps=0;missing_gps=0;out_of_bounds=0
        bar_all=[];paired=[];bar_nonzero=0
        bird_paired_days=Counter();bird_day_pair_value=defaultdict(set)
        gps_values={field:[] for field in QUALITY_FIELDS}
        tag_hdop_coverage=Counter();tag_hdop_finite=Counter()
        for bird,day,meta in flight:
            tag=meta["tag"]
            bird_days[bird].add(day)
            if tag:
                bird_tags[bird].add(tag)
                tag_birds[tag].add(bird)
                tag_days[bird,tag].add(day)
            else:unknown_tag_birds.add(bird)
            gps=maybe_number(meta["height"])
            if gps is None:missing_gps+=1
            elif not -300<=gps<=3000:out_of_bounds+=1
            else:valid_gps+=1
            bar=maybe_number(meta["bar"])
            if bar is not None:bar_all.append(bar)
            if gps is not None and -300<=gps<=3000 and bar is not None:
                paired.append(bar)
                if bar!=0:bar_nonzero+=1
                bird_paired_days[bird,day]+=1
                bird_day_pair_value[bird].add(bar)
            for field in QUALITY_FIELDS:
                number=maybe_number(meta[field])
                if number is not None:gps_values[field].append(number)
            if tag:
                tag_hdop_coverage[tag]+=1
                if maybe_number(meta["gps:hdop"]) is not None:tag_hdop_finite[tag]+=1

        cross_tag=sum(sum(len(tag_days[bird,tag])>=2 for tag in tags)>=2 for bird,tags in bird_tags.items())
        paired_days=Counter()
        for (bird,day),n in bird_paired_days.items():
            if n>=50:paired_days[bird]+=1
        paired_birds=sum(n>=2 for n in paired_days.values())
        bird_still_days=Counter()
        stationary_by_bird_day=Counter((bird,day) for bird,day,meta in still)
        for (bird,day),n in stationary_by_bird_day.items():
            if n>=20:bird_still_days[bird]+=1
        tag_coverage=[
            tag_hdop_finite[tag]/n
            for tag,n in tag_hdop_coverage.items() if n>=50
        ]

        panels[taxon]={
            "flight":{
                "raw_proxy_events":int(counted[taxon]["raw_flight_proxy_events"]),
                "first_5min_bins":len(flight),
                "distinct_birds":len(bird_days),
                "bird_days":sum(len(v) for v in bird_days.values()),
                "valid_gps_height_bins":valid_gps,
                "missing_gps_height_bins":missing_gps,
                "out_of_bounds_gps_height_bins":out_of_bounds,
            },
            "device":{
                "birds_with_tag_id":len(bird_tags),
                "tags":len(tag_birds),
                "birds_with_unknown_tag":len(unknown_tag_birds),
                "birds_with_two_tags":sum(len(v)>=2 for v in bird_tags.values()),
                "tags_shared_by_birds":sum(len(v)>=2 for v in tag_birds.values()),
                "cross_tag_repeated_birds":cross_tag,
                "separable_within_year":cross_tag>0,
                "population_tag_bird_effects_identified":False,
            },
            "barometer":{
                "all_flight_finite_bins":len(bar_all),
                "paired_valid_gps_bins":valid_gps,
                "finite_paired_bins":len(paired),
                "nonzero_paired_bins":bar_nonzero,
                "distinct_values_at_most_1000":len(set(paired)) if len(set(paired))<1000 else 1000,
                "paired_fraction":len(paired)/valid_gps if valid_gps else None,
                "paired_birds_with_two_50bin_days":paired_birds,
                "paired_birds_with_variable_height":sum(
                    len(vals)>=2 for vals in bird_day_pair_value.values()
                ),
                "channel_candidate":bool(
                    valid_gps>0 and len(paired)/valid_gps >=.8
                    and paired_birds>=10
                    and sum(len(vals)>=2 for vals in bird_day_pair_value.values())>=10
                    and len(set(paired))>1
                ),
            },
            "gps_quality":{
                **{field:qc_percentiles(vals,len(flight)) for field,vals in gps_values.items()},
                "tags_ge50_fixes":len(tag_coverage),
                "hdop_finite_rate_min_by_tag_ge50":min(tag_coverage) if tag_coverage else None,
                "hdop_finite_rate_max_by_tag_ge50":max(tag_coverage) if tag_coverage else None,
            },
            "stationary":{
                "first_5min_bins":len(still),
                "birds_with_any_still_fixes":len({bird for bird,day,meta in still}),
                "bird_days_at_least_20_bins":sum(n>=20 for n in stationary_by_bird_day.values()),
                "birds_with_two_still_days_ge20":sum(n>=2 for n in bird_still_days.values()),
                "source_only_speed_proxy_not_confirmed_stationarity":True,
            }
        }
    return {
        "status":"POST_OUTCOME_TAG_AND_MEASUREMENT_QC_NO_IDENTITY_TEST",
        "panels":panels,
        "frozen_source_file":GPS_FILE,
        "altitude_individual_identity_not_rescored":True,
        "permutations_run":0,
        "opened_measurement_quality_only":True,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gps",type=Path,required=True)
    parser.add_argument("--reference",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.gps.name!=GPS_FILE or args.reference.name!=REF_FILE:
        raise ValueError("Source name mismatch")
    gps_md5=check_md5(args.gps,EXPECTED_MD5)
    reference_md5=check_md5(args.reference,REF_MD5)
    with gzip.open(args.gps,"rt",encoding="utf-8-sig",newline="") as fp:
        reader=csv.DictReader(fp)
        required={
            "timestamp","individual-local-identifier","individual-taxon-canonical-name",
            "location-long","location-lat","ground-speed","height-above-msl"
        }
        if not required<=set(reader.fieldnames or ()):
            raise ValueError("Missing required frozen GPS fields")
        result=inspect_rows(reader)
        result["native_fields_present"]={k:k in set(reader.fieldnames or ()) for k in
             ["tag-local-identifier","bar:barometric-height",*QUALITY_FIELDS]}
    result["gps_md5"]=gps_md5
    result["reference_md5"]=reference_md5
    result["audit_contract"]="prospective/DELTATRACK_2021_DEVICE_IDENTIFIABILITY_CONTRACT_V1.json"
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary={t:{"birds":o["flight"]["distinct_birds"],"tags":o["device"]["tags"],
                 "cross_tag_birds":o["device"]["cross_tag_repeated_birds"],
                 "bar_candidate":o["barometer"]["channel_candidate"],
                 "bar_paired":o["barometer"]["finite_paired_bins"],
                 "hdop_fraction":o["gps_quality"]["gps:hdop"]["finite_fraction"],
                 "still_days":o["stationary"]["bird_days_at_least_20_bins"]}
             for t,o in result["panels"].items()}
    print(json.dumps(summary,sort_keys=True))


if __name__=="__main__":
    main()
