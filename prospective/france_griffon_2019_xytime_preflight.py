#!/usr/bin/env python3
"""2019–2021 French Gyps raw GPS: ALTITUDE-BLIND tracking support audit.

Input is the MD5-pinned 1.09GB public Dataverse ZIP, 9 native CSV seasons.
Uses ONLY non-height fields: bird/tag/timestamp/XY/speed/GPS HDOP/satellites,
with earliest five-minute-bin time selection before any height QC.

Never accesses 'height-above-msl' or 'bar:barometric-height' row values.
The result may identify structural suitability but is NOT a biological
height individuality or environmental reaction test.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from datetime import date
from pyproj import Transformer

SOURCE_ZIP="windTurbineAvoidance.zip"
SOURCE_MD5="b18cc8004d311d19ff24060f655178bf"
SOURCE_BYTES=1093170227
TAXON="Gyps fulvus"
# Native source lists a non-animal instrument/geodesy test as an individual.
# Its literal label was identified in the outcome-blind initial source roster.
NON_BIOLOGICAL_SOURCE_IDS={"Test géodésie ornitela"}
PATTERN=re.compile(r"Vulturestracks_(Jan_to_May|Jun_to_Aug|Sep_to_Dec)(2019|2020|2021)\.csv$")
REQUIRED={
 "timestamp","individual-local-identifier","tag-local-identifier",
 "individual-taxon-canonical-name","location-long","location-lat",
 "ground-speed","visible","import-marked-outlier",
 "gps:hdop","gps:satellite-count"
}
THIN_MINUTES=5
SPEED_LOW=5.
SPEED_HIGH=55.
GRIDS=(5000,50000)
MIN_DONOR_EVENTS=10
MIN_SCORED_DAY_EVENTS=20
MIN_INDEPENDENT_DAYS=2
MIN_BIRDS=10
PROJECTOR=Transformer.from_crs("EPSG:4326","EPSG:6933",always_xy=True)


def numeric(v):
    try:val=float(v)
    except (ValueError,TypeError):return None
    return val if math.isfinite(val) else None


def source_digest(path):
    if path.name!=SOURCE_ZIP or path.stat().st_size!=SOURCE_BYTES:
        raise ValueError("Frozen original Dataverse archive filename or bytes changed")
    digest=hashlib.md5()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            digest.update(b)
    if digest.hexdigest()!=SOURCE_MD5:
        raise ValueError("Original public source MD5 mismatch")
    return digest.hexdigest()


def select_rows(rows,first,counters,seen_tags,studies,source_year):
    """Streaming native tuple rows; only nonheight field indexes are used."""
    names=next(rows)
    fields={v:i for i,v in enumerate(names)}
    if not REQUIRED<=set(fields):
        raise ValueError("Source GPS CSV absent frozen nonheight fields "+
                         repr(sorted(REQUIRED-set(fields))))
    def item(row,key):
        p=fields[key]
        return row[p] if p<len(row) else ""
    for row in rows:
        counters["raw_rows"]+=1
        bird=item(row,"individual-local-identifier").strip()
        if not bird:
            counters["no_bird_id"]+=1;continue
        if bird in NON_BIOLOGICAL_SOURCE_IDS:
            counters["nonbiological_instrument_test_rows_quarantined"]+=1
            continue
        if item(row,"individual-taxon-canonical-name").strip()!=TAXON:
            counters["non_target_taxon"]+=1;continue
        if item(row,"visible").strip().lower()=="false" or \
          item(row,"import-marked-outlier").strip().lower() in ("true","1","yes","y"):
            counters["source_outlier_or_invisible"]+=1;continue
        stamp=item(row,"timestamp").strip()
        try:
            year=int(stamp[:4]);month=int(stamp[5:7]);day=int(stamp[8:10])
            hour=int(stamp[11:13]);minute=int(stamp[14:16])
            date(year,month,day)
        except (ValueError,TypeError):
            counters["bad_timestamp"]+=1;continue
        if year!=source_year or not(0<=hour<24 and 0<=minute<60):
            counters["unexpected_year_or_time"]+=1;continue
        lon=numeric(item(row,"location-long"))
        lat=numeric(item(row,"location-lat"))
        speed=numeric(item(row,"ground-speed"))
        if lon is None or lat is None or speed is None or not(-180<=lon<=180 and -85<=lat<=85):
            counters["bad_xy_speed"]+=1;continue
        if not(SPEED_LOW<=speed<=SPEED_HIGH):
            counters["outside_flight_speed_proxy"]+=1;continue
        tag=item(row,"tag-local-identifier").strip()
        if tag:seen_tags[bird].add(tag)
        study=item(row,"study-name").strip() if "study-name" in fields else ""
        if study:studies[study].add(bird)
        hdop=numeric(item(row,"gps:hdop"))
        satellites=numeric(item(row,"gps:satellite-count"))
        key=(bird,stamp[:10],hour*12+minute//THIN_MINUTES)
        original=first.get(key)
        if original is None or stamp<original[0]:
            first[key]=(stamp,lon,lat,hdop,satellites,tag)
        counters["raw_speed_qualified"]+=1


def fixed_support(count):
    by_bc=Counter();by_c=Counter();by_dc=Counter()
    for (bird,day,cell),n in count.items():
        by_bc[bird,cell]+=n
        by_c[cell]+=n
        by_dc[day,cell]+=n
    by_bd=Counter()
    for (bird,day,cell),n in count.items():
        other_own=by_bc[bird,cell]-n
        other_bird_other_day=by_c[cell]-by_bc[bird,cell]-by_dc[day,cell]+n
        if other_own>=MIN_DONOR_EVENTS and other_bird_other_day>=MIN_DONOR_EVENTS:
            by_bd[bird,day]+=n
    days=Counter()
    for (bird,day),n in by_bd.items():
        if n>=MIN_SCORED_DAY_EVENTS:
            days[bird]+=1
    eligible={b for b,n in days.items() if n>=MIN_INDEPENDENT_DAYS}
    return {
       "n_unique_birds_with_qualifying_day_events":len(eligible),
       "bird_days_scored":sum(days[b] for b in eligible),
       "scored_five_minute_GPS_fixes":sum(n for (b,d),n in by_bd.items()
                    if b in eligible and n>=MIN_SCORED_DAY_EVENTS),
       "admitted":len(eligible)>=MIN_BIRDS,
       "source_bird_ID_sha256":hashlib.sha256("\n".join(sorted(eligible)).encode()).hexdigest(),
       "admitted_bird_ids":sorted(eligible),
       "observed_coarse_cells":len(by_c),
       "all_scorable_bird_days_before_two_day_gate":sum(n>=MIN_SCORED_DAY_EVENTS for n in by_bd.values())
    }


def analyze(first,counters,tags,study_names):
    by_year=defaultdict(lambda:{
       "birds":set(),"five_minute_events":0,"days":set(),
       "hdop":0,"satellites":0})
    gridcounters={scale:Counter() for scale in GRIDS}
    bird_day_all=Counter()
    for (bird,day,k),(stamp,lon,lat,hdop,satellites,tag) in first.items():
        year=day[:4];obj=by_year[year]
        obj["birds"].add(bird);obj["five_minute_events"]+=1
        obj["days"].add((bird,day))
        obj["hdop"]+=hdop is not None
        obj["satellites"]+=satellites is not None
        bird_day_all[bird,day]+=1
        x,y=PROJECTOR.transform(lon,lat)
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("Previously valid WGS84 event has invalid EPSG6933 transform")
        for scale in GRIDS:
            gridcounters[scale][bird,day,(math.floor(x/scale),math.floor(y/scale))]+=1
    return {
        "phase":"FRENCH_GYPS_2019_2021_XYTIME_INSTRUMENT_ONLY_PREHEIGHT",
        "source_zip_md5":SOURCE_MD5,
        "selected_native_GPS_five_minute_events":len(first),
        "source_raw_row_audit":dict(counters),
        "selected_biological_animals":len({k[0] for k in first}),
        "selected_animal_days":len(bird_day_all),
        "distinct_source_study_name_labels":{name:len(birds)
                  for name,birds in sorted(study_names.items())},
        "animals_with_more_than_one_tag_ID":sum(len(s)>1 for s in tags.values()),
        "animals_with_any_tag_ID":len(tags),
        "n_distinct_tag_IDs":len({t for vals in tags.values() for t in vals}),
        "quarantined_nonbiological_animal_IDs":sorted(NON_BIOLOGICAL_SOURCE_IDS),
        "birds_missing_any_native_tag_id":sorted({bird for bird,day,k in first if bird not in tags}),
        "tags_aliased_to_multiple_biological_bird_IDs":{
            tag:sorted(birds) for tag,birds in sorted(
                {tag:{bird for bird,tset in tags.items() if tag in tset}
                 for vals in tags.values() for tag in vals}.items())
            if len(birds)>=2
        },
        "selected_animal_IDs":sorted({k[0] for k in first}),
        "record_quality_by_year":{
          year:{
              "birds":len(obj["birds"]),
              "bird_days":len(obj["days"]),
              "five_minute_selected":obj["five_minute_events"],
              "fraction_with_HDOP_numeric":obj["hdop"]/obj["five_minute_events"],
              "fraction_with_satellites_numeric":obj["satellites"]/obj["five_minute_events"]
          } for year,obj in sorted(by_year.items())
        },
        "horizontal_day_eligibility_by_cell_m":{
           str(scale):fixed_support(counter)
           for scale,counter in sorted(gridcounters.items())
        },
        "native_GPS_MSL_height_column_exists":True,
        "native_barometric_height_column_exists":True,
        "numeric_native_GPS_height_values_read":False,
        "numeric_barometric_height_values_read":False,
        "height_completeness_used_for_selection":False,
        "ecological_height_identity_or_wind_response_tested":False,
        "source_parent_overlap_resolved":False,
        "source_independence_claim":"UNVERIFIED pending exact Movebank original parent ID/individual-tag crosswalk",
        "biological_interpretation_guard":"Ordinary motion/XY/time support is a sampling feasibility result, not a biological claim that identity or thermals drive altitude."
    }


def original_zip_scan(path):
    source_digest(path)
    counters=Counter();first={};tags=defaultdict(set);studies=defaultdict(set)
    with zipfile.ZipFile(path) as z:
        members=[i for i in z.infolist()
                 if not i.is_dir()
                 and PATTERN.search(i.filename)
                 and not i.filename.startswith("__MACOSX/")]
        if len(members)!=9:
            raise ValueError("Exactly nine original 2019–2021 seasonal GPS CSVs required")
        by_year=Counter()
        for info in sorted(members,key=lambda x:x.filename):
            source_year=int(PATTERN.search(info.filename).group(2))
            by_year[str(source_year)]+=1
            with z.open(info) as binary:
                with io.TextIOWrapper(binary,encoding="utf-8-sig",errors="replace",newline="") as f:
                    select_rows(csv.reader(f),first,counters,tags,studies,source_year)
            print("Processed",info.filename,
                  "eligible_native_first_5min_so_far",len(first),flush=True)
    if dict(by_year)!={"2019":3,"2020":3,"2021":3}:
        raise ValueError("Expected each original source year to have three seasons")
    result=analyze(first,counters,tags,studies)
    result["source_seasons_by_year"]=dict(by_year)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    opt=parser.parse_args()
    result=original_zip_scan(opt.source)
    opt.out.parent.mkdir(parents=True,exist_ok=True)
    opt.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
       "selected_birds":result["selected_biological_animals"],
       "native_tag_reuse_birds":result["animals_with_more_than_one_tag_ID"],
       "xy_years":{k:v["birds"] for k,v in result["record_quality_by_year"].items()},
       "5km_birds":result["horizontal_day_eligibility_by_cell_m"]["5000"]["n_unique_birds_with_qualifying_day_events"],
       "50km_birds":result["horizontal_day_eligibility_by_cell_m"]["50000"]["n_unique_birds_with_qualifying_day_events"],
       "native_height_opened":False
    },sort_keys=True))

if __name__=="__main__":
    main()
