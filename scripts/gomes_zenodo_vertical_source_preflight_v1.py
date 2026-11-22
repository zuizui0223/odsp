#!/usr/bin/env python3
"""Gomes (2020) original v1 Zenodo Bats.csv source-only structural inventory.

Strictly header + row widths, NO original bat ecological numeric outcomes.
"""
from __future__ import annotations
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

DOI="10.5281/zenodo.4019867"
URL="https://zenodo.org/records/4019867/files/Bats.csv?download=1"
EXPECTED_MD5="2bc125dd0021d23c0efa0cb80828c632"
MAX_BYTES=4_000_000

def inspect_source(raw):
    if len(raw)>MAX_BYTES:
        raise RuntimeError("source exceeds frozen max file size")
    md5=hashlib.md5(raw).hexdigest()
    if md5!=EXPECTED_MD5:
        raise RuntimeError("published Zenodo file MD5 mismatch")
    try: text=raw.decode("utf-8-sig")
    except UnicodeError: text=raw.decode("latin-1")
    reader=csv.reader(io.StringIO(text,newline=""))
    headers=next(reader)
    if len(headers)<3 or len(set(headers))!=len(headers):
        raise RuntimeError("invalid or duplicate headers")
    lengths=Counter()
    for row in reader:
        lengths[len(row)]+=1
    count=sum(lengths.values())
    return {
      "status":"source_metadata_pass" if count>0 and lengths==Counter({len(headers):count}) else "source_metadata_stop",
      "dataset_doi":DOI,"version":"v1","url":URL,"expected_md5":EXPECTED_MD5,
      "original_file_md5":md5,"original_file_sha256":hashlib.sha256(raw).hexdigest(),
      "file_bytes":len(raw),"row_count":count,"header_fields":headers,
      "row_width_histogram":dict(sorted(lengths.items())),
      "ecological_outcome_values_accessed":False,
    }

def main():
    try:
        req=Request(URL, headers={"User-Agent":"odsp-gomes-zenodo-source-gate/1.0"})
        with urlopen(req,timeout=180) as r:
            original=r.read(MAX_BYTES+1)
        receipt=inspect_source(original)
    except Exception as e:
        receipt={"dataset_doi":DOI,"version":"v1","url":URL,"status":"source_access_or_schema_stop",
                 "stop_type":type(e).__name__,"stop_reason":str(e)[:500],"ecological_outcome_values_accessed":False}
    p=Path("results/gomes_zenodo_vertical_source_preflight_v1.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
