#!/usr/bin/env python3
"""Outcome-blind Dryad Schaub 2026 external-source + BOP RF schema preflight.

No GPS rows, altitude outcomes, date-specific tracking, geolocations or
individual identifiers are read. Documented feature compatibility is
checked against the frozen original BOP_RF contract. Source access is
restricted to official Dryad API metadata and exactly three small
non-GPS sidecars; 403/missing content is a source HOLD, never a reason
to download Data_1a or Data_2a.
"""
from __future__ import annotations

from collections import Counter
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_CONTRACT.json"
ORIGINAL_BOP = ROOT / "BOP_RODENT_STATE_PREDICTION_CONTRACT.json"
EXPECTED_DOI = "10.5061/dryad.n8pk0p398"
EXPECTED_NAMES = (
    "README.md", "Study_areas_bounding_boxes.csv",
    "Complete_succesful_breeding_seasons.csv",
    "Data_1a.csv", "Data_2a.csv",
)
EXPECTED_SMALL_FILE_IDS = {4917192, 4917158, 4917159}
EXPECTED_DATADRYAD_API = (
    "https://datadryad.org/api/v2/datasets/"
    "doi%3A10.5061%2Fdryad.n8pk0p398"
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_contract(path: Path = CONTRACT) -> dict:
    contract = json.loads(path.read_text(encoding="utf-8"))
    candidate = contract.get("candidate", {})
    source = contract.get("source_probe", {})
    if (
        contract.get("contract_id") != "bop-dryad-2026-external-schema-and-source-preflight-v1"
        or contract.get("role") != "outcome_blind_external_source_and_predictor_compatibility_check_only"
        or contract.get("historical_bop_primary_terminal") != "empirical_state_prediction_mixed"
        or candidate.get("doi") != EXPECTED_DOI
        or candidate.get("api_dataset_url") != EXPECTED_DATADRYAD_API
        or candidate.get("api_versions_url") != EXPECTED_DATADRYAD_API + "/versions"
        or tuple(x.get("name") for x in candidate.get("expected_files", [])) != EXPECTED_NAMES
        or {x["file_stream_id"] for x in candidate["expected_files"] if "file_stream_id" in x} != EXPECTED_SMALL_FILE_IDS
        or any(x.get("download_allowed") is not False for x in candidate["expected_files"][3:])
        or source.get("allow_hosts") != ["datadryad.org"]
        or source.get("allow_small_file_ids") != [4917192, 4917158, 4917159]
        or source.get("no_large_gps_download") is not True
        or source.get("no_mirror_substitution_after_failure") is not True
        or contract.get("decision",{}).get("no_reclassification_of_archived_BOP_or_closed_2026_version_gate") is not True
    ):
        raise ValueError("Dryad preflight contract selection or scientific roles changed")
    if sum(candidate["readme_public_metadata"]["species_counts"].values()) != 280:
        raise ValueError("official published species total no longer matches 280")
    return contract


def feature_compatibility(contract: dict, original_contract: dict) -> dict[str,object]:
    """Check only the *documented* Dryad CSV schema, not real GPS values."""
    if original_contract.get("contract_id") != "bop-rodent-state-prediction-v1":
        raise ValueError("original historical BOP model contract mismatch")
    if original_contract["models"]["primary"]["name"] != "random_forest":
        raise ValueError("original BOP primary learner changed")
    original = tuple(original_contract["source"]["required_columns"])
    declared = tuple(contract["dryad_data_1a_documented_columns"])
    listed = {row["bop"]: row for row in contract["frozen_feature_crosswalk"]}
    if (
        len(original) != 7 or len(set(original)) != len(original)
        or len(declared) != len(set(declared))
        or set(original) != set(listed)
    ):
        raise ValueError("source feature roster/crosswalk was altered")
    statuses = {}
    mapped = {}
    for col in original:
        cross = listed[col]
        mapped[col] = cross["dryad"]
        if cross["dryad"] is None:
            if cross["condition"] != "required_original_BOP_RF_feature_missing":
                raise ValueError("missing required original BOP predictor incorrectly labeled")
            statuses[col] = "documented_absent"
        else:
            if cross["dryad"] not in declared:
                raise ValueError("claimed Dryad field absent from pinned README schema")
            statuses[col] = cross["condition"]
    if (
        statuses["external-temperature"] != "documented_absent"
        or statuses["location-long"] != "rounded_coordinates_not_original_precision"
        or statuses["location-lat"] != "rounded_coordinates_not_original_precision"
        or statuses["height-above-msl"] != "raw_AMSL_data_1a_only_no_outcome_opened"
        or contract["candidate"]["readme_public_metadata"]["source_coordinates_rounded_degrees"] != 0.1
        or original_contract["prediction_target"]["semantic_limit"] != "absolute altitude state, not height above ground level"
    ):
        raise ValueError("historical feature/altitude semantics were loosened")
    return {
        "original_bop_rf_direct_external_scoring_admissible": False,
        "reason": "required external-temperature absent from documented Data_1a predictors; locations rounded to 0.1 degrees; individual ID crosswalk unverified",
        "original_required_feature_count": len(original),
        "documented_missing_required_features": ["external-temperature"],
        "precision_changed_features": ["location-lat", "location-long"],
        "source_column_correspondences": statuses,
        "data_1a_altitude_semantics": "documented_raw_height_above_MSL_not_height_above_ground",
        "data_2a_semantics": "in_flight_only_corrected_AMSL_not_directly_exchangeable_with_BOP",
        "published_total_280_not_independent_external_BOP_units": True,
        "original_RF_rerun_performed": False,
        "schema_only_not_verified_against_raw_GPS_header": True,
    }


def _strict_official_url(url: str, *, small_id: int|None) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "datadryad.org":
        raise ValueError("only the pinned official Dryad HTTPS host is authorized")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("credentials/fragments forbidden in source URL")
    if small_id is None:
        if url not in (EXPECTED_DATADRYAD_API, EXPECTED_DATADRYAD_API + "/versions"):
            raise ValueError("only frozen Dryad dataset/versions metadata API allowed")
    else:
        if small_id not in EXPECTED_SMALL_FILE_IDS:
            raise ValueError("GPS/source-data file ID cannot be downloaded")
        if url != f"https://datadryad.org/downloads/file_stream/{small_id}":
            raise ValueError("only pinned small non-GPS file_stream URLs allowed")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("source URL redirected; record HOLD instead of fetching unpinned destination")


def _bounded_official_get(url: str, max_bytes: int, *, small_id: int|None = None) -> bytes:
    _strict_official_url(url, small_id=small_id)
    if not 0 < max_bytes <= 131072:
        raise ValueError("source byte limit must be positive and <=131072")
    opener = urllib.request.build_opener(_NoRedirect())
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "odsp-bop-dryad-source-preflight/1.0",
            "Accept": "application/json" if small_id is None else "text/plain,text/csv",
        },
        method="GET",
    )
    with opener.open(req, timeout=20) as response:
        raw = response.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError("metadata/non-GPS sidecar larger than frozen byte limit")
    if not raw:
        raise ValueError("empty official source response")
    return raw


