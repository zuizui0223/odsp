#!/usr/bin/env python3
"""Frozen Swiss red-kite source-identity + GPS eligibility, WITHOUT outcomes.

Full provider GPS bytes are streamed solely to verify MD5, parse in-memory
year-ID, bird-ID, timestamp and geographic conditions and count season groups.
The mixed-response metadata CSV is handled by the already frozen prefix-only
scanner: reproductive responses are NEVER decoded. No raw identifiers,
coordinates, timestamps, individual histories, or model scores are exported.
"""
from __future__ import annotations

import argparse
import calendar
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from scripts.bop_red_kite_raw_group_prefix_only_v1 import KeyPrefixCollector
from scripts.bop_red_kite_german_gps_eligibility_v1 import _source_lines, _timestamp
from scripts.bop_nesttool_2024_yearid_animal_overlap_v1 import p_mixed

CONTRACT=ROOT/"research/BOP_RED_KITE_SUI_GPS_YEAR_ID_ADMISSION_V1_CONTRACT.json"
HEADERS=ROOT/"BOP_RED_KITE_HEADER_ONLY_V1_FIRST_RECEIPT.json"
INVENTORY=ROOT/"BOP_RED_KITE_SOURCE_INVENTORY_V1_FIRST_RECEIPT.json"
PREVIOUS=ROOT/"BOP_RED_KITE_RAW_GROUP_PREFIX_ONLY_V1_FIRST_RECEIPT.json"

DATE_ARMS=("fixed_2023_DOY_ordinal","actual_calendar_month_day")
THIN_ARMS=("observed_source_events","unique_UTC_hour_bin","rolling_3600_seconds")
MIN_ARMS=("strict_gt_800","inclusive_ge_800")


def _frozen():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    h=json.loads(HEADERS.read_text(encoding="utf-8"))
    inv=json.loads(INVENTORY.read_text(encoding="utf-8"))
    prev=json.loads(PREVIOUS.read_text(encoding="utf-8"))
    src=c["pinned_source_files"]
    rule=c["predeclared_eligibility"]
    limits=c["scientific_limits"]
    safety=c["read_protocol"]
    if (
        c.get("contract_id")!="bop-redkite-SUI-source-year-bird-GPS-eligibility-v1"
        or c.get("frozen_date")!="2026-11-19"
        or c.get("source_zenodo_doi")!="10.5281/zenodo.13736049"
        or [x.get("key") for x in src]!=["SUI_indseasondata.csv","SUI_trackingdata.csv"]
        or [x.get("bytes") for x in src]!=[117327,266416454]
        or [x.get("md5") for x in src]!=["91394907a2d036e3dbacf5cd4f70475b","f654300e9a77b8dc41221f44d468ea2c"]
        or src[0]["whitelisted_prefix_columns"]!=["bird_id","year","year_id"]
        or src[1]["known_header"]!=h["verified_first_header"]["SUI_trackingdata"]["column_names"]
        or src[1]["whitelisted_columns"]!=["bird_id","year_id","timestamp","long_wgs","lat_wgs"]
        or rule.get("strict_longitude_gt")!=4
        or rule.get("strict_latitude_gt")!=45
        or rule.get("UTC_fixed_2023_DOY_inclusive")!=[70,175]
        or rule.get("UTC_actual_calendar_month_day_inclusive")!=["03-11","06-24"]
        or rule.get("date_arms")!=list(DATE_ARMS)
        or rule.get("sampling_arms")!=list(THIN_ARMS)
        or rule.get("minimum_location_arms")!=list(MIN_ARMS)
        or rule.get("primary_descriptive_arm")!="fixed_2023_DOY_ordinal__unique_UTC_hour_bin__strict_gt_800"
        or rule.get("all_twelve_arms_reported_regardless_of_matching_article_counts") is not True
        or rule.get("cannot_select_matching_arm_after_results") is not True
        or rule.get("assumed_train_fraction")!=0.7
        or rule.get("use_actual_published_train_488_when_article_count_697") is not True
        or c["paper_population_claims"]["frozen_Zenodo_metadata_seasons"]!=2866
        or c["paper_population_claims"]["frozen_Zenodo_metadata_bird_ID_strings"]!=553
        or c["paper_population_claims"]["published_Swiss_eligible_seasons"]!=697
        or c["paper_population_claims"]["published_Swiss_eligible_birds"]!=258
        or limits.get("status_on_provider_verified")!="SUI_SOURCE_12_ARM_QUALITY_COUNTS_ONLY"
        or limits.get("BOP_historical_terminal")!="empirical_state_prediction_mixed"
        or limits.get("redkite_external_terminal")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or not all(safety.get(k) is True for k in (
            "official_zenodo_v1_two_files_only",
            "full_source_byte_stream_for_MD5_and_bounded_row_validation",
            "metadata_outcome_columns_never_parsed_or_printed",
            "GPS_no_outcome_columns_opened",
            "source_time_space_values_transient_runner_memory_only",
            "no_persisted_source_CSVs_or_individual_year_rosters",
            "no_raw_or_hashed_animal_ID_or_year_ID_or_coordinates_or_timestamps_in_artifacts",
            "no_credentials_or_Movebank_access","no_inference_from_other_files_or_live_study_counts",
            "original_md5_and_header_sha256_required"
        ))
    ):
        raise ValueError("original prospectively frozen Swiss source-only admission contract changed")
    manifest={x["key"]:x for x in inv["source_manifest_observation"]["manifest"]}
    for x in src:
        if manifest[x["key"]]["md5"]!=x["md5"] or manifest[x["key"]]["bytes"]!=x["bytes"]:
            raise ValueError("official 2024 Swiss source bytes/MD5 no longer pinned")
    original=prev["original_source_output"]["sources"][1]
    if (
        original["source"]!="SUI_indseasondata.csv"
        or original["physical_record_lines"]!=2866
        or original["distinct_bird_ID_strings"]!=553
        or original["distinct_year_ID_strings"]!=2866
        or original["source_full_file_md5_verified"] is not True
    ):
        raise ValueError("original Swiss metadata sample has drifted")
    return c,h


