#!/usr/bin/env python3
"""Source-confirmed year_id split and sharp conditional animal-overlap bounds.

Reads only the pinned public NestTool *code* ZIP and three GitHub R source
files. No tracking, individual-season CSV, outcome, model, bird ID, or
validation-label data are accessed. All overlap estimates are EXPECTATIONS
over hypothetical random year_id splits, NOT observed cross-split animals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts.bop_red_kite_2024_package_code_only_v1 import (
    _fetch_exact, _digest, extract_R_sources,
)

CONTRACT=ROOT/"research/BOP_NESTTOOL_2024_YEARID_SPLIT_ANIMAL_OVERLAP_V1_CONTRACT.json"
ZIP_RULES=ROOT/"research/BOP_RED_KITE_2024_PACKAGE_CODE_V1_CONTRACT.json"
PREVIOUS=ROOT/"BOP_RED_KITE_2024_PACKAGE_CODE_V1_FIRST_RECEIPT.json"

def load_frozen():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    z=c["archived_package"]
    git=c["historic_git"]
    article=c["article_aggregate"]
    limit=c["safety"]
    terminal=c["terminals"]
    files=git["three_paths"]
    if (
        c["contract_id"]!="bop-nesttool-2024-training-yearid-split-expected-animal-overlap-v1"
        or c["frozen_date"]!="2026-11-18"
        or z["record_id"]!=13736049
        or z["filename"]!="NestTool-1.0.0.zip"
        or z["exact_bytes"]!=6578763
        or z["provider_md5"]!="b172b87191f00f221e9d0151c61d65a6"
        or z["original_code_zip_sha256"]!="ce9737f120aaf039d8252525a9a96d869c3975030f5bf3960c8d86615455bdc9"
        or z["download_url"]!="https://zenodo.org/records/13736049/files/NestTool-1.0.0.zip?download=1"
        or git["commit"]!="8fdf3884b5f6079afdffdc5c563c9050766670a4"
        or [(x["path"],x["sha1"],x["split_input"],x["random_sample_name"]) for x in files]!=[
          ("R/train_home_range_detection.R","47c7b5f6dbcfb53c2df8a014a65fe59cf8a258dd","trackingsummary","milvus_id_train"),
          ("R/train_nest_detection.R","c028e728e0fdf646c3bf6f46e10b3ae6b8f55bcd","trackingsummary","milvus_id_train"),
          ("R/train_nest_success.R","c657973023308201cc11c2fa0c8830fd6655ec5b","nestingsummary","training_ids"),
        ]
        or (article["Swiss_eligible_seasons"],article["Swiss_eligible_bird_count"],
            article["max_seasons_per_bird"],article["training_seasons"],article["validation_seasons"])
            !=(697,258,7,488,209)
        or article["author_default_train_frac"]!=.7
        or article["success_outcome_conditional_subset_not_the_same_697"] is not True
        or c["estimand"]["expected_overlap_bound_not_realized_leakage"] is not True
        or c["estimand"]["no_accuracy_inflation_claim"] is not True
        or terminal["historical_BOP"]!="empirical_state_prediction_mixed"
        or terminal["redkite"]!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or terminal["new_Swiss_validation"]!="NOT_SCORED"
        or not all(limit.get(k) is True for k in (
            "no_Zenodo_GPS_or_indseason_CSV","no_nested_binary_model_or_RDS_RData_extraction",
            "download_only_pinned_code_ZIP_and_three_public_GitHub_R_sources",
            "verify_zip_provider_md5_and_sha256","verify_historical_GitHub_blobs",
            "only_published_code_pattern_labels_line_numbers_and_hashes",
            "no_raw_code_or_animal_keys_in_output","no_BOP_status_change"
        ))
    ):
        raise ValueError("source-only trainer-code and fixed-count mathematical contract drifted")
    previous=json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if (
        previous["original_archived_provider"]["code_ZIP_sha256"]!=z["original_code_zip_sha256"]
        or previous["code_parity"]["exact_byte_equal"] is not True
    ):
        raise ValueError("historical initial ZIP provenance missing")
    return c

def _fetch_dated_r(spec:dict,commit:str)->bytes:
    url=f"https://raw.githubusercontent.com/Vogelwarte/NestTool/{commit}/{spec['path']}"
    req=Request(url,headers={"User-Agent":"ODSP-BOP-year-id-split-code-only-v1","Accept-Encoding":"identity"})
    with urlopen(req,timeout=60) as res:
        parsed=urlparse(res.geturl())
        if (
            int(res.status)!=200
            or parsed.scheme!="https"
            or parsed.hostname!="raw.githubusercontent.com"
            or unquote(parsed.path)!=f"/Vogelwarte/NestTool/{commit}/{spec['path']}"
        ):
            raise ValueError("unexpected dated GitHub source redirect")
        b=res.read(1048577)
    if len(b)>1048576 or _digest(b)["git_blob_sha1"]!=spec["sha1"]:
        raise ValueError("dated GitHub training R code is not exact frozen blob")
    return b

def _line_hits(lines:list[str],expression:str)->list[int]:
    return [i for i,line in enumerate(lines,1) if expression in line]

def inspect_year_id_split(code:bytes,spec:dict)->dict:
    """Static source assertions only, not R execution or a re-trained model."""
    lines=code.decode("utf-8-sig").splitlines()
    src="\n".join(lines)
    input_name=spec["split_input"]
    chosen_name=spec["random_sample_name"]
    function_name=Path(spec["path"]).stem
    patterns={
        "default_train_frac_0_7":rf"{re.escape(function_name)}\s*<-\s*function\([^\n]*train_frac\s*=\s*0\.7",
        "year_id_pseudogroups":rf"milvus_id\s*<-\s*unique\(\s*{input_name}\$year_id\s*\)",
        "random_sample_of_year_id":r"(?:" + re.escape(chosen_name) + r")\s*<-\s*sample\(\s*milvus_id\s*,\s*round\(\s*length\(\s*milvus_id\s*\)\s*\*\s*train_frac\s*\)\s*\)",
        "train_year_filter":rf"filter\(\s*year_id\s*%in%\s*{chosen_name}\s*\)",
        "test_year_exclusion":rf"filter\(\s*!year_id\s*%in%\s*{chosen_name}\s*\)"
    }
    hits={}
    for label,pat in patterns.items():
        h=[i for i,line in enumerate(lines,1) if re.search(pat,line)]
        if len(h)!=1:
            raise ValueError("one dated trainer does not have exactly one frozen year_id train/test operation")
        hits[label]=h[0]
    if re.search(r"sample\(\s*unique\([^)]*bird_id",src):
        raise ValueError("unexpected bird_id random-sample instruction in frozen trainer")
    if not (hits["year_id_pseudogroups"]<hits["random_sample_of_year_id"]<
            hits["train_year_filter"]<hits["test_year_exclusion"]):
        raise ValueError("year_id split operations in unexpected order")
    return {
        "name":spec["path"],
        "split_unit":"year_id",
        "not_grouped_by_bird_id":True,
        "train_fraction_default":.7,
        "source_line_numbers":hits,
        "source_SHA256":hashlib.sha256(code).hexdigest(),
        "source_git_blob_SHA1":_digest(code)["git_blob_sha1"],
    }

def p_mixed(k:int,n:int,train:int)->float:
    if not (n>train>0 and 1<=k<=n):
        raise ValueError("invalid cohort size or number of seasons per bird")
    testing=n-train
    p_all_train=1.
    p_all_test=1.
    for j in range(k):
        p_all_train*=(train-j)/(n-j)
        p_all_test*=(testing-j)/(n-j)
    return max(0.,1.-p_all_train-p_all_test)

def sharp_expected_overlap_bounds(n_seasons:int,n_birds:int,max_seasons:int,
                                   ntrain:int)->dict:
    if (not 0<n_birds<=n_seasons<=n_birds*max_seasons
        or not 1<=ntrain<n_seasons
        or max_seasons<2):
        raise ValueError("unknown cohort constraints not feasible")
    probs=[p_mixed(k,n_seasons,ntrain) for k in range(1,max_seasons+1)]
    increments=[probs[i+1]-probs[i] for i in range(len(probs)-1)]
    # Strict discrete concavity: the *only* requirement for the majorization
    # extreme-concentration and most-balanced optimal histograms.
    if not all(increments[i+1]<increments[i] for i in range(len(increments)-1)):
        raise ValueError("finite hypergeometric mixed-bird probability is not concave")
    extra=n_seasons-n_birds
    filled,remainder=divmod(extra,max_seasons-1)
    hmin={k:0 for k in range(1,max_seasons+1)}
    hmin[max_seasons]=filled
    if remainder:
        hmin[1+remainder]+=1
    hmin[1]+=n_birds-filled-(1 if remainder else 0)
    base,remainder=divmod(n_seasons,n_birds)
    hmax={k:0 for k in range(1,max_seasons+1)}
    hmax[base]+=n_birds-remainder
    if remainder:
        hmax[base+1]+=remainder
    def valid(h):
        return sum(h.values())==n_birds and sum(k*v for k,v in h.items())==n_seasons and all(v>=0 for v in h.values())
    if not valid(hmin) or not valid(hmax):
        raise ValueError("purported sharp extremal histograms violate aggregate bird-season constraints")
    minimum=sum(hmin[k]*probs[k-1] for k in hmin)
    maximum=sum(hmax[k]*probs[k-1] for k in hmax)
    if minimum>maximum:
        raise ValueError("mathematical expected-overlap extrema reversed")
    return {
        "split_unit":"year_id_not_bird_id",
        "population_seasons":n_seasons,
        "population_birds_as_published":n_birds,
        "max_seasons_per_bird_as_published":max_seasons,
        "training_seasons":ntrain,
        "validation_seasons":n_seasons-ntrain,
        "prob_bird_both_given_k_seasons":{str(k):round(probs[k-1],9) for k in range(1,max_seasons+1)},
        "minimum_expected_birds_shared_between_train_and_test":round(minimum,6),
        "maximum_expected_birds_shared_between_train_and_test":round(maximum,6),
        "minimum_extremal_histogram":{str(k):v for k,v in hmin.items() if v},
        "maximum_extremal_histogram":{str(k):v for k,v in hmax.items() if v},
        "extrema_proven_by_strict_discrete_concavity":True,
        "expected_bird_overlap_NOT_realized_actual_split":True,
        "no_performance_inflation_estimated":True,
    }

def verify_trainer_sources(contract:dict,archive:bytes,references:dict[str,bytes])->dict:
    z=contract["archived_package"]
    if (
        len(archive)!=z["exact_bytes"]
        or hashlib.md5(archive).hexdigest()!=z["provider_md5"]
        or hashlib.sha256(archive).hexdigest()!=z["original_code_zip_sha256"]
    ):
        raise ValueError("original NestTool code ZIP bytes differ from frozen provider source")
    zip_rules=json.loads(ZIP_RULES.read_text(encoding="utf-8"))["strict_access"]
    sources=extract_R_sources(archive,zip_rules)
    all_results=[]
    for spec in contract["historic_git"]["three_paths"]:
        expected_member="NestTool-1.0.0/"+spec["path"]
        raw=sources.get(expected_member)
        ref=references.get(spec["path"])
        if raw is None or ref is None or len(raw)>contract["safety"]["source_member_max_uncompressed_bytes"]:
            raise ValueError("source code ZIP missing fixed trainer R source path")
        if _digest(ref)["git_blob_sha1"]!=spec["sha1"]:
            raise ValueError("dated GitHub trainer source content has changed")
        dated=inspect_year_id_split(ref,spec)
        source_match=(raw==ref)
        archived=inspect_year_id_split(raw,spec)
        all_results.append({
            "trainer":spec["path"],
            "historical_dated_git_blob_SHA1":dated["source_git_blob_SHA1"],
            "archived_zip_member_git_blob_SHA1":archived["source_git_blob_SHA1"],
            "exact_archived_git_bytes_equal":source_match,
            "frozen_year_id_split_dated_code":dated["source_line_numbers"],
            "frozen_year_id_split_archive":archived["source_line_numbers"],
            "observed_rand_split_unit_in_archive":"year_id",
            "bird_id_as_train_test_group_in_archive":False,
        })
    return {
        "source_archived_ZIP_SHA256":hashlib.sha256(archive).hexdigest(),
        "source_archived_ZIP_provider_MD5_verified":True,
        "three_trainers":all_results,
        "all_three_trainers_exact_prepublication_Git_match":all(x["exact_archived_git_bytes_equal"] for x in all_results)
    }

def run():
    c=load_frozen()
    z=c["archived_package"]
    source_zip=_fetch_exact(z["download_url"],z["exact_bytes"],z["provider_md5"],is_archive=True)
    references={spec["path"]:_fetch_dated_r(spec,c["historic_git"]["commit"])
                for spec in c["historic_git"]["three_paths"]}
    archive=verify_trainer_sources(c,source_zip,references)
    expected=sharp_expected_overlap_bounds(697,258,7,488)
    return {
        "schema_version":1,
        "status":c["terminals"]["code_exact"] if archive["all_three_trainers_exact_prepublication_Git_match"]
                          else c["terminals"]["code_mismatch"],
        "source_role":"2024_PUBLIC_SOURCE_CODE_ONLY_NO_MODEL_OR_BIOLOGICAL_DATA",
        "contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "archive_source_provenance":archive,
        "conditional_expected_bird_group_overlap":expected,
        "paper_488_209_split_actual_bird_memberships_accessed":False,
        "paper_internal_test_accuracy_reestimated":False,
        "causal_or_predictive_accuracy_inflation_demonstrated":False,
        "new_Swiss_animal_holdout_performance_measured":False,
        "mathematical_terminal":c["terminals"]["math"],
        "BOP_original_terminal":c["terminals"]["historical_BOP"],
        "redkite_biological_terminal":c["terminals"]["redkite"],
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.resolve() in (CONTRACT.resolve(),PREVIOUS.resolve(),ZIP_RULES.resolve()):
        raise ValueError("never overwrite preaccess code source contract/receipts")
    try:
        result=run()
    except (OSError,ValueError,UnicodeError,RuntimeError) as exc:
        result={
            "schema_version":1,
            "status":"SOURCE_CODE_PARITY_HOLD",
            "error_type":type(exc).__name__,
            "source_role":"2024_PUBLIC_SOURCE_CODE_ONLY_NO_MODEL_OR_BIOLOGICAL_DATA",
            "mathematical_terminal":"CONDITIONAL_EXPECTED_GROUP_OVERLAP_BOUNDS_NOT_REALIZED_LEAKAGE",
            "no_GPS_labels_models_or_animal_keys_read":True,
            "BOP_original_terminal":"empirical_state_prediction_mixed",
            "redkite_biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        }
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    if result["status"]=="SOURCE_CODE_PARITY_HOLD":
        raise SystemExit("HOLD_ARCHIVED_2024_TRAINER_CODE_PARITY: no individual-level validation inference")

if __name__=="__main__":
    main()