def _safe_source_attempt(url: str, max_bytes: int, *, small_id: int|None = None,
                         fetcher=None) -> tuple[dict[str,object], bytes|None]:
    """Never release source IDs, locations or raw contents in public summary."""
    reader = fetcher or _bounded_official_get
    try:
        raw = reader(url, max_bytes, small_id=small_id)
    except Exception as exc:
        if isinstance(exc, urllib.error.HTTPError):
            error = f"HTTP_{exc.code}"
        elif isinstance(exc, (TimeoutError, urllib.error.URLError)):
            error = "PROVIDER_TIMEOUT_OR_NETWORK_HOLD"
        elif isinstance(exc, ValueError):
            error = "UNEXPECTED_REDIRECT_OR_SOURCE_POLICY_HOLD"
        else:
            error = type(exc).__name__
        return {"status":"SOURCE_HOLD", "error_code":error, "bytes_verified":False},None
    if not isinstance(raw, bytes) or not raw or len(raw) > max_bytes:
        return {"status":"SOURCE_HOLD","error_code":"INVALID_SOURCE_BYTES","bytes_verified":False},None
    return {"status":"SOURCE_READ", "bytes_verified":True, "size_bytes":len(raw),"sha256":_sha(raw)},raw


def _parse_small_non_gps_file(name: str, raw: bytes|None) -> dict[str,object]:
    if raw is None:
        return {"status":"UNAVAILABLE"}
    if name=="README.md":
        try:
            txt=raw.decode("utf-8-sig")
        except UnicodeError:
            return {"status":"SCHEMA_HOLD","reason":"non_UTF8_README"}
        return {"status":"READ","header_mentions_data_1a":"Data_1a" in txt,
                "header_mentions_data_2a":"Data_2a" in txt}
    if name=="Study_areas_bounding_boxes.csv":
        try:
            reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            if "bb_name_2" not in (reader.fieldnames or []):
                return {"status":"SCHEMA_HOLD","reason":"area_column_missing"}
            rows=list(reader)
            areas={x["bb_name_2"].strip() for x in rows if x.get("bb_name_2")}
        except (UnicodeError, csv.Error, AttributeError):
            return {"status":"SCHEMA_HOLD","reason":"invalid_study_area_csv"}
        return {"status":"READ","record_count":len(rows),"distinct_study_area_labels":len(areas),
                "not_independent_ecological_populations":True}
    if name=="Complete_succesful_breeding_seasons.csv":
        try:
            reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            if "individual.global.identifier" not in (reader.fieldnames or []):
                return {"status":"SCHEMA_HOLD","reason":"breeding_subset_id_column_missing"}
            rows=list(reader)
            known={x["individual.global.identifier"].strip() for x in rows
                   if x.get("individual.global.identifier")}
        except (UnicodeError,csv.Error,AttributeError):
            return {"status":"SCHEMA_HOLD","reason":"invalid_breeding_subset_csv"}
        return {"status":"READ","subset_rows":len(rows),
                "subset_distinct_individual_ids":len(known),
                "not_whole_dataset_roster":True,"not_proof_of_BOP_independence":True}
    raise ValueError("only three frozen non-GPS sidecars are permitted")


