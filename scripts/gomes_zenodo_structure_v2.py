#!/usr/bin/env python3
"""Gomes original CSV categorical key preflight, independent of bat activity.
Only categorical/time key strings, never Number or solar/lunar measurements.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import csv,hashlib,io,json
from pathlib import Path
from urllib.request import Request,urlopen
from scripts.gomes_zenodo_vertical_source_preflight_v1 import URL,EXPECTED_MD5

KNOWN_HEADER=["","DAY","HOUR","X","COLOR","POS","Bat","Number","Date","Time",
              "S.Az","S.Alt","M.Az","M.Alt","Phase","M.SD","S.Illm","M.Illm","T.Illm"]
CONTEXT=("DAY","HOUR","X","COLOR","POS","Bat","Date","Time")

def metadata_scan(raw):
    if hashlib.md5(raw).hexdigest()!=EXPECTED_MD5:
        raise RuntimeError("pinned source MD5 mismatch")
    try: txt=raw.decode("utf-8-sig")
    except UnicodeError: txt=raw.decode("latin-1")
    reader=csv.reader(io.StringIO(txt,newline=""))
    header=next(reader)
    if header != KNOWN_HEADER:
        raise RuntimeError("original header changed")
    positions={f:header.index(f) for f in CONTEXT}
    values={f:set() for f in CONTEXT}
    paired=defaultdict(set)
    count=0
    missing=Counter()
    for row in reader:
        if len(row)!=len(header):
            raise RuntimeError("source row width changed")
        # Only extract source context fields; original response 'Number' is NOT accessed.
        v={f:row[i].strip() for f,i in positions.items()}
        count+=1
        for f,word in v.items():
            if word: values[f].add(word)
            else: missing[f]+=1
        paired[(v["DAY"],v["HOUR"],v["X"])].add(v["POS"])
    result={"status":"categorical_preflight_complete",
            "row_count":count,"response_number_opened":False,
            "unique_value_counts":{k:len(v) for k,v in values.items()},
            "distinct_categorical_values":{k:sorted(values[k])[:20]
                for k in ("POS","X","COLOR")},
            "day_values":sorted(values["DAY"])[:35],
            "hour_values":sorted(values["HOUR"])[:30],
            "bat_label_count":len(values["Bat"]),
            "missing_context_columns":dict(missing),
            "context_day_hour_x_groups":len(paired),
            "context_day_hour_x_with_two_or_more_pos":sum(len(v)>=2 for v in paired.values()),
            "accessed_columns":list(CONTEXT),
            "source_file_sha256":hashlib.sha256(raw).hexdigest()}
    return result

def main():
    try:
        request=Request(URL,headers={"User-Agent":"odsp-gomes-categorical-v2/1.0"})
        with urlopen(request,timeout=180) as resp:
            raw=resp.read(4_000_001)
        result=metadata_scan(raw)
    except Exception as e:
        result={"status":"source_schema_stop","type":type(e).__name__,
                "reason":str(e)[:400],"response_number_opened":False}
    p=Path("results/gomes_zenodo_structure_v2.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
