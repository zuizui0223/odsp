#!/usr/bin/env python3
"""Current anonymous Movebank *study summary* metadata preflight for German red kites.

Study-scope only (294443150), does not download reference entities, animal IDs,
tags, deployments, GPS fixes or breeding response values. Current provider
summary must NEVER be used as a 2024 sample roster or group-gain result.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_RED_KITE_GER_MOVEBANK_STUDY_METADATA_V1_CONTRACT.json"
ALLOWED_URL=("https://www.movebank.org/movebank/service/direct-read"
             "?entity_type=study&study_id=294443150")

def load_frozen():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    s=c["narrow_source"]
    p=c["paper"]
    z=c["safety"]
    d=c["decisions"]
    if (
        c.get("contract_id")!="bop-red-kite-Movebank-DE-study-public-metadata-v1"
        or c.get("preaccess_freeze_date")!="2026-11-18"
        or p.get("doi")!="10.1111/jav.03246"
        or p.get("Movebank_study_ids_as_published")!=[230545451,1356790386,294443150]
        or s.get("study_id")!=294443150
        or s.get("url")!=ALLOWED_URL
        or s.get("method")!="GET"
        or s.get("account_authentication")!="NONE"
        or s.get("max_response_bytes")!=65536
        or s.get("response_format")!="CSV_OR_PLAINTEXT_HOLD"
        or d.get("historical_BOP_terminal")!="empirical_state_prediction_mixed"
        or d.get("redkite_prediction_terminal")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or d.get("never_reclassify_fixed_source_99_49_as_99_63") is not True
        or any(z.get(field) is not True for field in (
            "no_individual_reference_data","no_tag_deployment_csv",
            "no_GPS_or_other_event_data","no_nest_HR_success_labels",
            "no_identifying_animal_or_tag_keys","no_credentials_or_cookies_or_login",
            "no_accepting_licence_or_terms_on_behalf_of_user",
            "raw_response_and_contact_person_not_exported",
            "never_infer_historic_2024_count_from_2026_live_metadata"
        ))
    ):
        raise ValueError("frozen public-study-only access/claim boundary drifted")
    if sorted(s["whitelist_fields"])!=sorted([
        "id","name","number_of_individuals","number_of_deployments","number_of_tags",
        "number_of_deployed_locations","timestamp_first_deployed_location",
        "timestamp_last_deployed_location","i_can_see_data","i_have_download_access",
        "there_are_data_which_i_cannot_see","license_type","study_permission"
    ]):
        raise ValueError("live study output column whitelist changed")
    return c

def _bool_or_unknown(v):
    s=str(v or "").strip().lower()
    if s in ("true","1","yes"):return True
    if s in ("false","0","no"):return False
    return None

def _int_or_unknown(v):
    s=str(v or "").strip()
    if not s:return None
    try:
        n=int(s)
    except ValueError:
        return None
    return n if n>=0 else None

def classify_response(raw:bytes,code:int,source_url:str,contract:dict)->dict:
    """Return ONLY high-level public study counts and permission flags."""
    if source_url!=ALLOWED_URL:
        raise ValueError("disallowed Movebank endpoint; no alternate source URLs permitted")
    if not isinstance(raw,bytes) or len(raw)>contract["narrow_source"]["max_response_bytes"]:
        raise ValueError("provider study summary too large")
    body=raw.decode("utf-8-sig",errors="replace")
    low=body.lower()
    base={
        "schema_version":1,
        "source_role":"ANONYMOUS_LIVE_STUDY_SUMMARY_ONLY",
        "provider_record_id":294443150,
        "provider_response_sha256":hashlib.sha256(raw).hexdigest(),
        "HTTP_status":code,
        "current_not_historical_2024":True,
        "entire_GER_163_65_original_paper_roster_verified":False,
        "historical_99_63_eligible_birds_verified":False,
        "archived_GER_99_season_49_bird_ID_result_unchanged":True,
        "individual_tag_deployment_or_event_rows_accessed":False,
        "nesting_or_success_labels_accessed":False,
        "historical_BOP_terminal":"empirical_state_prediction_mixed",
        "redkite_prediction_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
    }
    if code!=200:
        return {**base,"status":"STUDY_METADATA_ACCESS_HOLD","reason":"HTTP_NON_200"}
    if any(q in low for q in ("no data available","contact the data owner",
                             "license terms:","accept-license","access denied","permission denied")):
        return {**base,"status":"STUDY_METADATA_ACCESS_HOLD","reason":"PROVIDER_PERMISSION_OR_TERMS"}
    if not raw or body.lstrip().startswith(("<html","<!doctype html","<p>")):
        return {**base,"status":"STUDY_METADATA_ACCESS_HOLD","reason":"NOT_PUBLIC_CSV"}
    try:
        table=list(csv.DictReader(io.StringIO(body),strict=True))
    except (csv.Error,UnicodeError):
        return {**base,"status":"STUDY_METADATA_SCHEMA_OR_ID_HOLD","reason":"INVALID_CSV"}
    if len(table)!=1 or "id" not in table[0]:
        return {**base,"status":"STUDY_METADATA_SCHEMA_OR_ID_HOLD","reason":"NOT_ONE_PUBLIC_STUDY"}
    row=table[0]
    if str(row.get("id") or "").strip()!="294443150":
        return {**base,"status":"STUDY_METADATA_SCHEMA_OR_ID_HOLD","reason":"WRONG_STUDY_ID"}
    # Raw provider columns can include names and emails; ONLY these explicitly
    # whitelisted safe summaries are emitted and no rows are retained in files.
    permitted=contract["narrow_source"]["whitelist_fields"]
    if "name" not in permitted:
        raise ValueError("study name not explicitly whitelisted")
    name=str(row.get("name") or "")
    if not name or "kite" not in name.lower() and "milvus" not in name.lower():
        return {**base,"status":"STUDY_METADATA_SCHEMA_OR_ID_HOLD","reason":"STUDY_NAME_UNEXPECTED"}
    return {
        **base,"status":"CURRENT_MOVEBANK_STUDY_METADATA_ONLY",
        "study_name_red_kite_matched":True,
        "current_total_provider_individuals":_int_or_unknown(row.get("number_of_individuals")),
        "current_total_provider_deployments":_int_or_unknown(row.get("number_of_deployments")),
        "current_total_provider_tags":_int_or_unknown(row.get("number_of_tags")),
        "current_total_provider_locations":_int_or_unknown(row.get("number_of_deployed_locations")),
        "public_can_view":_bool_or_unknown(row.get("i_can_see_data")),
        "anonymous_download_access":_bool_or_unknown(row.get("i_have_download_access")),
        "public_data_may_be_partial":_bool_or_unknown(row.get("there_are_data_which_i_cannot_see")),
        "current_study_summary_does_not_establish_2024_season_filter":True,
    }

def run()->dict:
    contract=load_frozen()
    source=contract["narrow_source"]
    req=Request(ALLOWED_URL,headers={
        "Accept":"text/csv,text/plain;q=0.9",
        "Accept-Encoding":"identity",
        "User-Agent":"ODSP-BOP-2026-study-summary-only/1.0",
    },method="GET")
    with urlopen(req,timeout=30) as r:
        url=urlparse(r.geturl())
        if (url.scheme!="https"
            or url.hostname not in ("www.movebank.org","movebank.org","www.movebank.mpg.de","movebank.mpg.de")
            or url.path!="/movebank/service/direct-read"
            or url.query!="entity_type=study&study_id=294443150"):
            raise ValueError("public study metadata redirected away from exact frozen study-summary endpoint")
        raw=r.read(source["max_response_bytes"]+1)
        if len(raw)>source["max_response_bytes"]:
            raise ValueError("study metadata exceeds frozen limit")
        return classify_response(raw,int(r.status),ALLOWED_URL,contract)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.out.resolve()==CONTRACT.resolve():
        raise ValueError("may not overwrite provider study preaccess contract")
    try:
        result=run()
    except (OSError,ValueError,HTTPError,URLError,UnicodeError) as exc:
        result={
            "schema_version":1,
            "status":"STUDY_METADATA_ACCESS_HOLD",
            "error_type":type(exc).__name__,
            "source_role":"ANONYMOUS_LIVE_STUDY_SUMMARY_ONLY",
            "provider_record_id":294443150,
            "current_not_historical_2024":True,
            "entire_GER_163_65_original_paper_roster_verified":False,
            "historical_99_63_eligible_birds_verified":False,
            "archived_GER_99_season_49_bird_ID_result_unchanged":True,
            "individual_tag_deployment_or_event_rows_accessed":False,
            "nesting_or_success_labels_accessed":False,
            "historical_BOP_terminal":"empirical_state_prediction_mixed",
            "redkite_prediction_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        }
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    if result["status"] not in ("CURRENT_MOVEBANK_STUDY_METADATA_ONLY",):
        raise SystemExit("MOVEBANK_STUDY_METADATA_HOLD: source cohort not admitted")

if __name__=="__main__":
    main()
