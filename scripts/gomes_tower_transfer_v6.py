#!/usr/bin/env python3
"""Gomes v6 local tower transfer on exact author source.

The original paper identifies COLOR=green/red physical canopy towers, 180 m
apart; X is only source row index. No GPS flight height or q calibration.
"""
from __future__ import annotations
import csv
from decimal import Decimal,InvalidOperation
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request,urlopen

from odsp.gomes_tower_transfer_v6 import TowerCell,score_tower_transfer
from scripts.gomes_zenodo_vertical_source_preflight_v1 import URL,EXPECTED_MD5
from scripts.gomes_zenodo_structure_v2 import KNOWN_HEADER
from scripts.gomes_zenodo_number_weighted_v4 import SOURCE_SHA256


def parse_source_towers(raw):
    if hashlib.md5(raw).hexdigest()!=EXPECTED_MD5 or hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:
        raise ValueError("source hash mismatch")
    try:txt=raw.decode("utf-8-sig")
    except UnicodeError:txt=raw.decode("latin-1")
    rd=csv.reader(io.StringIO(txt,newline=""))
    names=next(rd)
    if names!=KNOWN_HEADER:raise ValueError("source header changed")
    fields=("DAY","HOUR","Bat","POS","Number","COLOR")
    selected=[names.index(x) for x in fields]
    result=[]
    for values in rd:
        if len(values)!=len(names):
            raise ValueError("source ragged row")
        day,hour,label,pos,number,tower=(values[i].strip() for i in selected)
        try:
            number=Decimal(number)
        except InvalidOperation as exc:
            raise ValueError("invalid original Number") from exc
        if not number.is_finite() or number<0 or number!=number.to_integral_value():
            raise ValueError("original Number must be a nonnegative integer")
        if not hour.isdecimal():
            raise ValueError("source hour not integer")
        result.append(TowerCell(day,int(hour),label,pos,int(number),tower))
    # Source-only earlier roster validated; do not change after tower effects.
    if (len(result)!=7854 or len({x.label for x in result})!=21 or
        len({x.day for x in result})!=9 or
        {x.tower for x in result}!={"green","red"} or
        sum(x.number for x in result)!=16123):
        raise ValueError("original two-tower source structure/total mismatch")
    return result


def main():
    req=Request(URL,headers={"User-Agent":"odsp-gomes-two-tower-heldout-v6/1.0"})
    with urlopen(req,timeout=180) as resp:
        raw=resp.read(4_000_001)
    rows=parse_source_towers(raw)
    report=score_tower_transfer(rows)
    report.update({
        "source_original_data_doi":"10.5281/zenodo.4019867",
        "source_original_file_sha256":SOURCE_SHA256,
        "tower_semantics_original_publication":"Gomes et al. 2020 PeerJ doi:10.7717/peerj.10591",
        "tower_color_is_verified_by_original_author_model":True,
        "study_towers_in_one_forest_not_independent_regions":True,
        "source_outcomes_previously_opened_v4":True,
        "tower_specific_model_protocol_frozen_before_tower_scores":True,
        "analysis_claim":"post-outcome exploratory local microspatial transfer of recorded acoustic layer only",
        "frozen_protocol_path":"docs/gomes_tower_transfer_v6_postoutcome_prescore_freeze.md",
    })
    out=Path("results/gomes_tower_transfer_v6.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
