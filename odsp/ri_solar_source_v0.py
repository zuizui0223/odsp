"""Source-pinned, fail-closed RI camera-trap outcome pipeline for new N2 ecology.

Archive: Zenodo 14508932 v3, DataS1.zip (MD5 pinned in frozen plan).
This is a NEW observational prediction analysis. It deliberately does not
re-open prior ODSP empirical endpoints or establish untouched-external
source independence. Source camera clock zone is ASSUMED America/New_York
until independently documented; any output is exploratory if unverified.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping
import zipfile

from .ri_solar_clock_transfer_v0 import (
    DielEvent, fit_species_profiles, score_new_site_future_year,
    site_is_sealed, summarize_site_level_transfer,
)

from .ri_zipinfo_technical_recovery_v0 import (
    inspect_ri_pinned_zip_central_directory,
)

SOURCE_MD5="c66943e6c2a9aab0abce2a1eba8ce02e"
EXPECTED_MEMBERS={
    "RI_CameraSurvey_Deployments.csv",
    "RI_CameraSurvey_Detections.csv",
}
DETECTION_TIME_FORMATS=("%H:%M:%S","%H:%M","%I:%M:%S %p","%I:%M %p")
DETECTION_DATE_FORMATS=("%Y-%m-%d","%m/%d/%Y","%Y/%m/%d","%m-%d-%Y")
DETECTION_DATETIME_FORMATS=(
    "%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M",
    "%m/%d/%Y %H:%M:%S","%m/%d/%Y %H:%M",
    "%Y-%m-%dT%H:%M:%S","%Y-%m-%dT%H:%M",
)
EXCLUDED_NAMES={
    "human","homo sapiens","unknown","unidentified","unknown species",
    "vehicle","other","blank","none","camera technician","animal",
}
SEASON_PATTERN=re.compile(
    r"(?i)(winter|summer|spring|fall|autumn)[^0-9]*(2018|2019|2020|2021|2022|2023)"
    r"|(2018|2019|2020|2021|2022|2023)[^a-z]*(winter|summer|spring|fall|autumn)"
)


def _norm(name:str)->str:
    return re.sub(r"[^a-z0-9]","",name.casefold().strip())


def _schema(rows:Iterable[Mapping[str,str]], aliases:Mapping[str,list[str]], *,
            required:tuple[str,...], one_of_datetime:bool=False
           )->tuple[dict[str,str],list[dict[str,str]]]:
    objects=list(rows)
    if not objects:
        raise ValueError("empty source CSV")
    header=tuple(objects[0])
    mapped={}
    for name, choices in aliases.items():
        hits=[h for h in header if _norm(h) in {_norm(x) for x in choices}]
        if len(hits)>1:
            raise ValueError(f"ambiguous column for {name}: {len(hits)} candidates")
        if hits:
            mapped[name]=hits[0]
    absent=[name for name in required if name not in mapped]
    if absent:
        raise ValueError(f"required source columns unavailable: {absent}")
    if one_of_datetime and not (
        "detection_datetime" in mapped
        or ("detection_date" in mapped and "detection_time" in mapped)
    ):
        raise ValueError("date and local clock-time columns unavailable")
    return mapped,objects


def _member_zip_csv(raw:bytes)->dict[str,list[dict[str,str]]]:
    if hashlib.md5(raw).hexdigest()!=SOURCE_MD5:
        raise ValueError("Zenodo v3 archive MD5 does not match frozen source")
    if len(raw)>75_000_000:
        raise ValueError("archive exceeds frozen input ceiling")
    # Post-first-failure TECHNICAL repair only: the original 150 MB
    # uncompressed-member gate was smaller than the pinned v3 detection
    # CSV (245,234,894 bytes). The separately pre-result frozen ZIP
    # contract requires MD5, only two known CSV basenames, safe member
    # paths, finite expansion ratio and member/total expanded-size caps
    # BEFORE the first byte of any CSV member is read. No ecological
    # selection, state, score or predictor is changed.
    inspection=inspect_ri_pinned_zip_central_directory(raw)
    if inspection.recovery_eligibility != "TECHNICAL_ZIP_RECOVERY_ELIGIBLE":
        raise ValueError("ZIP structure not authorized for source recovery")
    output={}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos=archive.infolist()
        for info in infos:
            if info.is_dir():
                continue
            name=Path(info.filename).name
            if name in EXPECTED_MEMBERS:
                if name in output:
                    raise ValueError("duplicate named ZIP input member")
                if (info.flag_bits & 0x1):
                    raise ValueError("encrypted archive member forbidden")
                with archive.open(info) as stream:
                    # Standard Python zipfile validates member CRC on read.
                    content=stream.read()
                text=content.decode("utf-8-sig")
                output[name]=list(csv.DictReader(io.StringIO(text,newline="")))
    if set(output)!=EXPECTED_MEMBERS:
        raise ValueError("frozen source deployment and detection members absent")
    return output


def _parse_season(value:str)->tuple[str,int]|None:
    match=SEASON_PATTERN.fullmatch(value.strip())
    if not match:
        return None
    season=(match.group(1) or match.group(4)).casefold()
    year=int(match.group(2) or match.group(3))
    if season not in ("winter","summer"):
        return None
    return season,year


def _parse_clock_datetime(row:Mapping[str,str], names:Mapping[str,str])->datetime|None:
    raw_dt=row.get(names.get("detection_datetime",""),"").strip()
    if raw_dt:
        for fmt in DETECTION_DATETIME_FORMATS:
            try:
                return datetime.strptime(raw_dt,fmt)
            except ValueError:
                pass
        return None
    raw_d=row.get(names.get("detection_date",""),"").strip()
    raw_t=row.get(names.get("detection_time",""),"").strip()
    for date_fmt in DETECTION_DATE_FORMATS:
        for time_fmt in DETECTION_TIME_FORMATS:
            try:
                return datetime.strptime(raw_d+" "+raw_t,date_fmt+" "+time_fmt)
            except ValueError:
                pass
    return None


def _dst_clock_hour_maybe_invalid(value:datetime)->bool:
    """Conservatively exclude local times with DST-ambiguous offsets.

    The source local clock zone is not independently verified; this
    excludes ambiguous or nonexistent 1–3 AM transition observations,
    not correcting arbitrary source clock drift.
    """
    from zoneinfo import ZoneInfo
    from datetime import timezone
    tz=ZoneInfo("America/New_York")
    a=value.replace(tzinfo=tz,fold=0)
    b=value.replace(tzinfo=tz,fold=1)
    if a.utcoffset()!=b.utcoffset():
        return True
    # Check round-trip of local wall time via real UTC.
    restored=a.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None)
    return restored!=value


def source_rows_to_events(
    archive_bytes:bytes,
    contract:Mapping[str,object],
)->tuple[list[DielEvent],dict[str,object]]:
    """Read one whole pinned archive after source design has been frozen."""
    if contract.get("study_id")!="odsp-ri-solar-vs-clock-site-year-transfer-v0":
        raise ValueError("wrong ecological study source contract")
    names=contract["source_schema_predeclared_aliases"]
    source=_member_zip_csv(archive_bytes)
    dep_names,deployments=_schema(
        source["RI_CameraSurvey_Deployments.csv"],names,
        required=("site","camera","yearseason","latitude","longitude"),
    )
    det_names,detections=_schema(
        source["RI_CameraSurvey_Detections.csv"],names,
        required=("site","camera","species","yearseason"),
        one_of_datetime=True,
    )
    coords:dict[tuple[str,str,str],tuple[float,float]]={}
    site_season_coords:dict[tuple[str,str],set[tuple[float,float]]]=defaultdict(set)
    problematic_deployments=0
    for row in deployments:
        site=row[dep_names["site"]].strip()
        camera=row[dep_names["camera"]].strip()
        season=row[dep_names["yearseason"]].strip()
        if not site or not camera or not season:
            problematic_deployments+=1
            continue
        try:
            lat=float(row[dep_names["latitude"]])
            lon=float(row[dep_names["longitude"]])
        except (ValueError,TypeError):
            problematic_deployments+=1
            continue
        if not 39<=lat<=43 or not -74<=lon<=-70:
            problematic_deployments+=1
            continue
        key=(site,camera,season)
        coordinate=(lat,lon)
        if key in coords and coords[key]!=coordinate:
            raise ValueError("same physical camera/season has conflicting coordinates")
        coords[key]=coordinate
        site_season_coords[site,season].add(coordinate)

    observed=[]
    counts=Counter()
    for row in detections:
        counts["source_image_detection_rows"]+=1
        site=row[det_names["site"]].strip()
        camera=row[det_names["camera"]].strip()
        species=row[det_names["species"]].strip().casefold()
        yearseason=row[det_names["yearseason"]].strip()
        parsed=_parse_season(yearseason)
        if not site or not camera or not species or species in EXCLUDED_NAMES or parsed is None:
            counts["excluded_unknown_or_nonfocal_taxa_season"]+=1
            continue
        loc=coords.get((site,camera,yearseason))
        if loc is None:
            counts["unmatched_deployment_or_coordinate"]+=1
            continue
        timestamp=_parse_clock_datetime(row,det_names)
        if timestamp is None:
            counts["unparseable_local_datetime"]+=1
            continue
        if _dst_clock_hour_maybe_invalid(timestamp):
            counts["dst_ambiguous_or_nonexistent_clock"]+=1
            continue
        season,year=parsed
        clock=timestamp.hour+timestamp.minute/60+timestamp.second/3600
        observed.append((
            site,camera,species,season,year,timestamp,loc[0],loc[1],clock,
        ))
        counts["admissible_image_detection_rows_before_thinning"]+=1

    # One event per species + camera + site + seasonal roster every 30 min.
    # Use earliest timestamp in source to avoid row ordering effects.
    observed.sort(key=lambda x:(x[0],x[1],x[2],x[3],x[4],x[5]))
    accepted=[]
    last_at={}
    for site,camera,species,season,year,timestamp,lat,lon,clock in observed:
        key=(site,camera,species,season,year)
        last=last_at.get(key)
        if last is not None and (timestamp-last).total_seconds()<1800:
            counts["deduplicated_image_rows"]+=1
            continue
        last_at[key]=timestamp
        accepted.append(DielEvent(site_id=site,species=species,
                                  season=season,season_year=year,
                                  day=timestamp.date(),clock_hour=clock,
                                  latitude=lat,longitude=lon))
    counts["retained_30min_events"]=len(accepted)
    if not accepted:
        raise ValueError("no valid ecological detections after predeclared cleaning")
    if counts["unmatched_deployment_or_coordinate"] > .02 * max(
        counts["source_image_detection_rows"],1
    ):
        raise ValueError("too many unmatched physical deployment IDs for valid transfer")
    return accepted,{
        "archive_md5":SOURCE_MD5,
        "schema_matched_deployment_columns":dep_names,
        "schema_matched_detection_columns":det_names,
        "source_deployment_record_count":len(deployments),
        "valid_deployment_join_keys":len(coords),
        "problematic_deployment_records":problematic_deployments,
        "physical_site_season_count":len(site_season_coords),
        "source_counts":dict(counts),
        "camera_source_local_timezone_verified":False,
        "site_sampling_population_probability_verified":False,
        "training_source_frozen_separation_checked_in_analysis":True,
        "historical_original_outcome_nonaccess_proven":False,
    }


def execute_frozen_ri_solar_transfer(
    archive_bytes:bytes,
    frozen_contract:Mapping[str,object],
)->dict[str,object]:
    events,audit=source_rows_to_events(archive_bytes,frozen_contract)
    train=[e for e in events if e.season_year<=2021 and not site_is_sealed(e.site_id)]
    future=[e for e in events if e.season_year>=2022 and site_is_sealed(e.site_id)]
    train_sites={e.site_id for e in train}
    future_sites={e.site_id for e in future}
    if train_sites&future_sites:
        raise ValueError("source/heldout physical site overlap")
    models,admission=fit_species_profiles(train)
    scored=[]
    out_of_support=0
    for event in future:
        if event.species not in models:
            out_of_support+=1
            continue
        scored.append((event,score_new_site_future_year(event,models[event.species])))
    result=summarize_site_level_transfer(scored)
    test_counts=Counter(event.season for event,row in scored)
    min_test_events=frozen_contract["design"]["minimum_heldout_events_per_season"]
    if not all(test_counts[s]>=min_test_events for s in ("winter","summer")):
        result["scientific_status"]="UNAVAILABLE_INSUFFICIENT_TEST_EVENTS"
        result["solar_transfer_both_seasons_positive"]=False
    if not result["all_season_site_floor_met"]:
        result["scientific_status"]="UNAVAILABLE_INSUFFICIENT_TEST_SITES"
        result["solar_transfer_both_seasons_positive"]=False
    return {
        "schema_version":1,
        "study_id":frozen_contract["study_id"],
        "status":result["scientific_status"],
        "published_archive_exploratory":True,
        "prior_outcomes_reclassified":False,
        "formal_untouched_external_claim":False,
        "observation_model_not_causal_behavior":True,
        "record_time_zone_verified":False,
        "train_physical_site_count":len(train_sites),
        "future_physical_site_count":len(future_sites),
        "train_physical_site_overlap_with_test":0,
        "test_events_after_training_only_species_admission":len(scored),
        "test_events_outside_training_species_support":out_of_support,
        "test_event_counts_by_season":dict(test_counts),
        "admission":admission,
        "source_audit":audit,
        "transferability":result,
    }
