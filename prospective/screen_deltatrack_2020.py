#!/usr/bin/env python3
"""Outcomes-blind x-y / time screening for two DELTATRACK gull species (2020).

Reads UTC timestamps, GPS position, animal/species IDs, ground speed and source
outlier marks. Deliberately does NOT access height-above-msl or any derived
vertical distribution. Species may never act as each other's comparison pool.
"""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

from pyproj import Transformer

from prospective.screen_gull_event_support import (
    GRID_METERS, MIN_EVENTS_PER_DAY, MIN_TRAIN_PER_CELL,
    MIN_OTHER_PER_CELL, MIN_REPEATED_DAYS, MIN_ELIGIBLE_ANIMALS_SOURCE,
    PRIMARY_MONTHS, PRIMARY_SPEED_MS, truthy_outlier, utc_day_and_bin,
)

SPECIES=("Larus argentatus","Larus fuscus")
SOURCE_FILE="DELTATRACK-gps-2020.csv.gz"
YEAR=2020
MAX_SPEED=55.0


def audit(path:Path)->dict:
    if path.name!=SOURCE_FILE:
        raise ValueError("Only frozen 2020 archive is admitted for this source")
    transformer=Transformer.from_crs("EPSG:4326","EPSG:32631",always_xy=True)
    earliest={}
    events=Counter()
    outliers={"manually-marked-outlier","import-marked-outlier"}
    with gzip.open(path,"rt",encoding="utf-8-sig",newline="") as f:
        rows=csv.DictReader(f)
        fields=set(rows.fieldnames or ())
        required={"timestamp","individual-local-identifier","individual-taxon-canonical-name",
                  "location-long","location-lat","ground-speed"}
        if not required.issubset(fields):
            raise ValueError("Required non-altitude columns missing "+str(required-fields))
        marks=outliers&fields
        for row in rows:
            events["total_source_rows"]+=1
            species=(row.get("individual-taxon-canonical-name") or "").strip()
            if species not in SPECIES:
                events["other_or_missing_taxon"]+=1
                continue
            events[species+":source_rows"]+=1
            if any(truthy_outlier(row.get(k,"")) for k in marks):
                events[species+":source_outliers"]+=1
                continue
            time=utc_day_and_bin(row.get("timestamp",""))
            if time is None:
                events[species+":time_invalid"]+=1
                continue
            day,bin5,month=time
            if int(day[:4]) != YEAR or month not in PRIMARY_MONTHS:
                events[species+":outside_window"]+=1
                continue
            animal=(row.get("individual-local-identifier") or "").strip()
            if not animal:
                events[species+":no_individual_id"]+=1
                continue
            try:
                lat=float(row["location-lat"])
                lon=float(row["location-long"])
                speed=float(row["ground-speed"])
            except (ValueError,TypeError):
                events[species+":missing_xy_or_speed"]+=1
                continue
            if not all(map(math.isfinite,(lon,lat,speed))) or not(-90<=lat<=90 and -180<=lon<=180):
                events[species+":nonfinite_or_invalid_xy_speed"]+=1
                continue
            events[species+":pre_flight_rows"]+=1
            if not PRIMARY_SPEED_MS <= speed <= MAX_SPEED:
                events[species+":not_flight_speed"]+=1
                continue
            x,y=transformer.transform(lon,lat)
            if not(math.isfinite(x) and math.isfinite(y)):
                events[species+":projection_failed"]+=1
                continue
            cell=(math.floor(x/GRID_METERS),math.floor(y/GRID_METERS))
            stamp=(row.get("timestamp") or "").strip()
            key=(species,animal,day,bin5)
            prev=earliest.get(key)
            if prev is None or stamp<prev[0]:
                earliest[key]=(stamp,cell)
            events[species+":flight_proxy_raw_events"]+=1

    by_species={}
    for species in SPECIES:
        by_day_cell=Counter()
        by_ind_cell=Counter()
        by_cell=Counter()
        animals=set()
        for (sp,animal,day,_),(_,cell) in earliest.items():
            if sp!=species:
                continue
            animals.add(animal)
            by_day_cell[animal,day,cell]+=1
            by_ind_cell[animal,cell]+=1
            by_cell[cell]+=1
        day_scorable=Counter()
        for (animal,day,cell),n in by_day_cell.items():
            if (by_ind_cell[animal,cell]-n>=MIN_TRAIN_PER_CELL
                and by_cell[cell]-by_ind_cell[animal,cell]>=MIN_OTHER_PER_CELL):
                day_scorable[animal,day]+=n
        repeated=Counter()
        for (animal,day),n in day_scorable.items():
            if n>=MIN_EVENTS_PER_DAY:
                repeated[animal]+=1
        eligible={animal for animal,n in repeated.items() if n>=MIN_REPEATED_DAYS}
        by_species[species]={
            "source_rows":events[species+":source_rows"],
            "raw_flight_proxy_events":events[species+":flight_proxy_raw_events"],
            "flight_proxy_unique_5min_bins":sum(sp==species for sp,*_ in earliest),
            "animals_with_any_5min_flight":len(animals),
            "animals_with_two_scorable_days":len(eligible),
            "scorable_days":sum(n>=MIN_EVENTS_PER_DAY and bird in eligible for (bird,day),n in day_scorable.items()),
            "5km_cells":len(by_cell),
            "structural_species_potential":len(eligible)>=MIN_ELIGIBLE_ANIMALS_SOURCE,
            "eligible_ids_fingerprint":hashlib.sha256("\n".join(sorted(eligible)).encode()).hexdigest(),
            "outlier_events":events[species+":source_outliers"],
        }

    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return {
        "endpoint":"deltatrack-2020-xytime-structural-gate-v1",
        "frozen_source":"https://zenodo.org/records/22102508",
        "gps_filename":path.name,
        "gz_sha256":h.hexdigest(),
        "source_total_rows":events["total_source_rows"],
        "other_or_missing_taxon_rows":events["other_or_missing_taxon"],
        "species":by_species,
        "altitude_values_opened":False,
        "altitude_outcomes_tested":False,
        "terminal":"source_structural_screen_complete",
        "claim_boundary":"No positive/negative ecological conclusion about individual flight-altitude shape",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gps",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    opt=p.parse_args()
    result=audit(opt.gps)
    opt.out.parent.mkdir(parents=True,exist_ok=True)
    opt.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:{"individuals":v["animals_with_two_scorable_days"],
                        "potential":v["structural_species_potential"],
                        "5min_bins":v["flight_proxy_unique_5min_bins"]}
                      for k,v in result["species"].items()},sort_keys=True))


if __name__=="__main__":
    main()
