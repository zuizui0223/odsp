#!/usr/bin/env python3
"""BOP_RODENT v3 vs 2026 VERSION source-only reference roster preflight.

Downloads only the two checksum-pinned Zenodo BOP_RODENT-reference-data.csv
members. Absolutely no GPS, altitude, observation-time or animal outcome
events are opened. Public JSON contains only aggregate counts and hashes.
"""
from __future__ import annotations

from collections import Counter
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib import request
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_CONTRACT.json"
EXPECTED_IDS = (10055071, 17310324)
EXPECTED_MD5S = (
    "81e85243e38823db4bde56e315b596f8",
    "fc4623f4dd5f32ef228b3dae386b2c1a",
)


def contract_from_bytes(raw: bytes) -> dict:
    contract = json.loads(raw)
    sources = contract.get("source_versions")
    if (
        contract.get("contract_id") != "bop-v3-v6-reference-only-roster-gate-v1"
        or contract.get("scientific_role") != "outcome_blind_source_identity_admission_preflight_not_empirical_prediction"
        or contract.get("original_frozen_terminal") != "empirical_state_prediction_mixed"
        or contract.get("movebank_study_id") != 1278021460
        or not isinstance(sources,list)
        or tuple(s["record_id"] for s in sources) != EXPECTED_IDS
        or tuple(s["md5"] for s in sources) != EXPECTED_MD5S
        or contract.get("only_authorized_download") != (
            "two pinned reference-data.csv files; downloading GPS/event observation members expressly forbidden"
        )
    ):
        raise ValueError("reference-only contract identity altered")
    for source in sources:
        expected_url = (
            f"https://zenodo.org/records/{source['record_id']}"
            "/files/BOP_RODENT-reference-data.csv?download=1"
        )
        if source.get("url") != expected_url or source.get("reference_file") != "BOP_RODENT-reference-data.csv":
            raise ValueError("only the exact two frozen reference CSV URLs are permitted")
    return contract


def _source_bytes(source: dict, limit: int) -> bytes:
    url = source["url"]
    parsed=urlparse(url)
    if parsed.hostname != "zenodo.org" or "/gps-" in parsed.path.lower() or not parsed.path.endswith("reference-data.csv"):
        raise ValueError("disallowed GPS/event observation source")
    if limit <= 0 or limit >= 1000000:
        raise ValueError("reference file source size ceiling altered")
    req = request.Request(
        url,
        headers={"User-Agent": "ODSP-scientific-reference-only-roster-preflight/1.0"}
    )
    # No mirror substitution, version switching, or outcome-dependent retry.
    with request.urlopen(req, timeout=35) as response:
        redirected = urlparse(response.geturl())
        # Zenodo may use an official files host; reject redirection to
        # an unexpected domain before processing bytes.
        if redirected.hostname not in ("zenodo.org","zenodo-files-prod.s3.amazonaws.com"):
            raise ValueError("reference download redirected outside declared provider")
        data=response.read(limit+1)
    if len(data)>limit:
        raise ValueError("provider reference source exceeds frozen small-file limit")
    if hashlib.md5(data).hexdigest()!=source["md5"]:
        raise ValueError("provider reference MD5 mismatch: stop without replacement")
    return data


