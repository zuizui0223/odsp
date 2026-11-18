#!/usr/bin/env python3
"""Verify frozen first official Zenodo German GPS-cadence aggregate, without GPS.

Both official Actions ZIP and JSON byte hashes were independently calculated
from the first official immutable artifact BEFORE this verifier was committed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_RED_KITE_GER_GPS_CADENCE_V1_CONTRACT.json"
RECEIPT=ROOT/"BOP_RED_KITE_GER_GPS_CADENCE_V1_FIRST_RECEIPT.json"

EXPECTED=[
 ("all_linked_geo_season_years",159,63,236989,236830,0,109,0.463619,0.613985,0.370629,
  (30,59.6,179.85),(85,201,925,103681,4907,87776,1842,6281,31132)),
 ("source_primary_gt800_eligible_years",99,49,210420,210321,0,67,0.487398,0.64955,0.392557,
  (30,59.03,95),(74,186,867,96527,4856,82563,1470,4764,19014)),
]
BINS=["0to5m","5to15m","15to30m","30to45m","45to55m",
      "55to65m","65to75m","75to120m","120mplus"]

def verify_first(receipt:dict,contract:dict,*,raw:bytes|None=None)->dict:
    a=receipt["first_actions"]
    source=receipt["source_funnel"]
    limits=receipt["interpretation"]
    contract_sha="18b743e0e1661172deeb90a9c8b69907c1b6864b08e64f82dd0db74913037de2"
    first_sha="77b375496f01a010487c13b8277a89373a60f41e72b24913634aea0db6381167"
    first_zip_sha="558af84440cb0fb792814c5d4eeb6394fc768cce5732fa7da63060c2556913fb"
    if (
        receipt.get("receipt_id")!="bop-red-kite-GER-official-source-GPS-cadence-first-v1"
        or receipt["preaccess_contract_commit"]!="903a85501371e6d8294cf0cb29125046da0eeb07"
        or a["run_id"]!=44290699238
        or a["source_job_id"]!=134755815277
        or a["source_branch_head_sha"]!="16f39546b79f90c4d89931c000699c9b1c9ef38a"
        or a["artifact_id"]!=14421093958
        or a["artifact_name"]!="bop-red-kite-ger-gps-cadence-first"
        or a["artifact_zip_bytes"]!=1265
        or a["artifact_zip_sha256"]!=first_zip_sha
        or a["official_JSON_filename"]!="bop-redkite-ger-gps-cadence-first.json"
        or a["official_JSON_bytes"]!=2922
        or a["official_JSON_sha256"]!=first_sha
        or a["contract_sha256"]!=contract_sha
        or hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=contract_sha
        or contract["contract_id"]!="bop-redkite-original-GER-GPS-cadence-frozen-v1"
        or a["source_job_conclusion"]!="success"
        or a["python_offline_tests"]!=["3.10","3.12","3.13"]
    ):
        raise ValueError("first official cadence provenance changed")
    if (
        source["original_GPS_physical_lines"]!=500778
        or source["malformed_GPS_rows"]!=1
        or source["year_ids_outside_pinned_metadata"]!=2524
        or source["year_ids_with_wrong_bird_strings"]!=0
        or source["linked_geo_season_GPS_events"]!=236989
        or source["official_GPS_and_metadata_MD5_verified"] is not True
    ):
        raise ValueError("first official GPS source counts changed")
    if len(receipt["cohorts"])!=2:
        raise ValueError("must preserve both fixed cohorts")
    for item,expected in zip(receipt["cohorts"],EXPECTED):
        (name,seasons,birds,events,positive,zero,short_n,p55,p60,p5565,quantiles,bins)=expected
        quant=item["quantiles_minutes"] if "quantiles_minutes" in item else item.get("global_nearest_rank_quantile_minutes",{})
        # Immutable receipt uses quantiles_minutes; original output has global_nearest_rank_quantile_minutes.
        actual_quant=(quant.get("q10"),quant.get("q50"),quant.get("q90"))
        actual_bins=tuple(item["bins"].get(k) for k in BINS)
        if (
            item["cohort"]!=name
            or item["seasons"]!=seasons
            or item["birds"]!=birds
            or item["events"]!=events
            or item["positive_gaps"]!=positive
            or item["zero"]!=zero
            or item["short55_seasons"]!=short_n
            or item["p_under55"]!=p55
            or item["p_under60"]!=p60
            or item["p_55to65"]!=p5565
            or actual_quant!=quantiles
            or actual_bins!=bins
            or sum(actual_bins)!=positive
            or positive+zero!=events-seasons
            or short_n>seasons
        ):
            raise ValueError("source sampling/cadence histogram was reclassified")
    for key,needed in {
        "greater_than_zero_subhourly_gaps_in_all_and_eligible_cohorts":True,
        "archive_not_strict_one_measurement_each_60_minutes":True,
        "source_99_seasons_49_bird_ID_strings_not_published_99_63":True,
        "publication_input_GPS_downsampling_algorithm_identified":False,
        "no_complete_original_external_replication":True,
        "original_163_seasons_65_birds_not_reproduced":True,
        "group_independence_authenticated":False,
        "no_real_GPS_coordinate_or_timestamp_or_birdID_exported":True,
        "no_nesting_or_success_labels_accessed":True,
        "no_new_probability_or_individual_gain_scored":True,
        "original_BOP_terminal":"empirical_state_prediction_mixed",
        "real_red_kite_prediction_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
    }.items():
        if limits.get(key)!=needed:
            raise ValueError("recorded code/sample limitations were promoted beyond the evidence")
    if raw is not None:
        if len(raw)!=2922 or hashlib.sha256(raw).hexdigest()!=first_sha:
            raise ValueError("rerun code-only GPS-cadence JSON differs from first official immutable bytes")
        out=json.loads(raw)
        if (
            out.get("status")!="SOURCE_GPS_CADENCE_OBSERVED_ONLY"
            or out.get("preaccess_contract_sha256")!=contract_sha
            or out.get("original_provider_GER_metadata_and_GPS_MD5_verified") is not True
            or out.get("original_60min_downsampling_method_identified") is not False
            or out.get("no_breeding_label_values_accessed") is not True
            or out.get("no_exact_timestamps_positions_or_IDs_exported") is not True
            or out.get("red_kite_biological_terminal")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        ):
            raise ValueError("rerun source GPS cadence or biological claim boundary changed")
        original=out["fixed_interval_cohorts"]
        for item,receipt_item in zip(original,receipt["cohorts"]):
            if (
                item["cohort"]!=receipt_item["cohort"]
                or item["interval_bin_counts"]!=receipt_item["bins"]
                or item["positive_consecutive_GPS_intervals"]!=receipt_item["positive_gaps"]
                or item["selected_season_ID_strings"]!=receipt_item["seasons"]
                or item["distinct_bird_ID_strings"]!=receipt_item["birds"]
            ):
                raise ValueError("latest provider source cadence disagrees with immutable first output")
    return {
        "first_official_archive_hash_verified":True,
        "original_cadence_source_run":a["run_id"],
        "original_eligible_seasons":99,
        "original_eligible_bird_strings":49,
        "subhourly_intervals_present":True,
        "eligible_fraction_under_55min":0.487398,
        "eligible_fraction_under_60min":0.64955,
        "original_downsampling_algorithm_known":False,
        "biological_terminal":limits["real_red_kite_prediction_terminal"],
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result",type=Path)
    args=p.parse_args()
    raw=args.result.read_bytes() if args.result else None
    ans=verify_first(
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        json.loads(CONTRACT.read_text(encoding="utf-8")),
        raw=raw)
    print(json.dumps(ans,sort_keys=True))

if __name__=="__main__":
    main()
