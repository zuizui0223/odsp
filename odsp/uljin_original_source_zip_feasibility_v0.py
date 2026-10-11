"""Original v1.1 EcoBank source ZIP feasibility: 41 fixed photoperiod pairs.

This module is deliberately limited to original event timestamp support.
It NEVER computes camera operating HOURS, time-refuge rates, latent
animal activity or causal ecological hypotheses from a source CSV alone.

A journal supplementary figure ZIP is NOT the original NIE EcoBank
Version 1.1 archive. The explicit external original-release attestation
and independently checked checksum are supplied by the investigator;
ZIP filenames and an internal manifest do not authenticate them.
No protected station coordinates are exported or reconstructed.
"""
from __future__ import annotations

from collections import Counter,defaultdict
from collections.abc import Mapping
from datetime import date
import csv
import hashlib
import io
from pathlib import Path
import re
import zipfile

from .uljin_ecological_temporal_refuge_v0 import (
    TAXA,BRANCHES,ZONES,assert_frozen_ecology,
    parse_clock_minutes,classify_event_time
)
from .uljin_photoperiod_mirror_design_v0 import (
    generate_preoutcome_2022_mirror_calendar
)

METHOD="uljin_original_v1p1_archive_41pairs_four_taxon_feasibility_v0"
MEMBERS=(
    "01_core_data/cameratrap_event_records.csv",
    "01_core_data/camera_operation_log.csv",
    "01_core_data/site_covariates_public.csv",
    "03_documentation/MANIFEST.tsv",
)
HEADERS=("Station","Species","scientificName","Date","Time")
MAX_ARCHIVE_UNCOMPRESSED_BYTES=150_000_000
TIME="Asia/Seoul"


def freeze_source_feasibility(
    plan:Mapping[str,object],biology:Mapping[str,object],
    calendar:Mapping[str,object]
)->tuple[list[dict[str,str]],dict[str,str]]:
    if (not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
            "PRE_ORIGINAL_SOURCE_ZIP_OUTCOME_FROZEN_AFTER_ECOLOGICAL_H1_H2_IMPLEMENTATION"
        or plan.get("necessary_exact_zip_members")!=list(MEMBERS)
        or plan.get("expected_original_event_columns")!=list(HEADERS)
        or plan.get("original_four_species")!=list(TAXA)
        or plan.get("original_date_pairs")!=41
        or plan.get("min_events_each_branch_support_guard")!=30
        or plan.get("min_source_event_both_branch_stations_exploratory_guard")!=8):
        raise ValueError("frozen source original Version 1.1 feasibility gate changed")
    by_date=assert_frozen_ecology(biology,calendar)
    pairs=generate_preoutcome_2022_mirror_calendar(calendar)["matched_dates"]
    if len(pairs)!=41 or len(by_date)!=82:
        raise ValueError("original astronomy matched dates changed")
    return pairs,by_date