def parse_animals(raw: bytes, expected_fields: list[str]) -> tuple[dict[str, str], dict[str, object]]:
    """Collapse repeated deployments by *animal-id*, never by tag or row."""
    try:
        content=raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("reference CSV UTF-8 decoding failed") from exc
    reader=csv.DictReader(io.StringIO(content),delimiter=",")
    header=reader.fieldnames
    if not header or any(name not in header for name in expected_fields):
        raise ValueError("reference CSV does not contain the declared animal-id/animal-taxon")
    if len(set(header))!=len(header):
        raise ValueError("reference CSV has duplicate header columns")
    roster:dict[str,str]={}
    deployments=0
    for row in reader:
        animal=(row["animal-id"] or "").strip()
        taxon=(row["animal-taxon"] or "").strip()
        if not animal or not taxon:
            raise ValueError("missing animal identity or taxon; fail closed")
        deployments+=1
        if animal in roster and roster[animal] != taxon:
            raise ValueError("same animal ID has conflicting taxa")
        roster[animal]=taxon
    if not roster:
        raise ValueError("source reference has zero biological animals")
    # Do not publish raw animal IDs; report only counts and a digest of
    # source roster plus full source checksum.
    fingerprint=hashlib.sha256(
        json.dumps(sorted(roster.items()),separators=(",",":"),ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return roster,{
        "reference_rows":deployments,
        "distinct_animal_ids":len(roster),
        "species_counts":dict(sorted(Counter(roster.values()).items())),
        "identity_taxon_roster_sha256":fingerprint,
        "reference_bytes_sha256":hashlib.sha256(raw).hexdigest(),
    }


def audit_reference_rosters(old:dict[str,str], new:dict[str,str], contract:dict) -> dict:
    aliases=contract["provider_changelog"]["corrected_animal_id_aliases"]
    removed=set(contract["provider_changelog"]["removed_out_of_scope_ids"])
    old_virtual=dict(old)
    applied_aliases=0
    for from_id,to_id in aliases.items():
        if from_id in old_virtual and to_id in new:
            if to_id in old_virtual and to_id!=from_id:
                raise ValueError("alias destination already existed in old archive: cannot infer novelty")
            old_virtual[to_id]=old_virtual.pop(from_id)
            applied_aliases+=1
        elif from_id in old_virtual and to_id not in new:
            raise ValueError("declared ID correction not seen in new reference roster")
        elif to_id in new and from_id not in old_virtual:
            raise ValueError("corrected new ID has no original identity")
    for animal in old_virtual.keys() & new.keys():
        if old_virtual[animal] != new[animal]:
            raise ValueError("same animal ID changed species across versions")
    common=old_virtual.keys() & new.keys()
    new_only=new.keys()-old_virtual.keys()
    old_only=old_virtual.keys()-new.keys()
    # Removed old IDs are not a novel cohort; keep a separate attrition count.
    recorded_removed=old_only & removed
    unexpected_removed=old_only-removed
    if unexpected_removed:
        raise ValueError("unexpected old animals missing from new reference: identity review needed")
    add_by_species=dict(sorted(Counter(new[x] for x in new_only).items()))
    threshold=contract["admission_rule"]["minimum_new_individuals_for_one_stratum_90pct_rank_calibration_plus_one_test"]
    supported={name:n>=threshold for name,n in add_by_species.items()}
    eligible=any(supported.values())
    return {
        "old_distinct_animals":len(old),
        "new_distinct_animals":len(new),
        "overlapping_corrected_animal_ids":len(common),
        "new_id_candidates_count":len(new_only),
        "new_id_candidates_by_species":add_by_species,
        "applied_known_alias_count":applied_aliases,
        "old_removed_out_of_scope_count":len(recorded_removed),
        "new_id_candidates_within_stratum_meet_min_count":supported,
        "one_stratum_minimum_count":threshold,
        "same_study_not_independent_population_replication":True,
        "metadata_novelty_not_proof_of_independent_animal":True,
        "original_empirical_BOP_terminal_changed":False,
        "scientific_status":(
            "METADATA_ONLY_CANDIDATE_NEEDS_OUTCOME_BLIND_GPS_ELIGIBILITY"
            if eligible else
            "NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT"
        ),
    }


def build_report(
    *,
    reference_bytes:tuple[bytes,bytes]|None=None,
    contract_path:Path=CONTRACT,
) -> dict[str,object]:
    content=contract_path.read_bytes()
    contract=contract_from_bytes(content)
    summary={
        "contract_id":contract["contract_id"],
        "contract_sha256":hashlib.sha256(content).hexdigest(),
        "source_version_dois":[s["doi"] for s in contract["source_versions"]],
        "source_md5s":list(EXPECTED_MD5S),
        "only_reference_data_access_authorized":True,
        "gps_event_data_accessed":False,
        "old_original_terminal":"empirical_state_prediction_mixed",
    }
    if reference_bytes is None:
        fetched=[]
        for source in contract["source_versions"]:
            fetched.append(
                _source_bytes(source,contract["maximum_reference_bytes_each"])
            )
        raw_sources=tuple(fetched)
    else:
        raw_sources=reference_bytes
    if len(raw_sources)!=2:
        raise ValueError("exactly two source reference CSVs are required")
    parsed=[]
    meta=[]
    for data in raw_sources:
        roster,sample=parse_animals(data,contract["expected_source_csv_field_names"])
        parsed.append(roster)
        meta.append(sample)
    if (
        meta[0]["distinct_animal_ids"] != contract["source_versions"][0]["published_metadata_individual_count"]
        or meta[1]["distinct_animal_ids"] != contract["source_versions"][1]["published_metadata_individual_count"]
    ):
        raise ValueError("official stated individual counts disagree with reference source")
    identity=audit_reference_rosters(parsed[0],parsed[1],contract)
    return {**summary, "references":meta, "identity_audit":identity}


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,help="New metadata-only JSON report")
    args=p.parse_args()
    try:
        report=build_report()
    except (ValueError,OSError,TimeoutError) as exc:
        message=str(exc)
        if any(key in message for key in ("reference CSV","missing animal identity","conflicting taxa")):
            scientific_status="METADATA_SCHEMA_MISMATCH"
        elif any(key in message for key in ("alias", "correction", "changed species", "unexpected old", "individual counts")):
            scientific_status="VERSION_IDENTITY_AMBIGUOUS"
        else:
            scientific_status="SOURCE_UNAVAILABLE"
        report={
            "contract_id":"bop-v3-v6-reference-only-roster-gate-v1",
            "scientific_status":scientific_status,
            "failure_class":type(exc).__name__,
            "failure_description":str(exc)[:350],
            "gps_event_data_accessed":False,
            "original_empirical_BOP_terminal_changed":False,
            "no_outcome_reanalysis_permitted":True,
        }
    output=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n"
    if args.out:
        if args.out.resolve()==CONTRACT.resolve():
            raise ValueError("never overwrite frozen source-only contract")
        args.out.write_text(output,encoding="utf-8")
    print(json.dumps({
        "scientific_status":report.get("scientific_status",report.get("identity_audit",{}).get("scientific_status")),
        "new_id_candidates_count":report.get("identity_audit",{}).get("new_id_candidates_count"),
        "gps_event_data_accessed":False,
        "failure_class":report.get("failure_class"),
    },sort_keys=True))


if __name__=="__main__":
    main()