def _metadata_year_bird(c,h):
    src=c["pinned_source_files"][0]
    header=h["verified_first_header"]["SUI_indseasondata"]
    scanner=KeyPrefixCollector({
        "key":src["key"],"bytes":src["bytes"],"md5":src["md5"],
        "header_columns":header["column_names"],
        "allowed_prefix_columns":src["whitelisted_prefix_columns"],
    },header["header_sha256"])
    for line in _source_lines({"filename":src["key"],"bytes":src["bytes"],"md5":src["md5"]}):
        scanner.feed(line)
    stats=scanner.finish()
    if (stats["physical_record_lines"]!=2866
        or stats["distinct_bird_ID_strings"]!=553
        or stats["distinct_year_ID_strings"]!=2866
        or stats["duplicate_year_ID_lines"]!=0
        or stats["year_ID_to_multiple_bird_IDs"]!=0):
        raise ValueError("Swiss source metadata animal-year join ambiguous")
    # Strings are volatile, in-memory only. Never log or emit them.
    return scanner.season_owner,stats


def _parse_approved_GPS_line(raw:bytes):
    """Decode only documented columns 1,2,3,7,8 of original 12-column CSV.

    The source columns 9-11, including temperature, are not field-decoded or
    saved. The leading columns are numeric or nonquoted identifier tokens.
    A malformed/quoted key is classified as invalid; never print source row.
    """
    parts=raw.split(b",",9)
    if len(parts)!=10 or any(
        not parts[k] or b'"' in parts[k] or b"\r" in parts[k] or b"\n" in parts[k]
        for k in (1,2,3,7,8)
    ):
        raise ValueError("malformed whitelisted Swiss GPS prefix")
    bird=parts[1].decode("utf-8")
    year=parts[2].decode("utf-8")
    when=_timestamp(parts[3].decode("utf-8"))
    lon=float(parts[7])
    lat=float(parts[8])
    if not (math.isfinite(lon) and math.isfinite(lat) and -180<=lon<=180 and -90<=lat<=90):
        raise ValueError("invalid Swiss GPS geographic coordinate")
    return bird,year,when,lon,lat


