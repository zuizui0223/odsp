"""Southern-Hemisphere equal-daylength mammal diel movement: source-locked first comparison.

Original public Movebank files validated against provider checksum before any
GPS displacement computation. Outputs ONLY source-level aggregate measures.
"""
import argparse
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import random
from statistics import mean, median
from zipfile import ZipFile

from scripts.movebank_native_ecology_20261019 import (
    HERE, original_files, checksum_and_download, solar_period, daylength
)
from scripts.movebank_solar_movement_20261019 import (
    load_events, valid_interval
)

CONTRACT = HERE / "research/MOVEBANK_SOUTHERN_SOLAR_MOVEMENT_V0_20261019.json"
CATALOG = HERE / "research/seasonal_database_catalog/2026-10-19/movebank/catalog.json"
SEED = 20261019

def southern_solar_cycle(d:date):
    """Solar cycle begins after the Southern winter solstice (June 21)."""
    year = d.year if (d.month,d.day) > (6,21) else d.year-1
    rise_start,summer,finish = date(year,6,21),date(year,12,21),date(year+1,6,21)
    if rise_start < d < summer:
        return year,"rising"
    if summer < d < finish:
        return year,"falling"
    return None,None

def matched_pairs(ready):
    """Match opposite Southern summer-solstice branches without examining speeds."""
    early={d:v for d,v in ready.items() if v["branch"]=="rising"}
    late={d:v for d,v in ready.items() if v["branch"]=="falling"}
    edges=[]
    for d1,a in early.items():
        for d2,b in late.items():
            if (d2-d1).days < 30:continue
            gap=abs(daylength(a["lat"],d1)-daylength(b["lat"],d2))*60
            if gap > 5:continue
            if any(not 0.5 <= a["n_"+part]/b["n_"+part] <= 2 for part in ("day","night")):continue
            edges.append((gap,d1,d2))
    taken_r=set();taken_f=set();pairs=[]
    for mismatch,rising,falling in sorted(edges):
        if rising not in taken_r and falling not in taken_f:
            pairs.append((rising,falling))
            taken_r.add(rising);taken_f.add(falling)
    return pairs

def safe_unzip_data_csv(zip_path, csv_path):
    """Decompress one source primary CSV; never blindly extract ZIP directories."""
    with ZipFile(zip_path) as archive:
        members=[x for x in archive.infolist()
                 if not x.is_dir() and x.filename.lower().endswith(".csv")
                 and "reference-data" not in x.filename.lower()]
        if len(members)!=1:
            raise ValueError(f"ZIP contains {len(members)} candidate ORIGINAL CSVs")
        m=members[0]
        if m.file_size>1500000000 or m.file_size<128:
            raise ValueError("Unreasonable decompressed CSV size")
        total=0
        with archive.open(m) as src, csv_path.open("wb") as dest:
            while True:
                block=src.read(1024*1024)
                if not block:break
                total+=len(block)
                if total>1500000000:
                    raise ValueError("ZIP decompressed size exceeded")
                dest.write(block)
    return total

