#!/usr/bin/env python3
"""Authenticated original Zenodo Bat-camera × nectar LOO plant source.

Original-data numerical values are opened ONLY AFTER the v2 frozen protocol
and synthetic known-truth tests. The source is observational and 1 forest.
"""
from __future__ import annotations
from collections import defaultdict
from decimal import Decimal,InvalidOperation
import hashlib, json, math
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen

from odsp.nectarivore_bat_resource_transfer_v2 import Plant,Layer,evaluate
from scripts.nectarivore_zenodo_author_id_bat_effort_v1_3 import (
    camera_plant_key,nectar_plant_key,positive_effort
)
from scripts.nectarivore_zenodo_source_v1_1_pairs import (
    FILES,read_source_allowed_columns
)

EXPECTED_ORIGINAL_CAMERA_ROWS=180
EXPECTED_ORIGINAL_NECTAR_ROWS=40
EXPECTED_ACTIVE_PAIRED_PLANTS=9
EXPECTED_ACTIVE_PAIRED_STRATA=26
RECORD="10527420"


def download_original(name):
    source_md5,source_sha,sheet,allowed=FILES[name]
    url=f"https://zenodo.org/records/{RECORD}/files/{quote(name)}?download=1"
    with urlopen(Request(url,headers={
        "User-Agent":"odsp-nectarivore-v2-preregistered-plant-score/1.0",
    }),timeout=120) as response:
        data=response.read(120_001)
    if hashlib.sha256(data).hexdigest()!=source_sha or hashlib.md5(data).hexdigest()!=source_md5:
        raise ValueError("original author file identity failure")
    return data,sheet


def parse_integer(x):
    try:d=Decimal(str(x).strip())
    except InvalidOperation as exc:raise ValueError("SOURCE_RESPONSE_STOP: invalid Bat camera Abundance") from exc
    if not d.is_finite() or d<0 or d!=d.to_integral_value():
        raise ValueError("SOURCE_RESPONSE_STOP: Bat visit Abundance must be nonnegative integer")
    return int(d)


def parse_resource(x):
    try:v=float(str(x).strip())
    except (ValueError,TypeError) as exc:raise ValueError("SOURCE_RESPONSE_STOP: nonnumeric nectar quantity") from exc
    if not math.isfinite(v) or v<0:
        raise ValueError("SOURCE_RESPONSE_STOP: nectar quantity must be finite and nonnegative")
    return v


def get_qualified_original_plant_profiles(cam_rows,nectar_rows):
    if len(cam_rows)!=EXPECTED_ORIGINAL_CAMERA_ROWS or len(nectar_rows)!=EXPECTED_ORIGINAL_NECTAR_ROWS:
        raise ValueError("original source table row counts changed")
    nectar_group=defaultdict(list)
    for r in nectar_rows:
        key=(nectar_plant_key(r["ML_ID"]),r["Stratum"])
        if r["Stratum"] not in {"Low","Middle","High"}:
            raise ValueError("unexpected nectar strata")
        nectar_group[key].append(r)
    source_qualified={}
    for r in cam_rows:
        if r["Taxa"]!="Bat":
            continue
        plant=camera_plant_key(r["ML_ID"])
        stratum=r["Stratum"]
        if stratum not in {"Low","Middle","High"}:
            raise ValueError("unknown Bat camera layer")
        if not positive_effort(r["Hours"]) or not positive_effort(r["Inflorescences"]):
            continue   # pre-registered SOURCE-ONLY effort eligibility, not response filtering
        key=(plant,stratum)
        if key not in nectar_group:
            continue
        if key in source_qualified:
            raise ValueError("Bat source plant×layer duplicated unexpectedly")
        source_qualified[key]=r
    by_plant=defaultdict(list)
    for (plant,stratum),r in source_qualified.items():
        by_plant[plant].append(stratum)
    selected={plant for plant,z in by_plant.items() if len(z)>=2}
    selected_rows=[(plant,z,source_qualified[(plant,z)])
                   for plant in sorted(selected,key=int) for z in ("Low","Middle","High")
                   if (plant,z) in source_qualified]
    if len(selected)!=EXPECTED_ACTIVE_PAIRED_PLANTS or len(selected_rows)!=EXPECTED_ACTIVE_PAIRED_STRATA:
        raise ValueError("original v1.3 plant-height-effort eligibility structure no longer matches")
    profiles=defaultdict(list)
    for plant,z,r in selected_rows:
        num=parse_integer(r["Abundance"])
        resource_values=[parse_resource(v["Nect_quant_mean"])
                         for v in nectar_group[(plant,z)]]
        if not resource_values:
            raise ValueError("SOURCE_RESPONSE_STOP: original nectar value absent for qualified source strata")
        nectar=sum(resource_values)/len(resource_values)
        exposure=float(r["Hours"])*float(r["Inflorescences"])
        profiles[plant].append(Layer(z,exposure,nectar,num))
    return [Plant(pid,tuple(profiles[pid])) for pid in sorted(profiles,key=int)]


def main():
    path=Path("results/nectarivore_bat_plant_resource_transfer_v2.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    result={
        "status":"SOURCE_ORIGINAL_DATA_STOP",
        "original_numeric_bat_and_nectar_response_access_attempted":True,
        "source_plant_IDs_not_released":True,
    }
    try:
        b,s=download_original("CameraTraps.xlsx")
        r,s2=download_original("Nectar measurements_Strata.xlsx")
        cam=read_source_allowed_columns(b,s,(
            "ML_ID","Taxa","Stratum","Hours","Inflorescences","Abundance"))
        nectar=read_source_allowed_columns(r,s2,(
            "ML_ID","Stratum","Year","Nect_quant_mean"))
        profiles=get_qualified_original_plant_profiles(cam,nectar)
        out=evaluate(profiles)
        result={
          "source":"Thiel et al 2024 American Journal of Botany",
          "source_doi":"10.5281/zenodo.10527420",
          "paper_doi":"10.1002/ajb2.16303",
          "original_zenodo_file_checksum":{n:FILES[n][1] for n in (
              "CameraTraps.xlsx","Nectar measurements_Strata.xlsx")},
          "preoutcome_contract":"docs/nectarivore_zenodo_bat_nectar_plant_holdout_v2_preoutcome.md",
          "source_plants_original_IDs_not_exported":True,
          "original_source_numeric_Abundance_and_Nect_quant_mean_opened":True,
          "original_camera_plant_years_not_dated":True,
          "prior_author_resource_visit_association_published":True,
          "no_species_level_bat_3d_SDM":True,
          "result":out,
        }
    except Exception as exc:
        result.update({
            "status":"SOURCE_ORIGINAL_DATA_OR_RESPONSE_STOP",
            "stop_exception":type(exc).__name__,
            "stop_reason":str(exc)[:350],
            "no_subset_fallback_or_scientific_effect_after_STOP":True,
        })
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