def collect_GPS_source(rows,known_header:bytes,meta:dict[str,str]):
    iterator=iter(rows)
    first=next(iterator,None)
    if first!=known_header:
        raise ValueError("original Swiss GPS CSV header altered or missing")
    timeline={name:defaultdict(list) for name in DATE_ARMS}
    counts=Counter()
    dates=Counter()
    conflicting=set()
    for raw in iterator:
        counts["source_GPS_physical_rows"]+=1
        try:
            bird,year,t,lon,lat=_parse_approved_GPS_line(raw)
        except (ValueError,UnicodeError,OverflowError):
            counts["malformed_GPS_rows"]+=1
            continue
        owner=meta.get(year)
        if owner is None:
            counts["GPS_rows_from_unlisted_year_ID"]+=1
            continue
        if bird!=owner:
            counts["GPS_rows_with_inconsistent_bird_ID"]+=1
            conflicting.add(year)
            continue
        counts["GPS_rows_with_exact_metadata_year_bird_match"]+=1
        if not (lon>4 and lat>45):
            counts["GPS_rows_outside_strict_geobounds"]+=1
            continue
        fixed=70<=t.timetuple().tm_yday<=175
        monthday=(3,11)<=(t.month,t.day)<=(6,24)
        epoch=calendar.timegm(t.timetuple())
        if fixed:
            timeline[DATE_ARMS[0]][year].append(epoch)
            dates[DATE_ARMS[0]]+=1
        if monthday:
            timeline[DATE_ARMS[1]][year].append(epoch)
            dates[DATE_ARMS[1]]+=1
    if conflicting:
        raise ValueError("official Swiss GPS source year ID to bird ID not one-to-one")
    return timeline,{
        "source_GPS_physical_rows":counts["source_GPS_physical_rows"],
        "malformed_GPS_rows":counts["malformed_GPS_rows"],
        "GPS_rows_from_unlisted_year_ID":counts["GPS_rows_from_unlisted_year_ID"],
        "GPS_rows_with_inconsistent_bird_ID":counts["GPS_rows_with_inconsistent_bird_ID"],
        "GPS_rows_with_exact_metadata_year_bird_match":counts["GPS_rows_with_exact_metadata_year_bird_match"],
        "GPS_rows_outside_strict_geobounds":counts["GPS_rows_outside_strict_geobounds"],
        "inseason_GPS_event_rows_by_date_arm":{k:dates[k] for k in DATE_ARMS},
        "linked_GPS_seasons_having_any_inseason_record_by_date_arm":{k:len(timeline[k]) for k in DATE_ARMS},
    }


