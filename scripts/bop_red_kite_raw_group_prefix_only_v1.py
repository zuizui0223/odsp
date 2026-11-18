#!/usr/bin/env python3
"""Official red-kite *source-only* identity-year prefix projection.

Reads the entire two pinned individual-season CSV byte streams to check provider
MD5, but interprets ONLY leading predeclared key fields before the first label,
sex, age or outcome column. The CSV transport necessarily contains label bytes;
they are discarded as uninterpreted suffix bytes and never printed or stored.
NO tracking/GPS file, output-label values, per-bird roster or predictions.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_RED_KITE_RAW_GROUP_PREFIX_ONLY_V1_CONTRACT.json"
INVENTORY=ROOT/"BOP_RED_KITE_SOURCE_INVENTORY_V1_FIRST_RECEIPT.json"
HEADERS=ROOT/"BOP_RED_KITE_HEADER_ONLY_V1_FIRST_RECEIPT.json"


def _load_contract():
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    inventory=json.loads(INVENTORY.read_text(encoding="utf-8"))
    headers=json.loads(HEADERS.read_text(encoding="utf-8"))
    access=contract.get("access",{})
    meaning=contract.get("interpretation",{})
    if (
        contract.get("contract_id")!="bop-redkite-declared-source-key-prefix-projection-v1"
        or contract.get("frozen_date")!="2026-11-18"
        or contract.get("source_zenodo_doi")!="10.5281/zenodo.13736049"
        or access.get("full_CSV_bytes_contain_real_outcomes_but_not_parsed_by_projection") is not True
        or access.get("project_only_leading_ID_and_year_columns") is not True
        or access.get("discard_all_nonprefix_bytes_without_field_decoding") is not True
        or access.get("no_GPS_files_or_tracking_events") is not True
        or access.get("no_raw_or_hashed_bird_ID_or_year_ID_in_public_receipts") is not True
        or access.get("max_prefix_bytes_per_line")!=512
        or meaning.get("biological_terminal")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or meaning.get("original_BOP_empirical_terminal")!="empirical_state_prediction_mixed"
        or meaning.get("original_BOP_Dryad_status")!="NOT_ADMITTED"
        or headers["critical_limits"]["no_individual_year_values_parsed"] is not True
    ):
        raise ValueError("preaccess source-only key projection contract violated")
    frozen=contract.get("input_files",[])
    if [x.get("key") for x in frozen]!=["GER_indseasondata.csv","SUI_indseasondata.csv"]:
        raise ValueError("only frozen pair of biological metadata CSVs permitted")
    inv={x["key"]:x for x in inventory["source_manifest_observation"]["manifest"]}
    first=headers["verified_first_header"]
    for spec in frozen:
        name=spec["key"]
        country=name[:3]
        if (
            inv[name]["md5"]!=spec["md5"]
            or inv[name]["bytes"]!=spec["bytes"]
            or first[country+"_indseasondata"]["filename"]!=name
            or first[country+"_indseasondata"]["column_names"]!=spec["header_columns"]
            or spec["header_columns"][:len(spec["allowed_prefix_columns"])]!=spec["allowed_prefix_columns"]
            or set(("bird_id","year_id"))-set(spec["allowed_prefix_columns"])
            or any(x in spec["allowed_prefix_columns"] for x in ("HR","nest","success","age_cy","sex"))
        ):
            raise ValueError("provider manifest/header or key-only whitelist drift")
    return contract,headers


class KeyPrefixCollector:
    """Streaming scanner: all nonprefix CSV bytes are never decoded or retained.

    The method counts *physical CSV record lines*; it does not certify that
    provider-controlled outcome suffixes have no quoted embedded line breaks.
    """
    def __init__(self,spec:dict,header_sha256:str,max_header:int=4096,max_prefix:int=512):
        self.spec=spec
        self.header_sha256=header_sha256
        self.max_header=max_header
        self.max_prefix=max_prefix
        self.digest=hashlib.md5()
        self.nbytes=0
        self.header_done=False
        self.header=bytearray()
        self.prefix=bytearray()
        self.commas=0
        self.tail=False
        self.records=0
        self.bird_counts=Counter()
        self.season_owner={}
        self.duplicate_year_lines=0
        self.year_with_multiple_bird_ID=0

    def _finish_header(self):
        if not self.header or self.header[-1]!=10:
            raise ValueError("incomplete source header")
        if hashlib.sha256(bytes(self.header)).hexdigest()!=self.header_sha256:
            raise ValueError("first physical source header does not match first archived header")
        expected=(",".join(self.spec["header_columns"])+"\r\n").encode("utf-8")
        if bytes(self.header)!=expected:
            raise ValueError("source header changed since frozen original CRLF receipt")
        self.header_done=True
        self.header.clear()

    def _finish_body_line(self):
        num_fields=len(self.spec["allowed_prefix_columns"])
        if self.commas!=num_fields or not self.tail or self.prefix[-1:]!=b",":
            raise ValueError("source line lacks fixed key-prefix columns")
        try:
            fields=self.prefix[:-1].decode("utf-8").split(",")
        except UnicodeDecodeError as e:
            raise ValueError("invalid key prefix UTF-8") from e
        if len(fields)!=num_fields or any(
            (not v) or v!=v.strip() or any(ord(ch)<32 or ch in '"\0' for ch in v)
            for v in fields
        ):
            raise ValueError("missing, quoted, multiline or malformed source key prefix")
        values=dict(zip(self.spec["allowed_prefix_columns"],fields))
        bird=values["bird_id"]
        season=values["year_id"]
        self.records+=1
        self.bird_counts[bird]+=1
        if season in self.season_owner:
            self.duplicate_year_lines+=1
            if self.season_owner[season]!=bird:
                self.year_with_multiple_bird_ID+=1
        else:
            self.season_owner[season]=bird
        self.prefix.clear()
        self.commas=0
        self.tail=False

    def feed(self,chunk:bytes):
        if not isinstance(chunk,bytes):
            raise ValueError("network stream must provide bytes")
        self.digest.update(chunk)
        self.nbytes+=len(chunk)
        if self.nbytes>self.spec["bytes"]:
            raise ValueError("source byte count exceeds published pinned file size")
        for byte in chunk:
            if not self.header_done:
                self.header.append(byte)
                if len(self.header)>self.max_header:
                    raise ValueError("source header exceeds fixed byte ceiling")
                if byte==10:
                    self._finish_header()
            elif byte==10:
                self._finish_body_line()
            elif not self.tail:
                self.prefix.append(byte)
                if len(self.prefix)>self.max_prefix:
                    raise ValueError("source identity-year key prefix exceeds fixed limit")
                if byte==44:
                    self.commas+=1
                    if self.commas==len(self.spec["allowed_prefix_columns"]):
                        self.tail=True
            else:
                # A body-line suffix may include sex, age, HR, nest, success.
                # It is not decoded, parsed into fields, buffered or persisted.
                pass

    def finish(self):
        if not self.header_done:
            raise ValueError("source contains no verified original CSV header")
        if self.prefix or self.tail:
            self._finish_body_line()  # tolerate absent final LF
        if self.nbytes!=self.spec["bytes"] or self.digest.hexdigest()!=self.spec["md5"]:
            raise ValueError("source full byte count or MD5 mismatched Zenodo manifest")
        if not self.records:
            raise ValueError("source lacks record lines")
        distribution=Counter(self.bird_counts.values())
        return {
            "source":self.spec["key"],
            "source_full_file_md5_verified":True,
            "source_bytes":self.nbytes,
            "physical_record_lines":self.records,
            "distinct_bird_ID_strings":len(self.bird_counts),
            "distinct_year_ID_strings":len(self.season_owner),
            "duplicate_year_ID_lines":self.duplicate_year_lines,
            "year_ID_to_multiple_bird_IDs":self.year_with_multiple_bird_ID,
            "number_of_birds_with_multiple_season_records":sum(v for k,v in distribution.items() if k>=2),
            "max_season_records_per_bird":max(distribution),
            "season_records_per_bird_histogram":{str(k):distribution[k] for k in sorted(distribution)},
        }


def project_prefix(chunks:Iterable[bytes],spec:dict,header_sha256:str)->tuple[dict,set[str],set[str]]:
    """Used by both official source runner and offline synthetic-only tests."""
    collector=KeyPrefixCollector(spec,header_sha256)
    for chunk in chunks:
        collector.feed(chunk)
    out=collector.finish()
    # These raw keys exist solely in volatile process memory for comparing
    # lexical collisions; they must NEVER be emitted to artifacts/logs.
    return out,set(collector.bird_counts),set(collector.season_owner)


def _fetch_source(spec:dict,header_sha256:str)->tuple[dict,set[str],set[str]]:
    key=spec["key"]
    url=f"https://zenodo.org/records/13736049/files/{key}?download=1"
    req=Request(url,headers={"User-Agent":"ODSP-red-kite-identity-prefix-only-v1/1.0","Accept-Encoding":"identity"})
    with urlopen(req,timeout=60) as res:
        final=urlparse(res.geturl())
        if (final.scheme!="https"
            or final.hostname not in ("zenodo.org","www.zenodo.org")
            or "/13736049/" not in unquote(final.path)
            or key not in unquote(final.path)
            or int(res.status)!=200):
            raise ValueError("source provenance redirect, content or status mismatch")
        def chunks():
            while True:
                b=res.read(8192)
                if not b:
                    return
                yield b
        return project_prefix(chunks(),spec,header_sha256)


def run()->dict:
    contract,heads=_load_contract()
    country=[]
    bird_sets=[]
    year_sets=[]
    for spec in contract["input_files"]:
        key=spec["key"]
        head=heads["verified_first_header"][key[:3]+"_indseasondata"]["header_sha256"]
        stats,birds,years=_fetch_source(spec,head)
        country.append(stats)
        bird_sets.append(birds)
        year_sets.append(years)
    duplicate_or_ambiguous=any(
        x["duplicate_year_ID_lines"] or x["year_ID_to_multiple_bird_IDs"] for x in country)
    status=("HOLD_SOURCE_SCHEMA_OR_CANONICAL_IDENTITY"
            if duplicate_or_ambiguous else "SOURCE_RAW_YEAR_ID_GROUP_COUNTS_ONLY")
    return {
        "schema_version":1,
        "source_role":"FULL_CSV_BYTES_FOR_MD5_PREFIX_KEYS_ONLY_SUFFIX_NOT_PARSED",
        "status":status,
        "preaccess_contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "sources":country,
        "source_pair_bird_ID_exact_string_overlap":len(bird_sets[0]&bird_sets[1]),
        "source_pair_year_ID_exact_string_overlap":len(year_sets[0]&year_sets[1]),
        "source_pair_lexical_overlap_not_canonical_identity_proof":True,
        "source_populations_verified_from_source":False,
        "GER_raw_roster_not_GPS_eligible_99_season_63_bird_roster":True,
        "GER_GPS_800fix_season_filter_reproduced":False,
        "animal_identity_crosswalk_authenticated":False,
        "breeding_response_suffix_values_parsed":False,
        "GPS_events_opened":False,
        "real_model_probabilities_scored":False,
        "biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "original_BOP_empirical_terminal":"empirical_state_prediction_mixed",
        "original_BOP_Dryad":"NOT_ADMITTED",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    if args.out.resolve() in {CONTRACT.resolve(),INVENTORY.resolve(),HEADERS.resolve()}:
        raise ValueError("refuse to overwrite frozen contract/source receipts")
    try:
        result=run()
    except (OSError,ValueError,UnicodeError) as exc:
        result={
            "schema_version":1,"source_role":"SOURCE_ONLY_ID_PROJECTION_ACCESS_HOLD",
            "status":"HOLD_SOURCE_SCHEMA_OR_CANONICAL_IDENTITY",
            "error_type":type(exc).__name__,
            "breeding_response_suffix_values_parsed":False,
            "GPS_events_opened":False,
            "real_model_probabilities_scored":False,
            "biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        }
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    if result["status"]!="SOURCE_RAW_YEAR_ID_GROUP_COUNTS_ONLY":
        raise SystemExit("SOURCE_ONLY_KEY_PROJECTION_HOLD: no predictive outcomes evaluated")

if __name__=="__main__":
    main()
