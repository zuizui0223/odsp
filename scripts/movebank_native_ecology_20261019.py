"""Source-wide native-file metadata and observation-only equal-daylength screening.

No animal displacement/behavioural outcomes are computed. No individual IDs, event
timestamps or coordinates are published. Source failures remain visible as HOLD.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timedelta, date, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = "https://datarepository.movebank.org/server/api"
HERE = Path(__file__).resolve().parents[1]
CATALOG = HERE / "research/seasonal_database_catalog/2026-10-19/movebank/catalog.json"
PILOT = HERE / "research/MOVEBANK_NATIVE_OBSERVATION_PILOT_20261019.json"

def fetch(url: str, retries: int = 3) -> bytes:
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent":"ODSP-ecology-public-research/1.0", "Accept":"application/json"})
            with urlopen(req, timeout=70) as response:
                return response.read()
        except (HTTPError,URLError,TimeoutError) as exc:
            if attempt == retries-1 or isinstance(exc,HTTPError) and exc.code in (401,403,404):
                raise
            time.sleep(2**attempt)
    raise RuntimeError("unreachable")

def get_json(url): return json.loads(fetch(url))

def original_files(package_uuid: str) -> list[dict]:
    b = get_json(f"{ROOT}/core/items/{package_uuid}/bundles?size=100")
    if b["page"]["totalPages"]!=1: raise ValueError("Unresolved bundle pagination")
    original = [x for x in b.get("_embedded",{}).get("bundles",[]) if x["name"]=="ORIGINAL"]
    if len(original)!=1: raise ValueError("Original bundle missing or ambiguous")
    files = get_json(f'{ROOT}/core/bundles/{original[0]["uuid"]}/bitstreams?size=100')
    if files["page"]["totalPages"]!=1: raise ValueError("Unresolved bitstream pagination")
    return [{"bitstream_uuid":x["uuid"],"name":x["name"],"bytes":x.get("sizeBytes"),"checksum":x.get("checkSum")}
            for x in files.get("_embedded",{}).get("bitstreams",[])]

def make_inventory(out_dir:Path,workers:int=6):
    packages=json.loads(CATALOG.read_text())["packages"]
    if len(packages)!=437 or len({p["package_uuid"] for p in packages})!=437:
        raise ValueError("The complete 437-package public source frame was modified")
    def one(p):
        x={k:p[k] for k in ("package_uuid","handle","scientific_names","sensor_names",
                             "reported_animal_count","reported_location_count","dois","licenses")}
        try: x.update(status="ok",files=original_files(p["package_uuid"]))
        except Exception as exc: x.update(status="source_hold",files=[],error=f"{type(exc).__name__}: {exc}")
        return x
    with ThreadPoolExecutor(max_workers=workers) as pool:
        fs=[pool.submit(one,p) for p in packages]
        entries=[f.result() for f in as_completed(fs)]
    entries.sort(key=lambda x:x["package_uuid"])
    summary={"frame_packages":437,"packages_with_resolved_original_files":sum(x["status"]=="ok" for x in entries),
        "packages_source_hold":sum(x["status"]!="ok" for x in entries),
        "original_bitstreams_found":sum(len(x["files"]) for x in entries),
        "note":"Native file metadata only. No animal-level temporal or behavioural response was measured."}
    out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/"native_file_inventory.json").write_text(json.dumps(entries,indent=2,ensure_ascii=False)+"\n")
    (out_dir/"native_file_inventory_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("NATIVE_INVENTORY_SUMMARY "+json.dumps(summary,sort_keys=True),flush=True)

def checksum_and_download(bitstream:dict,path:Path):
    ck=bitstream["checksum"]
    if ck["checkSumAlgorithm"].upper() not in ("MD5","SHA256","SHA-256"):
        raise ValueError("Unsupported checksum type")
    alg="md5" if ck["checkSumAlgorithm"].upper()=="MD5" else "sha256"
    h=hashlib.new(alg)
    url=f'{ROOT}/core/bitstreams/{bitstream["bitstream_uuid"]}/content'
    with urlopen(Request(url,headers={"User-Agent":"ODSP-ecology-public-research/1.0"}),timeout=150) as src, path.open("wb") as dst:
        while chunk:=src.read(1024*1024):
            dst.write(chunk);h.update(chunk)
    if h.hexdigest().lower()!=ck["value"].lower():
        path.unlink(missing_ok=True);raise ValueError("Provider checksum mismatch")
    if bitstream.get("bytes") is not None and path.stat().st_size!=bitstream["bytes"]:
        path.unlink(missing_ok=True);raise ValueError("Provider byte-count mismatch")
    return {"bytes":path.stat().st_size,"checksum_type":alg,"provider_checksum_verified":True}

def parse_time(raw:str):
    try:
        d=datetime.fromisoformat(raw.strip().replace("Z","+00:00"))
        if d.tzinfo is not None: d=d.astimezone(timezone.utc).replace(tzinfo=None)
        return d
    except (AttributeError,TypeError,ValueError):return None

def daylength(lat:float, d:date)->float:
    lat=math.radians(lat)
    n=d.timetuple().tm_yday
    dec=math.asin(0.39779*math.cos(2*math.pi*(n-172)/365.2422))
    den=math.cos(lat)*math.cos(dec)
    if abs(den)<1e-10:return 24.0 if math.sin(lat)*math.sin(dec)>0 else 0.0
    x=(math.sin(math.radians(-0.833))-math.sin(lat)*math.sin(dec))/den
    return 24/math.pi*math.acos(max(-1,min(1,x)))

def solar_period(ts:datetime,lat:float,lon:float)->tuple[date,str]:
    t=ts+timedelta(hours=lon/15)
    solar_h=t.hour+t.minute/60+t.second/3600
    return t.date(),"day" if abs(solar_h-12)<daylength(lat,t.date())/2 else "night"

def greedy_pairs(a:dict,b:dict,lat:float,caliper_min:float=5,minimum_separation:int=30):
    edges=[]
    for before in a:
        for after in b:
            if (after-before).days<minimum_separation:continue
            gap=abs(daylength(lat,before)-daylength(lat,after))*60
            if gap<=caliper_min:edges.append((gap,before,after))
    used_a=set();used_b=set();pairs=[]
    for gap,da,db in sorted(edges):
        if da not in used_a and db not in used_b:
            pairs.append((da,db,gap));used_a.add(da);used_b.add(db)
    return pairs

def inspect_csv(path:Path)->dict:
    support=defaultdict(lambda:[0,0])
    by_ind=defaultdict(int)
    lat_sum=defaultdict(lambda:[0.,0])
    n=invalid=0
    with path.open("r",encoding="utf-8-sig",newline="") as fh:
        rd=csv.DictReader(fh)
        cols=rd.fieldnames or []
        def col(*opts):return next((c for c in cols if c.lower().strip() in opts),None)
        ti=col("timestamp","event-date","eventdate")
        indcol=col("individual-local-identifier","individual-id","animal-id","individual local identifier")
        latcol=col("location-lat","location-latitude","latitude")
        loncol=col("location-long","location-longitude","longitude")
        if None in (ti,indcol,latcol,loncol):
            return {"status":"source_schema_hold","columns":cols,"reason":"Missing required event-time/individual/position fields"}
        for row in rd:
            n+=1
            d=parse_time(row.get(ti,""))
            ind=(row.get(indcol) or "").strip()
            try:lat=float(row[latcol]);lon=float(row[loncol])
            except (TypeError,ValueError):lat=float("nan");lon=float("nan")
            if d is None or not ind or not (math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180):
                invalid+=1;continue
            day,period=solar_period(d,lat,lon)
            support[(ind,day)][int(period=="night")]+=1
            by_ind[ind]+=1
            lat_sum[ind][0]+=lat;lat_sum[ind][1]+=1
    admitted=defaultdict(dict)
    for (ind,d),cnt in support.items():
        if cnt[0]>=3 and cnt[1]>=3: admitted[(ind,d.year)][d]=cnt
    pairs_per_year=[]
    for (ind,year),days in admitted.items():
        lat=lat_sum[ind][0]/lat_sum[ind][1]
        if lat<=0:continue # pilot is northern only
        solstice=date(year,6,21)
        before={d:c for d,c in days.items() if d<solstice}
        after={d:c for d,c in days.items() if d>solstice}
        pairs_per_year.append(len(greedy_pairs(before,after,lat)))
    return {"status":"coverage_evaluated","csv_rows":n,"valid_position_time_individual_rows":n-invalid,
            "invalid_or_missing_rows":invalid,"distinct_individuals_with_valid_fixes":len(by_ind),
            "distinct_local_individual_days":len(support),
            "individual_years_with_both_day_and_night_support":len(pairs_per_year),
            "individual_years_ge_5_pairs":sum(x>=5 for x in pairs_per_year),
            "individual_years_ge_10_pairs":sum(x>=10 for x in pairs_per_year),
            "individual_years_ge_20_pairs":sum(x>=20 for x in pairs_per_year),
            "max_conservative_matched_day_pairs":max(pairs_per_year,default=0),
            "note":"Conservative preliminary observation-day matching, NOT displacement, actual locomotor activity, causal effects or population-level inference."}

def pilot_coverage(out_dir:Path):
    manifest=json.loads(PILOT.read_text())
    out_dir.mkdir(parents=True,exist_ok=True)
    entries=[]
    for p in manifest["sources"]:
        out={"label":p["label"],"package_uuid":p["package_uuid"],"source_doi":p["doi"]}
        try:
            matches=[x for x in original_files(p["package_uuid"]) if x["bitstream_uuid"]==p["original_csv_bitstream_uuid"]]
            if len(matches)!=1 or matches[0]["checksum"]["value"]!=p["original_csv_md5"]:
                raise ValueError("Pinned original file UUID or provider MD5 changed")
            path=out_dir/(p["label"]+".csv")
            out["download"]=checksum_and_download(matches[0],path)
            out.update(inspect_csv(path))
            path.unlink(missing_ok=True)
        except Exception as exc:
            out.update(status="source_hold",reason=f"{type(exc).__name__}: {exc}")
        entries.append(out)
        print("PILOT_COVERAGE "+json.dumps(out,sort_keys=True),flush=True)
    result={"sources":entries,"scope":"Three fixed original-source GPS files: timing opportunities only, no movement-effect estimates"}
    (out_dir/"pilot_coverage_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("PILOT_COVERAGE_TOTAL "+json.dumps({"n_sources":len(entries),
            "n_evaluated":sum(x["status"]=="coverage_evaluated" for x in entries),
            "n_individual_years_ge10":sum(x.get("individual_years_ge_10_pairs",0) for x in entries)},sort_keys=True),flush=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["inventory","pilot"])
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--workers",default=6,type=int)
    args=ap.parse_args()
    if args.mode=="inventory":make_inventory(args.out,args.workers)
    else:pilot_coverage(args.out)

if __name__=="__main__":main()
