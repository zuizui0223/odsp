"""Explicit post-schema-exposure Rhode Island v3 ecological source adapter.

This is NEW exploratory v1, not a retroactive fix of the frozen v0 route.
v0's authoritative conclusion is source-schema UNAVAILABLE. The post-exposure
v1 source map is fixed independently in RI_SOLAR_CLOCK_SCHEMA_V1_EXPLORATORY_CONTRACT.json
before any NEW v1 score is calculated. It does not add/retune the
astronomical core, species-selection thresholds, split, or bootstrap.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import math
import re
from typing import Any, Mapping, Sequence

from .ri_solar_clock_transfer_v0 import (
    DielEvent, fit_species_profiles,
    score_new_site_future_year, site_is_sealed,
    summarize_site_level_transfer,
)
from .ri_solar_source_v0 import (
    _member_zip_csv, _dst_clock_hour_maybe_invalid,
)

VERSION="odsp-ri-solar-vs-clock-yearseason-v2-exploratory"
DEPLOYMENT_HEADER=(
    "YearSeason","Primary.Site.ID","Trap.Station.Name","Camera.Name",
    "Setup.Date","Retrieval.Date","Latitude","Longitude",
)
DETECTION_HEADER=(
    "YearSeason","Primary.Site.ID","Trap.Station.Name","Camera.Name",
    "Date.Time","Date","Time","Common.Name","Class","Order","Family",
    "Genus","Species","Genus.and.Species","Sighting.Quantity",
)
SITE="Primary.Site.ID"
STATION="Trap.Station.Name"
CAMERA="Camera.Name"
SEASON="YearSeason"
SPECIES="Genus.and.Species"
DATE_TIME="Date.Time"

SEASON_RE=re.compile(r"^(w|s)(18|19|20|21|22|23)$")
DATE_TIME_PATTERNS=(
    "%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M",
    "%m/%d/%Y %H:%M:%S","%m/%d/%Y %H:%M",
    "%m/%d/%Y %I:%M:%S %p","%m/%d/%Y %I:%M %p",
    "%Y-%m-%dT%H:%M:%S","%Y-%m-%dT%H:%M",
    "%Y-%m-%d %I:%M:%S %p","%Y-%m-%d %I:%M %p",
)
DATE_ONLY_PATTERNS=("%Y-%m-%d","%m/%d/%Y")
TIME_ONLY_PATTERNS=("%H:%M:%S","%H:%M","%I:%M:%S %p","%I:%M %p")
EXCLUDED_SPECIES=frozenset((
    "unknown","unidentified","human","homo sapiens",
    "empty","blank","none","other","vehicle","animal",
))


def _validate_contract(plan:Mapping[str,object])->None:
    if (plan.get("study_id")!="odsp-ri-solar-vs-clock-yearseason-v2-exploratory"
        or plan.get("analysis_status")!="FROZEN_POSTEXPOSURE_CODED_YEARSEASON_SOURCE_AMENDMENT_V2"):
        raise ValueError("not frozen post-schema-exposure RI source contract")
    source=plan.get("data",{})
    if (source.get("exact_deployment_header")!=list(DEPLOYMENT_HEADER)
        or source.get("exact_detection_header")!=list(DETECTION_HEADER)):
        raise ValueError("frozen literal source headers differ from v1 parser")
    fields=plan.get("key_map",{})
    if (
        fields.get("physical_site")!=SITE
        or fields.get("physical_station")!=STATION
        or fields.get("camera_device")!=CAMERA
        or fields.get("species")!=SPECIES
        or fields.get("detection_datetime")!=DATE_TIME
        or fields.get("deployment_match_composite")!=[SEASON,SITE,STATION,CAMERA]
    ):
        raise ValueError("source primary site/station/camera/taxon semantics changed")
    if plan.get("schema_version")!=2:
        raise ValueError("not frozen post-exposure coded-yearseason v2 contract")
    coding=plan.get("parser_policy",{}).get("yearseason_code_mapping",{})
    if (coding.get("pattern")!=r"^(w|s)(18|19|20|21|22|23)$"
        or coding.get("excluded_spring_codes")!=["sp22"]
        or coding.get("reject_unrecognized_codes") is not True):
        raise ValueError("source coding differs from frozen v2 map")
    processing=plan.get("parser_policy",{})
    if (processing.get("dedup_minutes")!=30
        or processing.get("unmatched_detection_join_fraction_hard_stop")!=.02
        or processing.get("datetime_formats")!=list(DATE_TIME_PATTERNS)):
        raise ValueError("source date/duplicate/join thresholds differ from v1")
    original=plan.get("unchanged_scientific_invariants",{})
    if (
        original.get("scientific_train_years")!=[2018,2019,2020,2021]
        or original.get("scientific_test_years")!=[2022,2023]
        or original.get("min_training_events_per_species")!=120
        or original.get("jeffreys_pseudocount")!=.5
        or original.get("bootstrap_draws")!=2000
        or original.get("bootstrap_seed")!=2026100803
    ):
        raise ValueError("frozen original ecological inference invariants changed")


def _season(value:str)->tuple[str,int]|None:
    # Published source codes w22/w23 and s22 replace literal WinterYYYY.
    # This was identified after v0/v1 source exposure: v2 is exploratory.
    match=SEASON_RE.fullmatch(value.strip().casefold())
    if match is None:
        return None
    return ("winter" if match.group(1)=="w" else "summer",
            2000+int(match.group(2)))


def _datetime(row:Mapping[str,str])->datetime|None:
    value=(row.get(DATE_TIME) or "").strip()
    if value:
        for fmt in DATE_TIME_PATTERNS:
            try:
                return datetime.strptime(value,fmt)
            except ValueError:
                pass
        return None
    d,t=(row.get("Date") or "").strip(),(row.get("Time") or "").strip()
    for fmt_d in DATE_ONLY_PATTERNS:
        for fmt_t in TIME_ONLY_PATTERNS:
            try:
                return datetime.strptime(d+" "+t,fmt_d+" "+fmt_t)
            except ValueError:
                pass
    return None


def _validate_headers(
    deployments:Sequence[Mapping[str,str]],
    detections:Sequence[Mapping[str,str]],
)->None:
    if not deployments or not detections:
        raise ValueError("source has no deployment or detection rows")
    if tuple(deployments[0])!=DEPLOYMENT_HEADER:
        raise ValueError("deployment member header changed from schema-v1 freeze")
    if tuple(detections[0])!=DETECTION_HEADER:
        raise ValueError("detection member header changed from schema-v1 freeze")


def _key(row:Mapping[str,str])->tuple[str,str,str,str]:
    return tuple((row.get(c) or "").strip() for c in (SEASON,SITE,STATION,CAMERA))


def v2_events_from_two_tables(
    deployments:Sequence[Mapping[str,str]],
    detections:Sequence[Mapping[str,str]],
    plan:Mapping[str,object],
)->tuple[list[DielEvent],dict[str,object]]:
    """One physical primary-site split; station+device needed ONLY for joining."""
    _validate_contract(plan)
    _validate_headers(deployments,detections)
    coords:dict[tuple[str,str,str,str],tuple[float,float]]={}
    field_stats=Counter()
    for row in deployments:
        key=_key(row)
        if any(not x for x in key):
            field_stats["deployment_blank_composite_key"]+=1
            continue
        try:
            lat,lon=float(row["Latitude"]),float(row["Longitude"])
        except (ValueError,TypeError,KeyError):
            field_stats["deployment_invalid_coordinate"]+=1
            continue
        if not math.isfinite(lat) or not math.isfinite(lon) or not 39<=lat<=43 or not -74<=lon<=-70:
            field_stats["deployment_invalid_coordinate"]+=1
            continue
        old=coords.setdefault(key,(lat,lon))
        if old!=(lat,lon):
            raise ValueError("same physical station+camera+season maps to conflicting coordinates")
    if not coords:
        raise ValueError("source has no admissible deployment join key")
    staged=[]
    counts=Counter()
    for row in detections:
        counts["source_photo_rows"]+=1
        key=_key(row)
        if any(not x for x in key):
            counts["detection_blank_join_key"]+=1
            continue
        parsed=_season(key[0])
        if parsed is None:
            counts["unrecognized_season_year"]+=1
            continue
        taxon=(row.get(SPECIES) or "").strip().casefold()
        if not taxon or taxon in EXCLUDED_SPECIES:
            counts["excluded_unknown_or_nontarget_taxon"]+=1
            continue
        position=coords.get(key)
        if position is None:
            counts["unmatched_original_camera_deployment"]+=1
            continue
        instant=_datetime(row)
        if instant is None:
            counts["unparsed_detection_clock"]+=1
            continue
        if _dst_clock_hour_maybe_invalid(instant):
            counts["DST_ambiguous_or_nonexistent_time"]+=1
            continue
        season,year=parsed
        hour=instant.hour+instant.minute/60.+instant.second/3600.
        staged.append((key[1],key[2],key[3],taxon,season,year,instant,
                       position[0],position[1],hour))
        counts["photo_rows_with_all_frozen_fields"]+=1
    # Join failure is a structural admission criterion; no arbitrary
    # denominator change after viewing observed species/clock outcomes.
    if counts["unmatched_original_camera_deployment"] > .02*max(counts["source_photo_rows"],1):
        raise ValueError("more than 2% of source images lack the frozen composite deployment match")
    staged.sort(key=lambda v:(v[0],v[1],v[2],v[3],v[4],v[5],v[6]))
    last_observation:dict[tuple[str,str,str,str,str,int],datetime]={}
    accepted=[]
    for site,station,camera,taxon,season,year,instant,lat,lon,hour in staged:
        key=(site,station,camera,taxon,season,year)
        previous=last_observation.get(key)
        if previous is not None and (instant-previous).total_seconds()<1800:
            counts["suppressed_within_30min_photo_duplicates"]+=1
            continue
        last_observation[key]=instant
        accepted.append(DielEvent(
            site_id=site,species=taxon,season=season,season_year=year,
            day=instant.date(),clock_hour=hour,latitude=lat,longitude=lon,
        ))
    counts["retained_independent_30min_detection_events"]=len(accepted)
    if not accepted:
        raise ValueError("no usable 30-minute wildlife camera detection events under v1")
    return accepted,{
        "schema_version":1,
        "source_schema_version":VERSION,
        "source_deployment_row_count":len(deployments),
        "source_detection_image_row_count":len(detections),
        "unique_site_station_camera_season_join_keys":len(coords),
        "deployment_metadata_filter_counts":dict(field_stats),
        "detection_filter_counts":dict(counts),
        "physical_site_ids_and_camera_coordinates_exposed":False,
        "camera_clock_timezone_independently_verified":False,
        "source_schema_selected_after_v0_data_rows_may_have_been_read":True,
        "frozen_v0_inference_reclassified":False,
    }


def run_exploratory_ri_solar_clock_v2(
    source_bytes:bytes,plan:Mapping[str,object],
)->dict[str,object]:
    _validate_contract(plan)
    members=_member_zip_csv(source_bytes)
    events,preflight=v2_events_from_two_tables(
        members["RI_CameraSurvey_Deployments.csv"],
        members["RI_CameraSurvey_Detections.csv"],
        plan,
    )
    train=[e for e in events if e.season_year<=2021 and not site_is_sealed(e.site_id)]
    heldout=[e for e in events if e.season_year>=2022 and site_is_sealed(e.site_id)]
    training_sites={e.site_id for e in train}
    heldout_sites={e.site_id for e in heldout}
    if training_sites & heldout_sites:
        raise ValueError("physical primary-site ID overlap between training and validation")
    profiles,admitted=fit_species_profiles(train)
    scored=[]
    out_of_training_taxa=0
    for event in heldout:
        model=profiles.get(event.species)
        if model is None:
            out_of_training_taxa+=1
            continue
        scored.append((event,score_new_site_future_year(event,model)))
    result=summarize_site_level_transfer(scored)
    by_season=Counter(e.season for e,x in scored)
    minimum=plan["unchanged_scientific_invariants"]["min_test_events_per_season"]
    if any(by_season[s]<minimum for s in ("winter","summer")):
        result["scientific_status"]="UNAVAILABLE_INSUFFICIENT_SCORED_EVENTS_PER_SEASON"
        result["solar_transfer_both_seasons_positive"]=False
    if not result["all_season_site_floor_met"]:
        result["scientific_status"]="UNAVAILABLE_INSUFFICIENT_NEW_SITES_PER_SEASON"
        result["solar_transfer_both_seasons_positive"]=False

    # Descriptive-only species heterogeneity: no species-wise selection
    # or multiple-testing claims from these post-exposure profiles.
    groups:dict[str,list[tuple[DielEvent,dict[str,float]]]]=defaultdict(list)
    for event,sc in scored:
        groups[event.species].append((event,sc))
    species_summaries={}
    minimum_species_sites=plan["secondary_exploratory_outputs"]["species_site_minimum"]
    minimum_species_years=plan["secondary_exploratory_outputs"]["species_year_minimum"]
    for species,records in sorted(groups.items()):
        if (len({e.site_id for e,_ in records})<minimum_species_sites
            or len({e.season_year for e,_ in records})<minimum_species_years):
            continue
        summary=summarize_site_level_transfer(records)
        species_summaries[species]={
            "scored_images_after_dedup":len(records),
            "new_site_count":len({e.site_id for e,_ in records}),
            "winter":summary["season_groups"]["winter"],
            "summer":summary["season_groups"]["summer"],
            "solely_descriptive":True,
        }
    return {
        "schema_version":1,
        "method_version":VERSION,
        "status":result["scientific_status"],
        "source_audit":preflight,
        "training_site_count":len(training_sites),
        "heldout_site_count":len(heldout_sites),
        "training_eligible_species_count":len(profiles),
        "scored_heldout_events":len(scored),
        "out_of_training_species_events":out_of_training_taxa,
        "scored_events_by_season":dict(by_season),
        "species_train_admission":admitted,
        "primary_heldout_solar_clock":result,
        "species_secondary_descriptive":species_summaries,
        "new_empirical_primary_qualified":False,
        "historical_v0_source_schema_failure_reclassified":False,
        "source_schema_chosen_after_previous_outcome_rows_may_have_been_read":True,
        "camera_detection_true_activity_identified":False,
        "camera_timezone_independently_verified":False,
    }
