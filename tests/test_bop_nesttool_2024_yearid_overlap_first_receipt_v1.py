"""Immutable code-only 2024 NestTool trainer split and expected overlap receipt."""
from __future__ import annotations

from copy import deepcopy
import json
import pytest

from scripts.verify_bop_nesttool_2024_yearid_overlap_first_v1 import (
    CONTRACT, RECEIPT, verify_first,
)

def objects():
    return (
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        json.loads(CONTRACT.read_text(encoding="utf-8")),
    )

def test_first_2024_code_source_three_trainers_and_sharp_math_agree():
    r,c=objects()
    output=verify_first(r,c)
    assert output["status"]=="FIRST_SOURCE_CODE_AND_EXPECTATION_BOUNDS_VERIFIED"
    assert output["first_run_id"]==44307730106
    assert output["first_artifact_id"]==14429691808
    assert output["three_Zenodo_trainers_byte_identical_to_2024_GitHub"] is True
    assert output["all_three_split_on_year_id_not_bird_id"] is True
    assert output["minimum_expected_duplicated_birds"]==pytest.approx(67.462949,abs=1e-6)
    assert output["maximum_expected_duplicated_birds"]==pytest.approx(146.540230,abs=1e-6)
    assert output["model_accuracy_inflation_measured"] is False
    assert output["original_realized_train_test_overlap_verified"] is False
    assert output["redkite_new_bird_validation"]=="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"

@pytest.mark.parametrize("path,value",[
    (("first_actions","run_id"),100),
    (("first_actions","original_json_sha256"),"0"*64),
    (("first_actions","original_artifact_zip_sha256"),"0"*64),
    (("first_actions","contract_sha256"),"0"*64),
    (("original_zip","exact_three_r_source_byte_match"),False),
    (("original_zip","trainer_split_source",1,"train_filter_line"),72),
    (("original_zip","trainer_split_source",2,"git_blob_sha1"),"0"*40),
    (("math","conditional_minimum_expected_birds_in_both_roles"),0),
    (("math","conditional_maximum_expected_birds_in_both_roles"),258),
    (("math","maximizer_histogram","3"),182),
    (("math","bounds_are_expectations_only"),False),
    (("math","unknown_original_realized_train_test_overlap"),False),
    (("claim_limits","reproductive_outcome_values_opened"),True),
    (("claim_limits","model_probabilities_calculated"),True),
    (("claim_limits","Swiss_to_Germany_external_validation_not_reassessed"),False),
    (("claim_limits","redkite_real_gain_terminal"),"GENERALIZING"),
])
def test_first_source_artifact_or_unwarranted_claim_mutation_fails(path,value):
    r,c=objects()
    changed=deepcopy(r)
    node=changed
    for k in path[:-1]:
        node=node[k]
    node[path[-1]]=value
    with pytest.raises(ValueError):
        verify_first(changed,c)

def test_math_non_deployable_mean_and_immutable_success_subset_scope():
    r,c=objects()
    assert r["math"]["original_random_split_grouping"]=="year_id"
    assert r["math"]["biological_grouping_required_for_new_birds"]=="bird_id"
    assert r["math"]["unknown_original_realized_train_test_overlap"] is True
    assert r["claim_limits"]["nest_success_smaller_conditioned_training_sample_not_scored"] is True
    assert c["article_aggregate"]["success_outcome_conditional_subset_not_the_same_697"] is True
    assert c["estimand"]["no_accuracy_inflation_claim"] is True
    assert len(r["original_zip"]["trainer_split_source"])==3
