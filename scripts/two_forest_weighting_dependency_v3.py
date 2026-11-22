#!/usr/bin/env python3
"""Two independent forests: published-source-open descriptive reference weights.

Published temperate 2014 original OAI JATS Table 1 vs tropical 2020 Zenodo v1
original count cells. NO new heldout geographic sites and NO calibrated sensor q.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen

from odsp.recorded_layer_weighting_v3 import observed_two_layer_weighting
from scripts.froidevaux2014_original_vertical_table_v1 import (
    parse_primary_table,
)
from scripts.froidevaux2014_pmc_oai_table_v2 import (
    URL as FROIDEVAUX_OAI_URL, extract_jats,
)
from scripts.gomes_zenodo_number_weighted_v4 import (
    parse_original,
    SOURCE_SHA256 as GOMES_SHA256,
)
from scripts.gomes_zenodo_vertical_source_preflight_v1 import (
    URL as GOMES_URL,
)

TARGET_YEAR="2026-11-23"
FROIDEVAUX_PUBLISHED_EXPECTED_GROUND=41850
FROIDEVAUX_PUBLISHED_EXPECTED_CANOPY=35630
GOMES_RETAINED_EXPECTED_TOTAL=16115
DOMINANT="pipistrellus pipistrellus"


def load_original_sources():
    with urlopen(Request(FROIDEVAUX_OAI_URL,headers={
        "User-Agent":"odsp-two-forest-reference-measures-v3/1.0",
        "Accept":"application/xml",
    }),timeout=120) as r:
        raw_oai=r.read(4_000_001)
    if len(raw_oai)>4_000_000:
        raise RuntimeError("official OAI response too large")
    original_froidevaux_xml=extract_jats(raw_oai)
    fr,meta=parse_primary_table(original_froidevaux_xml)
    if (sum(x["ground"] for x in fr)!=FROIDEVAUX_PUBLISHED_EXPECTED_GROUND
        or sum(x["canopy"] for x in fr)!=FROIDEVAUX_PUBLISHED_EXPECTED_CANOPY):
        raise RuntimeError("Froidevaux table no longer agrees with published source")

    with urlopen(Request(GOMES_URL,headers={
        "User-Agent":"odsp-two-forest-reference-measures-v3/1.0",
    }),timeout=120) as r:
        raw_gomes=r.read(4_000_001)
    gomes=parse_original(raw_gomes)
    return fr,meta,raw_oai,original_froidevaux_xml,gomes,raw_gomes


def summarize_sources(fr,meta,raw_oai,raw_jats,original_gomes,raw_gomes):
    swiss={r["taxon"]:(r["ground"],r["canopy"]) for r in fr}
    swiss_without_dominant={
        label:v for label,v in swiss.items()
        if " ".join(label.lower().split())!=DOMINANT
    }
    if len(swiss)!=16 or len(swiss_without_dominant)!=15:
        raise RuntimeError("frozen Swiss full/dominant-excluded source roster mismatch")

    gomes_all=defaultdict(Counter)
    for rec in original_gomes:
        gomes_all[rec.label][rec.position]+=rec.number
    if len(gomes_all)!=21:
        raise RuntimeError("Gomes original labels changed")
    eligible={label for label,c in gomes_all.items() if sum(c.values())>5}
    gomes={
        label:(gomes_all[label]["below"],gomes_all[label]["above"])
        for label in sorted(eligible)
    }
    if len(gomes)!=17 or sum(sum(v) for v in gomes.values())!=GOMES_RETAINED_EXPECTED_TOTAL:
        raise RuntimeError("original Gomes author rule or counts changed")

    return {
        "status":"original_sources_verified_two_forest_reference_sensitivity_descriptive",
        "research_start":"post_publication_and_prior_original_outcome_v3_descriptive",
        "no_new_unopened_source_holdout":True,
        "no_bat_position_or_detection_q_calibration":True,
        "independent_source_count":2,
        "temperate_swiss": {
            "doi":"10.1002/ece3.1296",
            "pmcid":"PMC4278821",
            "retrieval":"official_NCBI_OAI_fulltext_xml",
            "oai_response_sha256":hashlib.sha256(raw_oai).hexdigest(),
            "original_jats_sha256":hashlib.sha256(raw_jats).hexdigest(),
            "source_table_caption":meta["table_caption"],
            "ground_canopy_all_published_labels":observed_two_layer_weighting(swiss),
            "ground_canopy_excluding_author_noted_dominant":observed_two_layer_weighting(swiss_without_dominant),
            "forest_gap_published_source_sequences_excluded_from_vertical_binary":sum(r["gap"] for r in fr),
            "records_are_pooled_across_32_plots":True,
        },
        "tropical_french_guiana": {
            "doi":"10.5281/zenodo.4019867",
            "retrieval":"original_Zenodo_v1_checksum_pinned_Bats.csv",
            "original_file_sha256":hashlib.sha256(raw_gomes).hexdigest(),
            "source_original_label_count":len(gomes_all),
            "original_author_total_gt5_eligible_labels":len(gomes),
            "below_above_original_author_eligible_labels":observed_two_layer_weighting(gomes),
            "original_v4_conditioned_on_hour_I_nats":0.17613037973692044,
            "this_result_is_unconditional_and_NOT_numerically_identical_to_v4_I":True,
            "source_is_2_local_towers_only_180m_apart":True,
        },
        "claims":[
            "observed detector layers, not organism flight height",
            "mass-weighted and label-equal are distinct reference populations",
            "positive label-layer information might be generated by label×recorder detection differences",
            "paired original forest locations are not independently held out in this descriptive table contrast",
            "source richness, instrument heights and acoustic labels differ; not a cross-species SDM transfer",
        ],
    }


def main():
    output=Path("results/two_forest_weighting_dependency_v3.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    try:
        report=summarize_sources(*load_original_sources())
    except Exception as exc:
        report={
            "status":"original_source_integrity_or_access_stop",
            "exception":type(exc).__name__,
            "reason":str(exc)[:400],
            "real_forest_information_recomputed":False,
        }
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if report["status"].startswith("original_sources_verified"):
        print(json.dumps({
            "status":report["status"],
            "froids":report["temperate_swiss"]["ground_canopy_all_published_labels"],
            "froids_without_pipistrellus":report["temperate_swiss"]["ground_canopy_excluding_author_noted_dominant"],
            "gomes":report["tropical_french_guiana"]["below_above_original_author_eligible_labels"],
            "not_detector_corrected_or_geographically_held_out":True,
        },indent=2))
    else:
        print(json.dumps(report,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