def run_preflight(*, contract_path: Path=CONTRACT, original_bop_path: Path=ORIGINAL_BOP,
                  fetcher=None) -> dict[str,object]:
    raw_contract=contract_path.read_bytes()
    contract=load_contract(contract_path)
    original=json.loads(original_bop_path.read_text(encoding="utf-8"))
    feature=feature_compatibility(contract,original)
    candidate=contract["candidate"]
    api_attempts={}
    for kind,url in [("dataset",candidate["api_dataset_url"]),("versions",candidate["api_versions_url"])]:
        result,raw=_safe_source_attempt(url,131072,fetcher=fetcher)
        if raw is not None:
            try:
                payload=json.loads(raw)
            except (UnicodeError,ValueError):
                result["json_status"]="INVALID_JSON"
            else:
                if isinstance(payload,dict):
                    result["json_status"]="VALID_JSON"
                    # No author email, exact site names, original IDs, abstracts
                    # or non-whitelisted provider fields are exported.
                    license_value=payload.get("license")
                    if isinstance(license_value,str) and len(license_value)<150:
                        result["explicit_provider_license"]=license_value
                    result["top_level_key_count"]=len(payload)
                else:
                    result["json_status"]="VALID_JSON_OTHER_TYPE"
        api_attempts[kind]=result
    sidecars={}
    for spec in candidate["expected_files"][:3]:
        name=spec["name"]
        id_=int(spec["file_stream_id"])
        result,raw=_safe_source_attempt(
            f"https://datadryad.org/downloads/file_stream/{id_}",
            spec["max_download_bytes"],small_id=id_,fetcher=fetcher
        )
        result["parsed_non_gps"]= _parse_small_non_gps_file(name,raw)
        sidecars[name]=result
    any_success=any(x["status"]=="SOURCE_READ" for x in api_attempts.values()) or any(
        x["status"]=="SOURCE_READ" for x in sidecars.values()
    )
    return {
        "schema_version":1,
        "contract_id":contract["contract_id"],
        "contract_sha256":_sha(raw_contract),
        "dataset_doi":EXPECTED_DOI,
        "first_public_readme_date":candidate["published"],
        "documented_species_total":candidate["readme_public_metadata"]["dataset_total_tagged_individuals"],
        "documented_common_BOP_taxa_total":sum(
            candidate["readme_public_metadata"]["species_counts"][k] for k in (
                "Circus pygargus","Circus cyaneus","Circus aeruginosus","Buteo buteo"
            )
        ),
        "documented_data_1a_individuals":candidate["readme_public_metadata"]["data_1a_distinct_individuals"],
        "documented_data_2a_individuals":candidate["readme_public_metadata"]["data_2a_distinct_individuals"],
        "feature_compatibility":feature,
        "official_metadata_api":api_attempts,
        "small_non_gps_file_checks":sidecars,
        "metadata_source_status":"AT_LEAST_ONE_OFFICIAL_SOURCE_READ" if any_success else "OFFICIAL_METADATA_SOURCE_HOLD",
        "individual_cross_study_identity_overlap_status":"UNKNOWN_NOT_EVALUABLE_WITH_PUBLISHED_COUNTS",
        "original_BOP_RF_direct_external_transfer_status":"ORIGINAL_RF_PREDICTOR_INCOMPATIBLE",
        "new_model_prospective_freeze_required":True,
        "candidate_admission":"NOT_ADMITTED",
        "raw_gps_or_height_outcomes_accessed":False,
        "BOP_existing_mixed_terminal_reclassified":False,
        "BOP_2026_same_study_count_gate_reopened":False,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=None)
    args=parser.parse_args()
    report=run_preflight()
    data=json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)+"\n"
    if args.out:
        if args.out.resolve() in (CONTRACT.resolve(),ORIGINAL_BOP.resolve()):
            raise ValueError("no frozen scientific contract may be overwritten")
        args.out.write_text(data,encoding="utf-8")
    print(json.dumps({
        "candidate_admission":report["candidate_admission"],
        "source_status":report["metadata_source_status"],
        "original_RF":report["original_BOP_RF_direct_external_transfer_status"],
        "gps_accessed":report["raw_gps_or_height_outcomes_accessed"],
        "api_dataset":report["official_metadata_api"]["dataset"]["status"],
        "small_files":{k:v["status"] for k,v in report["small_non_gps_file_checks"].items()},
    },sort_keys=True))


if __name__=="__main__":
    main()