def _sha256(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


def _csv_member(z:zipfile.ZipFile,path:str)->tuple[list[str],list[dict[str,str]]]:
    raw=z.read(path)
    try:
        text=raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("original v1.1 member has non-UTF8 source bytes") from exc
    reader=csv.DictReader(io.StringIO(text,newline=""))
    header=reader.fieldnames
    if not header or len(set(header))!=len(header):
        raise ValueError("original source member headers missing or duplicated")
    records=list(reader)
    if any(None in record for record in records):
        raise ValueError("unexpected extra source CSV columns")
    return header,records


def read_original_source_feasibility(
    plan:Mapping[str,object],biology:Mapping[str,object],
    calendar:Mapping[str,object],
    archive:Path|None,
    *,
    externally_verified_original_v1p1:bool=False,
    externally_verified_archive_sha256:str|None=None,
)->dict[str,object]:
    pairs,by_date=freeze_source_feasibility(plan,biology,calendar)
    if (archive is None or externally_verified_original_v1p1 is not True
        or externally_verified_archive_sha256 is None):
        return {
            "status":"HOLD_NOT_ORIGINAL_SOURCE_INPUT_AND_CHECKSUM_ATTESTED",
            "source_original_member_read":False,
            "fixed_calendar_pairs":41,
            "four_taxa_preserved":list(TAXA),
            "real_hourly_operating_hours_computed":False
        }
    if not re.fullmatch(r"[0-9a-f]{64}",externally_verified_archive_sha256):
        raise ValueError("independently documented original archive SHA256 required")
    if not isinstance(archive,Path) or not archive.is_file():
        raise ValueError("attested archive path does not exist")
    digest=_sha256(archive)
    if digest!=externally_verified_archive_sha256:
        return {
            "status":"HOLD_SOURCE_ORIGINAL_ARCHIVE_CHECKSUM_MISMATCH",
            "source_original_member_read":False,
            "sha256_matches_independent_external_attestation":False
        }
    if not zipfile.is_zipfile(archive):
        raise ValueError("original v1.1 EcoBank input must be a ZIP archive")
    with zipfile.ZipFile(archive) as z:
        infos=z.infolist()
        paths={info.filename for info in infos}
        if len(paths)!=len(infos) or any(
            info.filename.startswith("/")
            or ".." in Path(info.filename).parts
            or "\\" in info.filename
            for info in infos):
            raise ValueError("duplicate/unsafe ZIP member paths")
        if sum(info.file_size for info in infos)>MAX_ARCHIVE_UNCOMPRESSED_BYTES:
            raise ValueError("untrusted archive too large for original public CSV ingestion")
        missing=[path for path in MEMBERS if path not in paths]
        if missing:
            return {
                "status":"HOLD_REQUIRED_ORIGINAL_V1P1_MEMBERS_ABSENT",
                "source_original_member_read":False,
                "missing_original_members":missing,
                "sha256_matches_independent_external_attestation":True,
            }
        eh,events=_csv_member(z,MEMBERS[0])
        oh,operations=_csv_member(z,MEMBERS[1])
        ch,covariates=_csv_member(z,MEMBERS[2])
        if not set(HEADERS).issubset(eh):
            raise ValueError("original public event member missing published header schema")
        # MANIFEST is preserved but not interpreted as cryptographic
        # source attestation; source record's external sha256 is decisive.
        manifest_size=z.getinfo(MEMBERS[3]).file_size
        if manifest_size==0:
            raise ValueError("original v1.1 manifest empty")
    # Keep source sensitive station coordinates OUT of result: only
    # released event Station labels and aggregate counts as needed.
    matched=Counter()
    species_pair_station=defaultdict(lambda:defaultdict(set))
    species_pair_dates=defaultdict(lambda:defaultdict(set))
    site_branch=defaultdict(set)
    species_branch=Counter()
    zones=Counter()
    invalid_rows=0
    excluded_outside=0
    for event in events:
        try:
            day_text=event["Date"]
            day=date.fromisoformat(day_text)
            if day.isoformat()!=day_text:
                raise ValueError("non-ISO source event date")
            station=event["Station"]
            if not isinstance(station,str) or not station.strip():
                raise ValueError("missing original physical camera station")
            sp=event["Species"]
            if sp not in TAXA:
                raise ValueError("unknown original focal ungulate species")
            minute=parse_clock_minutes(event["Time"])
        except (ValueError,TypeError) as exc:
            invalid_rows+=1
            raise ValueError("original event source contains invalid species/date/clock") from exc
        if day_text not in by_date:
            excluded_outside+=1
            continue
        branch=by_date[day_text]
        zone=classify_event_time(day,minute)
        species_branch[(sp,branch)]+=1
        zones[(sp,branch,zone)]+=1
        site_branch[(sp,branch)].add(station)
        matched[(station,day_text,sp)]+=1
    rowsets=[]
    for sp in TAXA:
        rising_sites=site_branch[(sp,"rising")]
        falling_sites=site_branch[(sp,"falling")]
        both_sites=rising_sites&falling_sites
        pair_count=0
        station_pair_count=0
        for p in pairs:
            a,b=p["ascending_date"],p["descending_date"]
            any_a=any(matched[(station,a,sp)]>0 for station in both_sites)
            any_b=any(matched[(station,b,sp)]>0 for station in both_sites)
            if any_a and any_b:
                pair_count+=1
            station_pair_count+=sum(
                matched[(station,a,sp)]>0 and matched[(station,b,sp)]>0
                for station in both_sites
            )
        n0=species_branch[(sp,"rising")]
        n1=species_branch[(sp,"falling")]
        rowsets.append({
            "Species":sp,
            "rising_early_growing_season_original_events":n0,
            "falling_midsummer_original_events":n1,
            "unique_stations_with_events_in_rising_branch":len(rising_sites),
            "unique_stations_with_events_in_falling_branch":len(falling_sites),
            "unique_stations_with_source_events_in_BOTH_branches":len(both_sites),
            "original_mirrored_date_pairs_with_events_both_dates_at_any_shared_station":pair_count,
            "station_x_matched_date_pair_both_dates_positive_event_cells":station_pair_count,
            "rising_daylight_core_events":zones[(sp,"rising","daylight_core")],
            "rising_daylight_edge_events":zones[(sp,"rising","daylight_edge")],
            "rising_night_events":zones[(sp,"rising","night")],
            "falling_daylight_core_events":zones[(sp,"falling","daylight_core")],
            "falling_daylight_edge_events":zones[(sp,"falling","daylight_edge")],
            "falling_night_events":zones[(sp,"falling","night")],
            "LOW_SUPPORT_event_only_exploratory_guard":(
                min(n0,n1)<30 or len(both_sites)<8
            ),
            "NO_EFFORT_DENOMINATOR_AND_NO_REAL_BEHAVIORAL_TEST":True,
        })
    return {
        "status":"SOURCE_ATTESTED_ORIGINAL_EVENT_TIMESTAMP_FEASIBILITY_ONLY",
        "original_archive_sha256":digest,
        "original_v1p1_archive_externally_verified":True,
        "original_data_member_headers":{
            "event":eh,"operation":oh,"station_covariates":ch
        },
        "original_data_member_row_counts":{
            "event":len(events),"operation":len(operations),
            "station_covariates":len(covariates)
        },
        "source_event_rows_OUTSIDE_original_82_day_calendar":excluded_outside,
        "source_event_rows_ON_original_82_day_calendar":sum(species_branch.values()),
        "invalid_event_rows":invalid_rows,
        "original_41_calendar_pairs_UNCHANGED":True,
        "source_species_branch_original_timestamp_support":rowsets,
        "hourly_operation_source_columns_only_not_verified_or_normalized":True,
        "camera_hours_did_NOT_get_inferred_from_trap_nights":True,
        "real_animal_daytime_refuge_rate_or_source_site_significance_computed":False,
        "original_station_exact_GPS_not_exported":True,
        "source_release_license_requires_KOGL_attribution":True,
    }
