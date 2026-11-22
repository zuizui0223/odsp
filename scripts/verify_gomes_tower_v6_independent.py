#!/usr/bin/env python3
"""Independent replay of Gomes v6 two-tower primary proper scores.

Intentionally does not import either ODSP v6 scorer or its source adapter.
The original author-design is already opened. This verifies arithmetic only,
not sensor q, biological causation or independence of two nearby towers.
"""
from __future__ import annotations
from collections import defaultdict
from decimal import Decimal
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.request import Request,urlopen


URL="https://zenodo.org/records/4019867/files/Bats.csv?download=1"
SHA256="4a3b84e7175c29110bb6220f5cdf5889152897501b371fad3e2d9a74523773c9"
MD5="2bc125dd0021d23c0efa0cb80828c632"
EXPECTED={
    "green": {"B0":-1.6766025460057739, "B1":-1.3551956282356767, "gain":0.3214069177700971, "count":13117},
    "red": {"B0":-1.4064120021984057, "B1":-1.1537558404835977, "gain":0.252656161714808, "count":3006},
}
TOL=1e-10


def verify_original():
    request=Request(URL,headers={"User-Agent":"odsp-gomes-two-tower-independent-replay-v1/1.0"})
    with urlopen(request,timeout=180) as response:
        raw=response.read(4_000_001)
    if hashlib.sha256(raw).hexdigest()!=SHA256 or hashlib.md5(raw).hexdigest()!=MD5:
        raise RuntimeError("source checksum mismatch")
    text=raw.decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(text,newline=""))
    expected_fields={"DAY","HOUR","Bat","POS","Number","COLOR"}
    if not expected_fields.issubset(set(reader.fieldnames or [])):
        raise RuntimeError("source field mismatch")
    events=[]
    for line in reader:
        number=Decimal(str(line["Number"]).strip())
        if number<0 or not number.is_finite() or number!=number.to_integral_value():
            raise RuntimeError("invalid original Number response")
        events.append((line["COLOR"].strip(),line["DAY"].strip(),
                       int(line["HOUR"]),line["Bat"].strip(),line["POS"].strip(),
                       int(number)))
    if len(events)!=7854 or sum(e[-1] for e in events)!=16123:
        raise RuntimeError("source row or count changed")
    return events


def fit_and_score(events):
    scored={}
    for held in ("green","red"):
        train=[r for r in events if r[0]!=held]
        test=[r for r in events if r[0]==held]
        global_tot=defaultdict(int)
        hour_tot=defaultdict(int)
        bat_hour_tot=defaultdict(int)
        training_class_count=defaultdict(int)
        for tower,day,hour,bat,layer,count in train:
            global_tot[layer]+=count
            hour_tot[(hour,layer)]+=count
            bat_hour_tot[(bat,hour,layer)]+=count
            training_class_count[bat]+=count
        total=sum(row[-1] for row in test)
        if total==0:raise RuntimeError("empty target tower")
        base_loss=0.0
        detailed_loss=0.0
        for tower,day,hour,bat,layer,count in test:
            if count==0:continue
            hourly_n=hour_tot[(hour,"above")]+hour_tot[(hour,"below")]
            if hourly_n:
                p_base=(hour_tot[(hour,layer)]+.5)/(hourly_n+1.0)
            else:
                p_base=(global_tot[layer]+.5)/(global_tot["above"]+global_tot["below"]+1)
            cell_n=bat_hour_tot[(bat,hour,"above")]+bat_hour_tot[(bat,hour,"below")]
            if training_class_count[bat]>5 and cell_n>0:
                p_bat=(bat_hour_tot[(bat,hour,layer)]+.5)/(cell_n+1.0)
            else:
                p_bat=p_base
            base_loss+=count*math.log(p_base)
            detailed_loss+=count*math.log(p_bat)
        score0=base_loss/total
        score1=detailed_loss/total
        increment=(detailed_loss-base_loss)/total
        scored[held]={"count":total,"B0":score0,"B1":score1,"gain":increment}
    return scored


def main():
    results=fit_and_score(verify_original())
    checks=[]
    for tower,observed in results.items():
        for key, value in observed.items():
            tol=0.0 if key=="count" else TOL
            delta=abs(float(value)-float(EXPECTED[tower][key]))
            checks.append({"tower":tower,"quantity":key,"maximum_abs_difference":delta,
                           "matches_original_v6":delta<=tol})
    if not all(x["matches_original_v6"] for x in checks):
        raise RuntimeError("independent v6 replay differs from archived estimates")
    payload={
        "status":"independent_source_and_math_replay_agree",
        "reproduction_target":"v6 original local whole-tower B0/B1 frozen scores",
        "original_source_sha256":SHA256,
        "separate_implementation":True,
        "replay_imported_odsp_v6_engine":False,
        "scores":results,
        "max_difference":max(c["maximum_abs_difference"] for c in checks),
        "checks_passed":len(checks),
        "no_biological_q_calibration":True,
        "two_towers_not_geographic_replication":True,
    }
    path=Path("results/gomes_tower_v6_independent_replay.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
