#!/usr/bin/env python3
"""Strict, two-source, NO-GPS marsh-harrier reference-only eligibility check.

v1 contract: committed before any reference CSV was opened. Actual provider
headers fail the predeclared alias schema -> SOURCE_SCHEMA_HOLD; do not
retroactively rewrite that historical decision.
v2: explicitly post-header, outcome-blind reconciliation of the fields
animal-id, animal-taxon and tag-id using the exact source MD5s.

Outputs aggregate counts and source cryptographic digests ONLY; no animal IDs,
tags, names, coordinates, GPS fixes or model predictions are ever published.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Mapping
import urllib.request
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
V1_PATH=ROOT/"research/BOP_TWO_MARSH_REFERENCE_ONLY_V1_CONTRACT.json"
V2_PATH=ROOT/"research/BOP_TWO_MARSH_REFERENCE_ONLY_V2_POSTHEADER_CONTRACT.json"

_RECORDS=("MH_WATERLAND","H_GRONINGEN")
_ALIAS_CANDIDATES={
    "animal":("individual-local-identifier","individual-id","individual.id","individual_id"),
    "species":("individual-taxon-canonical-name","taxon","species","individual.taxon.canonical.name"),
    "tag":("tag-local-identifier","tag-id","tag.id"),
}
_V2_COLUMNS=("animal-id","animal-taxon","tag-id","alt-project-id")
_HEX32=re.compile(r"^[0-9a-f]{32}$")


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def _contract():
    v1=json.loads(V1_PATH.read_text(encoding="utf-8"))
    v2=json.loads(V2_PATH.read_text(encoding="utf-8"))
    records=v1.get("fixed_archive_versions")
    if (
        v1.get("contract_id")!="bop-two-marsh-harrier-archive-reference-only-v1"
        or v1.get("frozen_date")!="2026-10-28"
        or len(records or [])!=2
        or [r.get("study") for r in records]!=list(_RECORDS)
        or v1.get("access_constraints",{}).get("no_GPS_event_files") is not True
        or v1.get("target_miscoverage")!=0.1
        or v1.get("min_new_calibration_entities_per_stratum")!=9
        or v1.get("min_new_untouched_validation_entities_per_stratum")!=1
        or v2.get("contract_id")!="bop-two-marsh-reference-schema-observed-v2"
        or v2.get("created_after_source_header_access") is not True
        or v2.get("v1_schema_mismatch","").startswith("SOURCE_SCHEMA_HOLD") is not True
        or v2.get("source_csv_required_columns")!=list(_V2_COLUMNS)
    ):
        raise ValueError("source-only frozen contracts changed")
    allowed=v1["source_access_allowlist"]
    if len(allowed)!=2:
        raise ValueError("source allowlist must contain exactly two reference CSVs")
    for r,url in zip(records,allowed):
        vs=v2["only_allowed_zenodo_record_and_filename"].get(r["study"],{})
        expected=f"https://zenodo.org/records/{r['record_id']}/files/{r['reference_filename']}"
        if (
            url!=expected or r["reference_md5"]!=vs.get("md5")
            or r["record_id"]!=vs.get("record_id")
            or r["reference_filename"]!=vs.get("filename")
            or not _HEX32.fullmatch(r["reference_md5"])
            or "gps" in url.lower() or "acceleration" in url.lower()
        ):
            raise ValueError("provider source identifier or whitelist mismatch")
    return v1,v2


def _bounded_provider_fetch(url:str, byte_cap:int)->bytes:
    if not (url.startswith("https://zenodo.org/records/") and
            url.endswith("-reference-data.csv")):
        raise ValueError("only pinned Zenodo reference-data CSV URL allowed")
    request=urllib.request.Request(
        url+"?download=1",
        headers={"User-Agent":"ODSP-source-only-reference-preflight/1.0",
                 "Accept":"text/csv,text/plain,application/octet-stream"},
    )
    with urllib.request.urlopen(request,timeout=30) as response:
        final=response.geturl()
        parsed=urlparse(final)
        if parsed.scheme!="https" or parsed.netloc not in ("zenodo.org","www.zenodo.org"):
            raise ValueError("unexpected provider redirect host")
        if not (
            parsed.path==urlparse(url).path
            or (parsed.path.startswith("/api/records/") and parsed.path.endswith("/content"))
        ):
            raise ValueError("source redirected outside exact reference file")
        payload=response.read(byte_cap+1)
    if not payload or len(payload)>byte_cap:
        raise ValueError("reference file missing or exceeds source-only byte cap")
    return payload


def _rows(payload:bytes, *, expected_md5:str)->tuple[tuple[str,...],list[dict]]:
    if not isinstance(payload,bytes) or len(payload)>10_000 or not payload:
        raise ValueError("only small nonempty reference CSV byte strings allowed")
    if hashlib.md5(payload).hexdigest()!=expected_md5:
        raise ValueError("reference CSV MD5 mismatch; do not open or classify")
    try:
        decoded=payload.decode("utf-8-sig")
        reader=csv.DictReader(io.StringIO(decoded))
        header=reader.fieldnames
        if not header or len(header)!=len(set(header)):
            raise ValueError("reference CSV has no unique header")
        if any(not col or col!=col.strip() for col in header):
            raise ValueError("reference CSV header malformed")
        data=list(reader)
    except UnicodeDecodeError as exc:
        raise ValueError("reference CSV is not UTF-8") from exc
    if any(None in row for row in data):
        raise ValueError("reference CSV contains undeclared extra fields")
    return tuple(header),data


def _summarize(name:str,header:tuple[str,...],data:list[dict])->tuple[dict,set[str],set[str]]:
    if any(col not in header for col in _V2_COLUMNS):
        raise ValueError("post-header v2 cannot parse required source fields")
    distinct:dict[str,str]={}
    tag_animal:dict[str,set[str]]={}
    tags=set()
    for row in data:
        animal=row["animal-id"]
        taxon=row["animal-taxon"]
        tag=row["tag-id"]
        project=row["alt-project-id"]
        if any(not isinstance(x,str) or not x or x!=x.strip() for x in (animal,taxon,tag,project)):
            raise ValueError("empty or malformed animal/reference tag record")
        if project!=name:
            raise ValueError("reference project does not match fixed study")
        if animal in distinct and distinct[animal]!=taxon:
            raise ValueError("same animal ID has inconsistent species")
        distinct[animal]=taxon
        tag_animal.setdefault(tag,set()).add(animal)
        tags.add(tag)
    if any(species!="Circus aeruginosus" for species in distinct.values()):
        raise ValueError("fixed sources contain unexpected species; require new contract")
    reused={tag for tag,animals in tag_animal.items() if len(animals)>1}
    return ({
        "study":name,
        "source_reference_rows":len(data),
        "unique_species_animals":len(distinct),
        "unique_tag_identifiers":len(tags),
        "different_animals_sharing_a_tag_count":len(reused),
        "largest_number_of_animals_per_reused_tag":max((len(tag_animal[t]) for t in reused),default=0),
        "one_study_can_supply_9_calibration_plus_1_validation":
            len(distinct)>=10,
        "no_raw_identity_fields_exported":True,
    },set(distinct),set(tags))


def classify_checked_reference_bytes(
    inputs:Mapping[str,bytes], *, v1:dict, v2:dict,
)->dict:
    """MD5-verify both source CSVs BEFORE inspecting field values."""
    archive=v1["fixed_archive_versions"]
    if set(inputs)!=set(_RECORDS):
        raise ValueError("exact two whitelisted reference files required")
    verified={}
    for entry in archive:
        name=entry["study"]
        payload=inputs[name]
        header,rows=_rows(payload,expected_md5=entry["reference_md5"])
        verified[name]={"header":header,"rows":rows,"bytes":len(payload),"sha256":_sha(payload)}
    # V1 is a TERMINAL SCIENTIFIC RECORD: original aliases do not contain
    # the actual provider fields. This is NOT reparsed as precommitted success.
    v1_aliases=v1["metadata_schema_policy"]
    match=all(
        any(col in item["header"] for col in v1_aliases[key])
        for item in verified.values()
        for key in ("required_individual_field_candidates",
                    "required_species_field_candidates",
                    "required_tag_field_candidates")
    )
    v1_status="V1_SOURCE_SCHEMA_MATCHED" if match else "SOURCE_SCHEMA_HOLD"
    if v1_status!="SOURCE_SCHEMA_HOLD":
        raise ValueError("v1 source schema unexpectedly changed after header access")
    summaries=[]
    animals={}
    tags={}
    for entry in archive:
        name=entry["study"]
        source=verified[name]
        counts,an,ta=_summarize(name,source["header"],source["rows"])
        counts["official_reference_md5_verified"]=True
        counts["reference_sha256"]=source["sha256"]
        counts["reference_byte_count"]=source["bytes"]
        counts["published_individual_count"]=entry["publicly_reported_species_individuals"]
        counts["reference_distinct_count_matches_publication"]=(counts["unique_species_animals"]==counts["published_individual_count"])
        summaries.append(counts)
        animals[name]=an
        tags[name]=ta
    overlap=animals[_RECORDS[0]]&animals[_RECORDS[1]]
    total=sum(len(v) for v in animals.values())-len(overlap)
    same_tag=tags[_RECORDS[0]]&tags[_RECORDS[1]]
    return {
        "schema_version":2,
        "role":"POST_HEADER_SOURCE_ONLY_IDENTITY_FEASIBILITY_NOT_PROSPECTIVE_VALIDATION",
        "original_v1_terminal":v1_status,
        "v1_contract_sha256":_sha(V1_PATH.read_bytes()),
        "v2_contract_sha256":_sha(V2_PATH.read_bytes()),
        "source_access":"TWO_MD5_VERIFIED_REFERENCE_CSV_FILES_ONLY",
        "studies":summaries,
        "identical_animal_id_strings_shared_across_studies":len(overlap),
        "identical_tag_id_strings_shared_across_studies":len(same_tag),
        "upper_bound_distinct_candidate_animals_by_exact_string":total,
        "within_study_rank_90pct_nonvacuous_any":any(x["one_study_can_supply_9_calibration_plus_1_validation"] for x in summaries),
        "hypothetical_pooled_count_at_least_10":total>=10,
        "study_cluster_count":len(_RECORDS),
        "status":"REFERENCE_ID_AND_TAG_REUSE_AUDIT_ONLY",
        "external_rank_admission_status":"HOLD_POPULATION_AND_IDENTITY_EXCHANGEABILITY_UNVERIFIED",
        "actual_same_animal_under_different_IDs_not_excluded":True,
        "source_id_string_overlap_not_proof_of_biological_independence":True,
        "historical_MH_ANTWERPEN_already_opened_and_excluded":True,
        "raw_animal_tag_IDs_in_result":False,
        "GPS_height_or_location_events_accessed":False,
        "original_BOP_RF_retrained":False,
        "original_BOP_terminal":"empirical_state_prediction_mixed",
        "Dryad_original_RF_gate":"ORIGINAL_RF_PREDICTOR_INCOMPATIBLE",
        "new_external_prediction_claim":False,
    }


def first_source_only_result()->dict:
    v1,v2=_contract()
    cap=int(v1["access_constraints"]["file_size_cap_bytes_each"])
    payloads={}
    for entry,url in zip(v1["fixed_archive_versions"],v1["source_access_allowlist"]):
        payloads[entry["study"]]=_bounded_provider_fetch(url,cap)
    return classify_checked_reference_bytes(payloads,v1=v1,v2=v2)


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    try:
        result=first_source_only_result()
    except (OSError,ValueError) as exc:
        # Fail closed; never leak source lines, URLs with identifiers or
        # source response bodies. Preserve the first run on access failure.
        result={
            "schema_version":2,
            "source_access":"SOURCE_ACCESS_OR_SCHEMA_HOLD",
            "error_category":type(exc).__name__,
            "GPS_height_or_location_events_accessed":False,
            "new_external_prediction_claim":False,
            "historical_BOP_terminal":"empirical_state_prediction_mixed",
            "reason":"source-byte integrity, schema or provider access gate failed",
        }
    out=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    if args.out:
        if args.out.resolve() in (V1_PATH.resolve(),V2_PATH.resolve()):
            raise ValueError("cannot overwrite frozen source contracts")
        args.out.write_text(out,encoding="utf-8")
    print(json.dumps({
        "source_access":result["source_access"],
        "v1_terminal":result.get("original_v1_terminal","SOURCE_ACCESS_HOLD"),
        "v2_status":result.get("status","SOURCE_ACCESS_HOLD"),
        "candidate_upper_bound":result.get("upper_bound_distinct_candidate_animals_by_exact_string"),
        "no_GPS":result["GPS_height_or_location_events_accessed"] is False,
    },sort_keys=True))
    if result["source_access"]!="TWO_MD5_VERIFIED_REFERENCE_CSV_FILES_ONLY":
        raise SystemExit("PUBLIC SOURCE ACCESS/INTEGRITY HOLD, no biological outcomes opened")


if __name__=="__main__":
    main()
