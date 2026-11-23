#!/usr/bin/env python3
"""Independent numerical replay of Thiel 2024 nine-plant Bat-nectar V2.

Uses a separately vectorized NumPy likelihood/grid optimizer, NOT V2
odsp.nectarivore_bat_resource_transfer_v2 scorer/fit/evaluate.
The original source parser/eligibility adapter is reused: this is a numerical
verification, not a second source/field study or detector calibration.
"""
from __future__ import annotations
from itertools import product
import json
from math import log
from pathlib import Path
import numpy as np

from scripts.nectarivore_bat_plant_resource_transfer_v2 import (
    download_original, get_qualified_original_plant_profiles,
)
from scripts.nectarivore_zenodo_source_v1_1_pairs import read_source_allowed_columns

GRID=np.arange(-2.0,2.0000001,.5,dtype=float)
EXPECTED_TOTAL=5421
EXPECTED_LOO_BASELINE=(
    -0.9203232383339386,
    -0.08126296407876588,
    -1.5742247419332787,
    -1.4411127046109184,
    -0.7833458708392776,
    -0.9008746242083185,
    -0.6767018342978679,
    -0.8791206501223982,
    -1.1659959827799131,
)
EXPECTED_PER_PLANT_VISITS=(693,72,44,949,1812,691,701,316,143)
EXPECTED_MEAN=-0.9358847345782975
TOL=1e-10


def independent_score(profile,alpha_mid,alpha_high,beta):
    layer_effects={"Low":0.0,"Middle":alpha_mid,"High":alpha_high}
    src_layers=profile.layers
    exposures=np.array([np.log(x.exposure) for x in src_layers],dtype=float)
    effects=np.array([layer_effects[x.name] for x in src_layers],dtype=float)
    nectar=np.array([np.log1p(x.resource) for x in src_layers],dtype=float)
    counts=np.array([x.visits for x in src_layers],dtype=float)
    probs=counts/counts.sum()
    logits=exposures+effects+beta*nectar
    largest=float(logits.max())
    normalization=largest+float(np.log(np.exp(logits-largest).sum()))
    return float(np.dot(probs,logits)-normalization)


def independent_fit(training,resource):
    if any(x.identity in [p.identity for p in training[:0]] for x in []):
        raise AssertionError("unreachable")
    best=None
    result=None
    resource_grid=GRID if resource else (0.0,)
    for am,ah,beta in product(GRID,GRID,resource_grid):
        loglik=float(np.mean([independent_score(p,am,ah,beta)
                              for p in training]))
        loglik-=.02*float(beta)*float(beta)
        score=(round(loglik,14),-abs(beta),-(abs(am)+abs(ah)),
               -abs(am),-abs(ah),-beta,-am,-ah)
        if best is None or score>best:
            best=score
            result=(float(am),float(ah),float(beta))
    return result


def original_source_profiles():
    cam_source,cam_sheet=download_original("CameraTraps.xlsx")
    nectar_source,nectar_sheet=download_original("Nectar measurements_Strata.xlsx")
    cam=read_source_allowed_columns(cam_source,cam_sheet,
        ("ML_ID","Taxa","Stratum","Hours","Inflorescences","Abundance"))
    nectar=read_source_allowed_columns(nectar_source,nectar_sheet,
        ("ML_ID","Stratum","Year","Nect_quant_mean"))
    return get_qualified_original_plant_profiles(cam,nectar)


def independently_verify(profiles):
    if len(profiles)!=9 or sum(len(p.layers) for p in profiles)!=25:
        raise RuntimeError("original plant/recording-stratum eligibility changed")
    if sum(z.visits for p in profiles for z in p.layers)!=EXPECTED_TOTAL:
        raise RuntimeError("original source bat-camera count total changed")
    folds=[]
    ordered=sorted(profiles,key=lambda p:p.identity)
    for idx,target in enumerate(ordered):
        training=[p for p in ordered if p.identity!=target.identity]
        if len(training)!=8 or target in training:
            raise RuntimeError("original heldout individual leaked")
        b0params=independent_fit(training,resource=False)
        b1params=independent_fit(training,resource=True)
        b0=independent_score(target,*b0params)
        b1=independent_score(target,*b1params)
        visits=sum(z.visits for z in target.layers)
        delta=b1-b0
        if (visits!=EXPECTED_PER_PLANT_VISITS[idx] or
            abs(b0-EXPECTED_LOO_BASELINE[idx])>TOL or
            abs(b1-b0)>TOL or b1params[2]!=0.0):
            raise RuntimeError(f"independent numerical replay mismatch on original plant fold {idx+1}")
        folds.append({"fold":idx+1,
            "heldout_count":visits,
            "heldout_layer_count":len(target.layers),
            "B0":b0,"B1":b1,"B1_minus_B0":delta,
            "training_resource_beta":b1params[2]})
    m0=float(np.mean([f["B0"] for f in folds]))
    m1=float(np.mean([f["B1"] for f in folds]))
    if abs(m0-EXPECTED_MEAN)>TOL or abs(m1-EXPECTED_MEAN)>TOL:
        raise RuntimeError("independent source gain differs from originally archived V2")
    return {
        "status":"independent_numpy_scoring_replayed_original_no_nectar_gain",
        "prior_first_v2_success_run_id":45096400185,
        "original_full_dataset_individuals":len(ordered),
        "original_source_paired_height_cells":sum(len(p.layers) for p in profiles),
        "original_source_bat_camera_visit_counts":EXPECTED_TOTAL,
        "B0_equal_original_plant_logscore":m0,
        "B1_equal_original_plant_logscore":m1,
        "B1_minus_B0":m1-m0,
        "original_resource_beta_positive_folds":sum(x["training_resource_beta"]!=0 for x in folds),
        "checked_original_plant_folds":len(folds),
        "max_absolute_difference_against_original_v2":max(
            abs(x["B0"]-EXPECTED_LOO_BASELINE[i]) for i,x in enumerate(folds)),
        "heldout_aggregate_checks_without_original_plant_IDs":folds,
        "reused_original_file_parser_and_source_eligibility":True,
        "independent_numpy_probability_score_and_fit":True,
        "no_new_ecological_model_or_detection_calibration":True,
    }


def main():
    report=independently_verify(original_source_profiles())
    path=Path("results/nectarivore_bat_plant_resource_v3_independent.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