def _three_counts(epoch_times:list[int])->dict[str,int]:
    sorted_times=sorted(epoch_times)
    last=None
    rolling=0
    for t in sorted_times:
        if last is None or t-last>=3600:
            last=t
            rolling+=1
    return {
        THIN_ARMS[0]:len(sorted_times),
        THIN_ARMS[1]:len({t//3600 for t in sorted_times}),
        THIN_ARMS[2]:rolling,
    }


def expected_shared_birds(histogram:Counter,n_seasons:int,ntrain:int)->float:
    if not (n_seasons>=2 and 1<=ntrain<n_seasons and
        sum(histogram.values())>0 and sum(k*v for k,v in histogram.items())==n_seasons):
        raise ValueError("incoherent hypothetical year-level split population")
    return sum(v*p_mixed(k,n_seasons,ntrain) for k,v in histogram.items())


def summarize_all_12(timelines,meta,cutoff:int=800)->list[dict]:
    results=[]
    for date_arm in DATE_ARMS:
        per_year_counts={y:_three_counts(times) for y,times in timelines[date_arm].items()}
        for thin in THIN_ARMS:
            for minrule in MIN_ARMS:
                years=[y for y,variants in per_year_counts.items()
                       if (variants[thin]>cutoff if minrule=="strict_gt_800"
                           else variants[thin]>=cutoff)]
                birdcounts=Counter(meta[y] for y in years)
                if any(y not in meta for y in years):
                    raise ValueError("source Swiss admission contains unknown year-ID key")
                hist=Counter(birdcounts.values())
                n=len(years)
                ntrain=round(.7*n)
                if n>=2 and 1<=ntrain<n:
                    overlap=round(expected_shared_birds(hist,n,ntrain),6)
                else:
                    overlap=None
                name=f"{date_arm}__{thin}__{minrule}"
                results.append({
                    "arm":name,
                    "eligible_year_ID_strings":n,
                    "distinct_bird_ID_strings":len(birdcounts),
                    "bird_seasons_per_bird_histogram":{str(k):hist[k] for k in sorted(hist)},
                    "birds_with_multiple_eligible_seasons":sum(v for k,v in hist.items() if k>=2),
                    "max_seasons_per_bird":max(hist,default=0),
                    "hypothetical_uniform_year_split_training_seasons":ntrain if n>=2 else None,
                    "hypothetical_uniform_year_split_test_seasons":n-ntrain if n>=2 else None,
                    "expected_bird_ID_strings_in_both_split_roles":overlap,
                    "matches_both_published_697_seasons_258_birds_numerically":(n==697 and len(birdcounts)==258),
                    "published_2024_real_split_and_bird_authentication_not_verified":True,
                })
    if len(results)!=12 or len({x["arm"] for x in results})!=12:
        raise ValueError("not all precommitted Swiss screening arms emitted")
    return results


def run():
    c,h=_frozen()
    meta,stats=_metadata_year_bird(c,h)
    src=c["pinned_source_files"][1]
    head=h["verified_first_header"]["SUI_trackingdata"]
    expected=(",".join(head["column_names"])+"\r\n").encode("utf-8")
    if hashlib.sha256(expected).hexdigest()!=head["header_sha256"]:
        raise ValueError("Swiss first provider GPS line no longer matches original receipt")
    timeline,count=collect_GPS_source(
        _source_lines({"filename":src["key"],"bytes":src["bytes"],"md5":src["md5"]}),
        expected,meta)
    if count["source_GPS_physical_rows"]<2866:
        raise ValueError("Swiss original GPS source unexpectedly small for metadata roster")
    arms=summarize_all_12(timeline,meta)
    return {
        "schema_version":1,
        "status":"SUI_SOURCE_12_ARM_QUALITY_COUNTS_ONLY",
        "preaccess_contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "original_GPS_and_metadata_full_provider_MD5_verified":True,
        "Swiss_source_unfiltered_metadata_year_ID_strings":stats["distinct_year_ID_strings"],
        "Swiss_source_unfiltered_metadata_bird_ID_strings":stats["distinct_bird_ID_strings"],
        "GPS_source_aggregate":count,
        "twelve_fixed_eligibility_arms":arms,
        "primary_arm_published_before_source":c["predeclared_eligibility"]["primary_descriptive_arm"],
        "no_posthoc_selection_of_matching_697_258":True,
        "no_label_or_GPS_source_individual_record_emitted":True,
        "paper_2024_training_roster_authenticated":False,
        "original_actual_2024_training_random_seed_observed":False,
        "actual_forecast_probabilities_scored":False,
        "BOP_historical_terminal":"empirical_state_prediction_mixed",
        "redkite_biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    if args.out.resolve() in {CONTRACT.resolve(),HEADERS.resolve(),PREVIOUS.resolve(),INVENTORY.resolve()}:
        raise ValueError("cannot overwrite immutable source contracts/receipts")
    try:
        result=run()
    except (OSError,ValueError,UnicodeError,OverflowError,RuntimeError) as exc:
        result={
            "schema_version":1,
            "status":"HOLD_SWISS_SOURCE_GPS_OR_IDENTITY",
            "error_type":type(exc).__name__,
            "source_role":"FROZEN_SWISS_SOURCE_SELECTION_NO_OUTCOME_ANALYSIS",
            "no_label_or_GPS_source_individual_record_emitted":True,
            "paper_2024_training_roster_authenticated":False,
            "actual_forecast_probabilities_scored":False,
            "BOP_historical_terminal":"empirical_state_prediction_mixed",
            "redkite_biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        }
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    if result["status"]!="SUI_SOURCE_12_ARM_QUALITY_COUNTS_ONLY":
        raise SystemExit("SWISS_SOURCE_ELIGIBILITY_HOLD: do not promote group/biology claims")


if __name__=="__main__":
    main()
