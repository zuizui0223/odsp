#!/usr/bin/env python3
"""Author-corrected v4 original acoustic count response: fixed before opening.
Pinned Gomes Zenodo 2020 v1; only DAY/HOUR/Bat/POS/Number accessed.
"""
from __future__ import annotations
import csv,hashlib,io,json
from decimal import Decimal,InvalidOperation
from pathlib import Path
from urllib.request import Request,urlopen

from odsp.weighted_detected_vertical_transfer import CountCell,score_weighted_counts
from scripts.gomes_zenodo_structure_v2 import KNOWN_HEADER
from scripts.gomes_zenodo_vertical_source_preflight_v1 import URL,EXPECTED_MD5

SOURCE_SHA256="4a3b84e7175c29110bb6220f5cdf5889152897501b371fad3e2d9a74523773c9"
EXPECTED_SOURCE_ROWS=7854

def parse_original(raw):
    if hashlib.md5(raw).hexdigest()!=EXPECTED_MD5 or hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:
        raise ValueError("v1 original source hash mismatch")
    try:txt=raw.decode("utf-8-sig")
    except UnicodeError:txt=raw.decode("latin-1")
    rd=csv.reader(io.StringIO(txt,newline=""))
    header=next(rd)
    if header!=KNOWN_HEADER:raise ValueError("source header drift")
    inds=[header.index(f) for f in ("DAY","HOUR","Bat","POS","Number")]
    cells=[]
    for row in rd:
        if len(row)!=len(header):raise ValueError("source row length drift")
        day,hour,label,pos,num=(row[i].strip() for i in inds)
        if not hour.isdecimal():raise ValueError("invalid HOUR")
        try: count=Decimal(num)
        except InvalidOperation:raise ValueError("Number not numeric")
        if not count.is_finite() or count<0 or count!=count.to_integral_value():
            raise ValueError("Number must be finite nonnegative integer count")
        cells.append(CountCell(day,int(hour),label,pos,int(count)))
    if len(cells)!=EXPECTED_SOURCE_ROWS or len({x.day for x in cells})!=9 or len({x.label for x in cells})!=21:
        raise ValueError("mismatch to pre-open source structural audit")
    return cells

def main():
    req=Request(URL,headers={"User-Agent":"odsp-gomes-number-weighted-v4/1.0"})
    with urlopen(req,timeout=180) as r:
        raw=r.read(4_000_001)
    cells=parse_original(raw)
    summary=score_weighted_counts(cells)
    outcome={
        "source_doi":"10.5281/zenodo.4019867",
        "source_version":"v1",
        "source_original_sha256":SOURCE_SHA256,
        "author_reference_md5":"376bfc130acad070aa7045f6c816cd09",
        "preopen_design":"docs/gomes_zenodo_number_weighted_v4_preopen.md",
        "author_original_response_is_Number":True,
        "earlier_row_level_v3_is_not_biological_activity":True,
        "calibrated_true_flight_height":False,
        "calibrated_species_layer_detection":False,
        **summary,
    }
    p=Path("results/gomes_zenodo_number_weighted_v4.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(outcome,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(outcome,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
