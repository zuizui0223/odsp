#!/usr/bin/env python3
"""Basham 62-study V2 pre-frozen, original-source study-heldout proxy prediction.

Different from animal 3D SDM. Reads original author numerical biodiversity
proxy only after the preoutcome scoring contract and known-truth tests.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.request import Request,urlopen

from odsp.vertebrate_vertical_study_transfer_v2 import (
    SourceRow,assemble_profiles,evaluate_transfer
)
from scripts.vertebrate_vertical_study_source_v1 import (
    SOURCE_URL,SOURCE_GIT_BLOB,git_blob_hash,source_structure
)

EXPECTED_SHA256="028f5ad6371151a1cd5d89d2e2711711b4de383e24dd914a55e28b74aaa9cdc1"
EXPECTED_SOURCE_ROWS=1422
EXPECTED_STUDIES=62
EXPECTED_SITES=86
EXPECTED_PROFILE_GROUPS=127
EXPECTED_DUPLICATE_GROUPS=14
EXPECTED_EXTRA_HEIGHT_ROWS=49
TARGET_FIELD="corrected_biodiversity_metric_value"

def read_original_outcome(raw:bytes):
    if git_blob_hash(raw)!=SOURCE_GIT_BLOB or hashlib.sha256(raw).hexdigest()!=EXPECTED_SHA256:
        raise ValueError("original corrigendum-version source bytes mismatch")
    structure=source_structure(raw)
    if structure["status"]!="source_structure_admitted_numerical_biodiversity_sealed":
        raise ValueError("source geometry admission changed")
    if (structure["source_rows"]!=EXPECTED_SOURCE_ROWS or
        structure["source_unique_studies"]!=EXPECTED_STUDIES or
        structure["source_site_identifiers"]!=EXPECTED_SITES or
        structure["source_site_metric_units"]!=EXPECTED_PROFILE_GROUPS or
        structure["site_metric_units_with_repeated_numeric_height"]!=EXPECTED_DUPLICATE_GROUPS or
        structure["redundant_site_metric_height_rows"]!=EXPECTED_EXTRA_HEIGHT_ROWS):
        raise ValueError("source structure no longer reproduces the sealed gate")
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    expected_columns={"link","study_id","taxa","biodiversity_metric",
                      "mean_strata_height_p",TARGET_FIELD}
    if not expected_columns.issubset(reader.fieldnames or []):
        raise ValueError("original source response schema changed")
    rows=[]
    for r in reader:
        try:
            h=float(r["mean_strata_height_p"])
            value=float(r[TARGET_FIELD])
        except (ValueError,TypeError) as exc:
            raise ValueError("SOURCE_RESPONSE_STOP: nonnumeric author-corrected value/height") from exc
        if not math.isfinite(value) or value<0:
            raise ValueError("SOURCE_RESPONSE_STOP: invalid source biodiversity proxy")
        rows.append(SourceRow(
            study=r["study_id"].strip(),site=r["link"].strip(),
            taxon=r["taxa"].strip(),metric=r["biodiversity_metric"].strip(),
            height=h,value=value
        ))
    if len(rows)!=EXPECTED_SOURCE_ROWS:
        raise ValueError("original source rows changed after header audit")
    return rows,structure


def evaluate_source(raw):
    rows,source_structure_receipt=read_original_outcome(raw)
    profiles,admitted=assemble_profiles(rows)
    if len(profiles)!=EXPECTED_PROFILE_GROUPS or (
        admitted["site_metric_units_with_duplicate_heights"]!=EXPECTED_DUPLICATE_GROUPS or
        admitted["extra_height_rows_collapsed_by_arithmetic_mean"]!=EXPECTED_EXTRA_HEIGHT_ROWS
    ):
        raise ValueError("V2 source geometry/repeated-height interpretation conflicts with preopen receipt")
    score=evaluate_transfer(profiles)
    return {
        "source_publication":"Basham et al. (2023), Biological Reviews",
        "source_doi":"10.1111/brv.12896",
        "source_original_corrected_2026_commit":source_structure_receipt["source_commit"],
        "source_sha256":EXPECTED_SHA256,
        "original_response_field":TARGET_FIELD,
        "source_admission":source_structure_receipt,
        "eligible_site_height_profiles":admitted,
        "prospectively_fixed_study_heldout_scores":score,
        "not_independent_original_publication_discovery":True,
        "not_true_latent_species_level_3d_sdm":True,
        "original_response_first_scored_after_protocol":"docs/vertebrate_vertical_study_v2_preoutcome_scoring_freeze.md",
    }


def main():
    receipt={"status":"SOURCE_RESPONSE_STOP",
             "source_git_sha1":SOURCE_GIT_BLOB,
             "original_biodiversity_numbers_tested":False,
             "prospective_protocol":"docs/vertebrate_vertical_study_v2_preoutcome_scoring_freeze.md"}
    try:
        req=Request(SOURCE_URL,headers={"User-Agent":"ODSP-study-v2-prospective-source/1.0"})
        with urlopen(req,timeout=120) as response:
            raw=response.read(2_000_001)
        if len(raw)>2_000_000:
            raise ValueError("original file size over maximum")
        receipt=evaluate_source(raw)
    except Exception as exc:
        receipt.update({
            "status":"SOURCE_ACCESS_OR_RESPONSE_STOP",
            "original_biodiversity_numbers_tested":False,
            "exception":type(exc).__name__,
            "reason":str(exc)[:420],
            "no_scientific_effects_scored_or_reported":True,
        })
    path=Path("results/vertebrate_vertical_study_transfer_v2.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if receipt.get("status")=="SOURCE_ACCESS_OR_RESPONSE_STOP":
        print(json.dumps(receipt,indent=2))
    else:
        # Public original-study IDs stay only in the private in-process folds,
        # not printed. Report all group-level effects including negatives.
        print(json.dumps({
            "status":receipt["prospectively_fixed_study_heldout_scores"]["status"],
            "source_sha256":receipt["source_sha256"],
            "profile_source_audit":receipt["eligible_site_height_profiles"],
            "by_endpoint":receipt["prospectively_fixed_study_heldout_scores"]["scores_by_endpoint"],
            "no_latent_3d_species_sdm_or_detector_correction":True,
        },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
