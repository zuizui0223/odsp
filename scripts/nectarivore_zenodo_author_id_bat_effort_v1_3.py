#!/usr/bin/env python3
"""Source-known Marcgravia ID reconciliation + Bat-only effort qualification.

Original author Explanations in Camera and Nectar sheets both identify ML_ID
as Marcgravia individual. Canonical MLNN ↔ NN matching was preregistered before
numerical Bat visits, nectar volume, sugar/pH or mist-net effects were opened.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import json, math, re
from pathlib import Path

from scripts.nectarivore_zenodo_source_v1_1_pairs import original_files

LAYERS={"Low","Middle","High"}


def camera_plant_key(s):
    value=str(s).strip()
    m=re.fullmatch(r"ML0*([1-9][0-9]*)",value)
    if not m:raise ValueError("source camera plant ID outside source-documented MLnn grammar")
    return str(int(m.group(1)))


def nectar_plant_key(s):
    v=str(s).strip()
    if not re.fullmatch(r"[1-9][0-9]*",v):
        raise ValueError("source nectar plant ID outside integer grammar")
    return str(int(v))


def positive_effort(v):
    try:
        x=float(str(v).strip())
    except (TypeError,ValueError):
        return False
    return math.isfinite(x) and x>0


def audit(tables,files):
    cam=tables["CameraTraps.xlsx"]
    nectar=tables["Nectar measurements_Strata.xlsx"]
    net=tables["Mist-netting_bats.xlsx"]
    mapped={}
    for source,rows,keyer in (("camera",cam,camera_plant_key),
                               ("nectar",nectar,nectar_plant_key)):
        originals={r["ML_ID"] for r in rows if r.get("ML_ID")}
        linked={keyer(v) for v in originals}
        if len(linked)!=len(originals):
            raise ValueError("source plant ID mapping collision")
        mapped[source]=linked
    for r in cam:
        if r["Stratum"] not in LAYERS:
            raise ValueError("camera categorical forest layer not in original three")
    for r in nectar:
        if r["Stratum"] not in LAYERS:
            raise ValueError("nectar categorical forest layer not in original three")

    camera_pairs={(camera_plant_key(r["ML_ID"]),r["Stratum"])
                  for r in cam}
    nectar_pairs={(nectar_plant_key(r["ML_ID"]),r["Stratum"])
                  for r in nectar}
    matched=camera_pairs & nectar_pairs
    by_plant=defaultdict(set)
    for ident,layer in matched:by_plant[ident].add(layer)

    negative_camera_effort=Counter()
    negative_bat_inflorescences=Counter()
    count_design=Counter()
    bat_with_valid_exposure=set()
    bat_rows=0
    all_bat_plant_ids=set()
    for r in cam:
        group=r["Taxa"]
        z=r["Stratum"]
        key=(camera_plant_key(r["ML_ID"]),z,group)
        count_design[key]+=1
        if not positive_effort(r["Hours"]):
            negative_camera_effort[(group,z)]+=1
        if group=="Bat":
            bat_rows+=1
            all_bat_plant_ids.add(key[0])
            if not positive_effort(r["Inflorescences"]):
                negative_bat_inflorescences[z]+=1
            if positive_effort(r["Hours"]) and positive_effort(r["Inflorescences"]):
                bat_with_valid_exposure.add(key[:2])
    bat_paired=bat_with_valid_exposure & nectar_pairs
    bat_by_plant=defaultdict(set)
    for k,z in bat_paired:bat_by_plant[k].add(z)

    # Show original labels/effort structure, never original ecological counts.
    source_taxa_counts=dict(Counter(r["Taxa"] for r in cam))
    missing_effort=[{"Taxa":t,"Stratum":z,"n_nonpositive_or_not_numeric_Hours":n}
                    for (t,z),n in sorted(negative_camera_effort.items())]
    invalid_inf=[{"stratum":z,"n_nonpositive_or_not_numeric_inflorescences":n}
                 for z,n in sorted(negative_bat_inflorescences.items())]
    original_years=sorted({r["Year"] for r in nectar if r.get("Year")})
    paired_ge2=sum(len(v)>=2 for v in bat_by_plant.values())
    paired_ge3=sum(len(v)>=3 for v in bat_by_plant.values())
    status="canonical_plant_ID_and_Bat_effort_source_admitted" if (
        paired_ge2>=5 and not any(t=="Bat" for (t,z) in negative_camera_effort)
        and not negative_bat_inflorescences
        and len([v for v in count_design.values() if v>1])==0
    ) else "source_plant_Bat_effort_or_duplicate_key_hold"

    return {
        "status":status,
        "source_file_sha256s":{k:v["original_sha256"] for k,v in files.items()},
        "canonical_ID_mapping":"ML0*(positive integer) in Camera to positive integer in Nectar",
        "original_explanation_supports_equivalence_of_ML_ID":True,
        "original_camera_plant_IDs":len(mapped["camera"]),
        "original_nectar_plant_IDs":len(mapped["nectar"]),
        "original_plant_IDs_shared_after_author_id_normalization":len(mapped["camera"]&mapped["nectar"]),
        "paired_plant_layer_units_after_normalization":len(matched),
        "plants_with_at_least_two_paired_layers_before_effort":sum(len(v)>=2 for v in by_plant.values()),
        "plants_with_all_three_paired_layers_before_effort":sum(len(v)>=3 for v in by_plant.values()),
        "bat_camera_rows":bat_rows,
        "Bat_camera_plants":len(all_bat_plant_ids),
        "Bat_camera_plant_layer_units_with_positive_Hours_and_inflorescences":len(bat_with_valid_exposure),
        "Bat_camera_plant_layer_units_paired_with_nectar":len(bat_paired),
        "Bat_camera_plants_with_at_least_two_paired_resource_layers":paired_ge2,
        "Bat_camera_plants_with_all_three_paired_resource_layers":paired_ge3,
        "camera_taxa_original_row_counts_design_only":source_taxa_counts,
        "camera_Hours_nonpositive_or_nonnumeric_by_source_taxa_layer":missing_effort,
        "Bat_inflorescences_nonpositive_or_nonnumeric_by_layer":invalid_inf,
        "source_camera_taxon_plant_layer_duplicate_key_groups":sum(v>1 for v in count_design.values()),
        "nectar_source_year_codes":original_years,
        "nectar_year_not_documented_in_original_CameraTraps_Data_sheet":True,
        "mistnet_source_event_rows_metadata_only":len(net),
        "original_visit_count_nectar_quantity_sugar_pH_bat_capture_association_opened":False,
        "no_latent_3D_species_SDM_or_q_calibration":True,
    }


def main():
    path=Path("results/nectarivore_zenodo_author_ID_Bat_effort_v1_3.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        tables,files=original_files()
        result=audit(tables,files)
    except Exception as e:
        result={
            "status":"source_identity_or_structure_stop",
            "error_type":type(e).__name__,"reason":str(e)[:400],
            "original_visit_count_nectar_quantity_sugar_pH_bat_capture_association_opened":False,
        }
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
