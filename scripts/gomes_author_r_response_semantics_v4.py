#!/usr/bin/env python3
"""Inspect independent author R code for source response semantics only.
Original Bats.csv biological counts are NEVER opened here.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen

URL="https://zenodo.org/records/4019867/files/Hourly_Models.R?download=1"
EXPECTED_MD5="376bfc130acad070aa7045f6c816cd09"
CUES=("Number","Bat","POS","read.csv","read_csv","glmer","glm","glmm","family","counts","offset","activity","response","aggregate","group_by")

def interpret(raw):
    if hashlib.md5(raw).hexdigest()!=EXPECTED_MD5:
        raise RuntimeError("original v1 author code checksum mismatch")
    try: s=raw.decode("utf-8-sig")
    except UnicodeError: s=raw.decode("latin-1")
    lines=s.splitlines()
    hits=[{"line":i+1,"code":line[:220]} for i,line in enumerate(lines)
          if any(c.lower() in line.lower() for c in CUES)]
    return {"status":"author_code_semantics_opened","code_sha256":hashlib.sha256(raw).hexdigest(),
            "code_line_count":len(lines),"author_response_name_hits":hits[:100],
            "original_bat_activity_counts_opened":False}

def main():
    try:
        with urlopen(Request(URL,headers={"User-Agent":"odsp-gomes-author-r-semantics/1.0"}),timeout=120) as r:
            data=r.read(300_000)
        out=interpret(data)
    except Exception as e:
        out={"status":"author_code_source_stop","exception":type(e).__name__,"reason":str(e)[:400],
             "original_bat_activity_counts_opened":False}
    path=Path("results/gomes_author_r_response_semantics_v4.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