def analyze_south(source_path):
    tracks,n_rows,bad=load_events(source_path)
    day_data=defaultdict(lambda:{"day":[],"night":[],"lat":[]})
    intervals=qualified_intervals=0
    south_count=0
    for individual,records in tracks.items():
        records.sort(key=lambda v:v[0])
        for before,after in zip(records,records[1:]):
            intervals+=1
            v=valid_interval(before[0],before[1],before[2],after[0],after[1],after[2])
            if v is None:continue
            d,part,speed,hours,lat=v
            if lat>=0:continue
            qualified_intervals+=1
            day_data[(individual,d)][part].append(speed)
            day_data[(individual,d)]["lat"].append(lat)
    total_individuals=len(tracks)
    tracks.clear()
    by_year=defaultdict(dict)
    for (individual,d),a in day_data.items():
        if len(a["day"])<3 or len(a["night"])<3:continue
        y,branch=southern_solar_cycle(d)
        if y is None:continue
        lat=mean(a["lat"])
        if lat>=0:continue
        south_count+=1
        by_year[(individual,y)][d]={
            "day":median(a["day"]),"night":median(a["night"]),
            "n_day":len(a["day"]),"n_night":len(a["night"]),
            "lat":lat,"branch":branch
        }
    del day_data
    by_animal=defaultdict(list)
    covered_years=0
    matched_date_pairs=0
    individual_cycles_with_both_branches=0
    for (animal,cycle),daily in by_year.items():
        branches={x["branch"] for x in daily.values()}
        if branches!={"rising","falling"}:continue
        individual_cycles_with_both_branches+=1
        pairs=matched_pairs(daily)
        if len(pairs)<10:continue
        covered_years+=1
        matched_date_pairs+=len(pairs)
        pair_means=[]
        for before,after in pairs:
            a,b=daily[before],daily[after]
            delta_day=__import__("math").log1p(b["day"])-__import__("math").log1p(a["day"])
            delta_night=__import__("math").log1p(b["night"])-__import__("math").log1p(a["night"])
            pair_means.append((delta_night-delta_day,delta_day,delta_night))
        by_animal[animal].append(tuple(mean(v[i] for v in pair_means) for i in range(3)))
    effects=[tuple(mean(y[i] for y in years) for i in range(3)) for years in by_animal.values()]
    result={
        "source_rows":n_rows,"invalid_rows":bad,"reported_gps_individuals":total_individuals,
        "adjacent_step_candidates":intervals,"valid_south_solar_daypart_steps":qualified_intervals,
        "qualifying_individual_local_days":south_count,
        "cycles_with_both_branch_day_night_observations":individual_cycles_with_both_branches,
        "individual_cycles_ge10_matched_day_pairs":covered_years,
        "one_to_one_matched_day_pairs":matched_date_pairs,
        "qualifying_distinct_individuals":len(effects)
    }
    if len(effects)<5:
        return {**result,"effect_status":"insufficient_independent_animals","effect":None}
    rng=random.Random(SEED)
    point=mean(x[0] for x in effects)
    sims=sorted(mean(effects[rng.randrange(len(effects))][0] for _ in range(len(effects))) for _ in range(2000))
    return {**result,"effect_status":"exploratory_population_description","effect":{
        "n_individuals":len(effects),
        "n_positive":sum(x[0]>0 for x in effects),
        "n_negative":sum(x[0]<0 for x in effects),
        "n_zero":sum(x[0]==0 for x in effects),
        "mean_falling_minus_rising_log1p_night_over_day_kmh":point,
        "mean_falling_minus_rising_day_log1p_kmh":mean(x[1] for x in effects),
        "mean_falling_minus_rising_night_log1p_kmh":mean(x[2] for x in effects),
        "individual_cluster_bootstrap_95_percentile":[sims[49],sims[1949]],
        "warning":"Original GPS-step displacement, not true latent activity. Individual uncertainty is conditional on one archive/recruitment context; same-region fauna not an interaction experiment."
    }}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    full=json.loads(CATALOG.read_text(encoding="utf-8"))["packages"]
    assert c["version"]=="southern-solar-matched-mammal-gps-v0" and len(c["sources"])==3 and len(full)==437
    listed={x["package_uuid"]:x for x in full}
    results=[]
    for source in c["sources"]:
        label=source["label"]
        r={"source":label,"taxon":source["taxon"],"source_doi":source["doi"],"region":source["area"]}
        path=a.out/(label+".source")
        csvpath=a.out/(label+".csv")
        try:
            if source["package_uuid"] not in listed or source["taxon"] not in listed[source["package_uuid"]]["scientific_names"]:
                raise ValueError("Frozen frame source/taxon mismatch")
            files=original_files(source["package_uuid"])
            matches=[f for f in files if f["bitstream_uuid"]==source["provider_original_bitstream_uuid"]]
            if len(matches)!=1 or matches[0]["checksum"]["value"].lower()!=source["provider_original_md5"].lower() or matches[0]["bytes"]!=source["provider_original_bytes"]:
                raise ValueError("Provider source identity/MD5/bytes no longer match")
            r["source_digest_replayed"]=checksum_and_download(matches[0],path)
            if source["provider_filename"].endswith(".zip"):
                r["extracted_csv_bytes"]=safe_unzip_data_csv(path,csvpath)
            else:
                path.replace(csvpath)
            r.update(analyze_south(csvpath))
        except Exception as exc:
            r.update({"effect_status":"source_hold","error":f"{type(exc).__name__}: {exc}"})
        finally:
            path.unlink(missing_ok=True);csvpath.unlink(missing_ok=True)
        print("SOUTHERN_MAMMAL_SOLAR_RESULT "+json.dumps(r,sort_keys=True),flush=True)
        results.append(r)
    report={"scope":"Fixed-source Southern-Hemisphere descriptive ecological comparison; not a causal environmental test",
            "measurement":"Provider-MD5-verified original same-individual 0.5–2h GPS-step displacement",
            "sources":results}
    (a.out/"southern_three_source_grouped_results.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SOUTHERN_MAMMAL_SOLAR_SUMMARY "+json.dumps({
        "total_sources":len(results),
        "with_supported_effect":sum(x.get("effect_status")=="exploratory_population_description" for x in results),
        "source_or_support_holds":sum(x.get("effect_status")!="exploratory_population_description" for x in results)
    },sort_keys=True),flush=True)

if __name__=="__main__":
    main()
