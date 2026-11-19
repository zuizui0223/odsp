"""Known-truth and adversarial tests for 2024 NestTool season/bird split gap."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import itertools
import json
import zipfile

import pytest

from scripts.bop_nesttool_2024_yearid_animal_overlap_v1 import (
    CONTRACT, inspect_year_id_split, load_frozen, p_mixed,
    sharp_expected_overlap_bounds, verify_trainer_sources,
)

def _contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))

def _r_code(spec:dict, group_field:str="year_id")->bytes:
    function=spec["path"].split("/")[-1][:-2]
    data=spec["split_input"]
    target=spec["random_sample_name"]
    return (
        f"{function} <- function({data}, train_frac=0.7,plot=TRUE) {{\n"
        + f"milvus_id <- unique({data}$" + f"{group_field})\n"
        + f"{target} <- sample(milvus_id, round(length(milvus_id)*train_frac))\n"
        + f"milvus_train <- {data} %>%\n"
        + f"  dplyr::filter(year_id %in% {target})\n"
        + f"milvus_test <- {data} %>%\n"
        + f"  dplyr::filter(!year_id %in% {target})\n"
        + "}\n"
    ).encode("utf-8")

def _mock_zipped(c:dict,change_archive:bool=False):
    refs={}
    a=io.BytesIO()
    with zipfile.ZipFile(a,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("NestTool-1.0.0/R/data_prep.R",b"data_prep <- function(...) TRUE\n")
        for idx,spec in enumerate(c["historic_git"]["three_paths"]):
            ref=_r_code(spec)
            refs[spec["path"]]=ref
            spec["sha1"]=hashlib.sha1(b"blob "+str(len(ref)).encode()+b"\0"+ref).hexdigest()
            blob=ref if not(change_archive and idx==1) else ref+b"\n# extra documented note\n"
            z.writestr("NestTool-1.0.0/"+spec["path"],blob)
    archive=a.getvalue()
    c["archived_package"]["exact_bytes"]=len(archive)
    c["archived_package"]["provider_md5"]=hashlib.md5(archive).hexdigest()
    c["archived_package"]["original_code_zip_sha256"]=hashlib.sha256(archive).hexdigest()
    return archive,refs,c

def test_frozen_contract_is_only_code_and_paper_aggregate():
    c=load_frozen()
    assert c["frozen_date"]=="2026-11-18"
    assert c["archived_package"]["provider_md5"]=="b172b87191f00f221e9d0151c61d65a6"
    assert c["article_aggregate"]["Swiss_eligible_seasons"]==697
    assert c["article_aggregate"]["Swiss_eligible_bird_count"]==258
    assert c["article_aggregate"]["training_seasons"]==488
    assert c["article_aggregate"]["validation_seasons"]==209
    assert c["article_aggregate"]["success_outcome_conditional_subset_not_the_same_697"] is True
    assert c["safety"]["no_Zenodo_GPS_or_indseason_CSV"] is True
    assert c["safety"]["no_nested_binary_model_or_RDS_RData_extraction"] is True

def test_uniform_train_test_hypergeom_per_bird_probabilities():
    assert p_mixed(1,697,488)==pytest.approx(0,abs=1e-15)
    assert p_mixed(2,697,488)==pytest.approx(0.4204884645195336,abs=1e-12)
    assert p_mixed(7,697,488)==pytest.approx(0.9183898647783769,abs=1e-12)
    with pytest.raises(ValueError):
        p_mixed(0,697,488)

def test_sharp_697_258_swiss_expected_bird_overlap_extrema():
    result=sharp_expected_overlap_bounds(697,258,7,488)
    assert result["minimum_expected_birds_shared_between_train_and_test"]==pytest.approx(67.462949,abs=1e-6)
    assert result["maximum_expected_birds_shared_between_train_and_test"]==pytest.approx(146.540230,abs=1e-6)
    assert result["minimum_extremal_histogram"]=={"1":184,"2":1,"7":73}
    assert result["maximum_extremal_histogram"]=={"2":77,"3":181}
    assert result["extrema_proven_by_strict_discrete_concavity"] is True
    assert result["expected_bird_overlap_NOT_realized_actual_split"] is True
    assert result["no_performance_inflation_estimated"] is True

def test_extrema_are_sharp_on_a_fully_enumerable_small_case():
    n,b,m,t=9,4,3,6
    result=sharp_expected_overlap_bounds(n,b,m,t)
    all_expected=[]
    for hist in itertools.product(range(b+1),repeat=m):
        if sum(hist)!=b or sum((i+1)*hist[i] for i in range(m))!=n:
            continue
        all_expected.append(sum(p_mixed(i+1,n,t)*hist[i] for i in range(m)))
    assert len(all_expected)>1
    assert result["minimum_expected_birds_shared_between_train_and_test"]==pytest.approx(min(all_expected),abs=1e-6)
    assert result["maximum_expected_birds_shared_between_train_and_test"]==pytest.approx(max(all_expected),abs=1e-6)

def test_synthetic_2024_year_id_splitting_is_detected_for_all_three_functions():
    c=_contract()
    for spec in c["historic_git"]["three_paths"]:
        out=inspect_year_id_split(_r_code(spec),spec)
        assert out["split_unit"]=="year_id"
        assert out["not_grouped_by_bird_id"] is True
        assert set(out["source_line_numbers"])=={
            "default_train_frac_0_7","year_id_pseudogroups",
            "random_sample_of_year_id","train_year_filter","test_year_exclusion"
        }
        assert "bird" not in json.dumps(out["source_line_numbers"])

def test_synthetic_bird_id_split_cannot_masquerade_as_year_id():
    c=_contract()
    for spec in c["historic_git"]["three_paths"]:
        with pytest.raises(ValueError,match="year_id"):
            inspect_year_id_split(_r_code(spec,group_field="bird_id"),spec)

def test_synthetic_zip_three_r_trainers_byte_identical_to_reference():
    c=_contract()
    archive,refs,c=_mock_zipped(c)
    r=verify_trainer_sources(c,archive,refs)
    assert r["all_three_trainers_exact_prepublication_Git_match"] is True
    assert len(r["three_trainers"])==3
    assert all(x["observed_rand_split_unit_in_archive"]=="year_id" for x in r["three_trainers"])
    assert all(x["bird_id_as_train_test_group_in_archive"] is False for x in r["three_trainers"])

def test_zip_training_code_drift_is_reported_without_claim_of_identity():
    c=_contract()
    archive,refs,c=_mock_zipped(c,change_archive=True)
    r=verify_trainer_sources(c,archive,refs)
    assert r["all_three_trainers_exact_prepublication_Git_match"] is False
    assert sum(x["exact_archived_git_bytes_equal"] is False for x in r["three_trainers"])==1

def test_package_corruption_and_wrong_historical_git_hash_stop():
    c=_contract()
    archive,refs,c=_mock_zipped(c)
    with pytest.raises(ValueError,match="original NestTool"):
        verify_trainer_sources(c,archive+b"\x00",refs)
    refs2=deepcopy(refs)
    refs2["R/train_nest_detection.R"]=b"unrelated code"
    with pytest.raises(ValueError,match="dated GitHub"):
        verify_trainer_sources(c,archive,refs2)
