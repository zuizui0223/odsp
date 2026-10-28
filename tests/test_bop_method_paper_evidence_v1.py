"""Manuscript evidence audit, not a new inferential or empirical endpoint.

All quantitative BOP manuscript statements in the locked matrix are read
from immutable scientific receipts. The paper cannot upgrade old crossfit
scores to a single-future-model guarantee, move a synthetic method study
to an empirical source, or reinterpret the original pooled comparator as
within-species context information.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from odsp.new_group_gain_envelope import fit_new_group_gain_lower_envelope

ROOT=Path(__file__).resolve().parents[1]
MATRIX=ROOT/"research/BOP_METHOD_PAPER_EVIDENCE_MATRIX_V1.json"
PAPER=ROOT/"manuscript/BOP_INDEPENDENT_ANIMAL_GAIN_METHODS_DRAFT_v1.md"
PROOF=ROOT/"docs/bop_individual_gain_inference_theory_v1.md"


def _blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()


def _evidence():
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def test_frozen_source_receipts_are_unchanged_on_current_branch():
    m=_evidence()
    assert m["schema_version"]==1
    assert m["role"]=="POST_RESULT_MANUSCRIPT_EVIDENCE_CROSSWALK_NO_NEW_EMPIRICAL_OR_CONFIRMATORY_ANALYSIS"
    assert len(m["source_receipts"])==7
    for k,source in m["source_receipts"].items():
        contents=(ROOT/source["path"]).read_bytes()
        assert _blob(contents)==source["git_blob_sha1"], "old source changed: "+k


def test_every_bop_paper_claim_replays_to_frozen_original_sources():
    m=_evidence()
    s={k:json.loads((ROOT/v["path"]).read_text(encoding="utf-8"))
       for k,v in m["source_receipts"].items()}
    b=s["bop"];f=s["rank"];t=s["managed"];v=s["v2026"];d=s["dryad"];c=s["common"];w=s["trace"]
    old=m["frozen_biological_endpoint"]
    assert old["source_doi"]==b["source"]["archive_doi"]
    assert old["eligible_groups"]==b["primary_random_forest"]["eligible_individual_count"]==30
    assert old["eligible_events"]==b["data_flow"]["eligible_event_count"]==154655
    assert old["positive_group_gains"]==b["primary_random_forest"]["positive_individual_count"]==27
    assert old["nonpositive_group_gains"]==b["primary_random_forest"]["nonpositive_individual_count"]==3
    assert old["positive_multiclass_brier_groups"]==b["primary_random_forest"]["positive_brier_improvement_count"]==30
    assert old["mean_group_gain_nats_event"]==b["primary_random_forest"]["mean_gain_descriptive"]
    assert old["terminal"]==b["primary_random_forest"]["terminal_category"]=="empirical_state_prediction_mixed"
    assert old["comparator"]=="fold_training_pooled_altitude_state_marginal"
    assert old["rank_for_real_future_bird"]=="UNAVAILABLE_FROM_HISTORICAL_CROSSFITS"

    fixed=m["synthetic_fixed_model"]
    assert fixed["worlds"]==f["generator"]["replicates"]==128
    assert fixed["validation_groups_each_condition"]==f["generator"]["validation_groups_per_scenario"]==40960
    assert fixed["target_coverage"]==f["first_result"]["same_process_group_coverage"]
    assert fixed["shifted_coverage"]==f["first_result"]["shifted_validation_labels_plus_two_mod_four_group_coverage"]
    assert fixed["trained_and_scored_real_birds"]==0

    managed=m["synthetic_managed_predictor"]
    assert managed["worlds"]==t["fixed_design"]["world_count"]==64
    assert managed["validation_groups_each_condition"]==t["fixed_design"]["validation_group_count_per_scenario"]==10240
    assert managed["target_coverage"]==t["observed_first_result"]["same_process_coverage"]
    assert managed["shifted_coverage"]==t["observed_first_result"]["shifted_validation_coverage"]
    assert managed["model_family"]=="deterministic_stratum_by_binary_context_categorical_not_historical_RF"

    source=m["same_study_source_gate"]
    first=v["first_terminal"]
    assert source["novel_ID_candidates"]==first["novel_id_candidate_count"]==10
    assert source["maximum_within_one_species"]==first["maximum_single_species_new_ids"]==6
    assert source["required_per_stratum_calibration_plus_untouched"]==first["necessary_new_ids_for_90pct_stratified_rank_calibration_plus_one_untouched_validation"]==10
    assert source["terminal"]==first["category"]=="NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT"
    assert source["gps_outcomes_read"] is False

    dryad=m["independent_dryad_source_gate"]
    assert dryad["candidate"]==d["terminal"]["candidate"]=="NOT_ADMITTED"
    assert dryad["original_RF_compatibility"]==d["original_model_compatibility"]["direct_external_predictor_reuse"]
    assert dryad["missing_original_RF_predictor"]==["external-temperature"]
    assert dryad["matched_independent_animal_roster"] is False
    assert dryad["gps_outcomes_read"] is False

    common=m["synthetic_common_input_transport"]
    assert common["worlds"]==c["design"]["worlds"]==len(w["worlds"])==24
    assert common["validation_individuals_per_scenario"]==2880
    assert common["same_target_covered_individuals"]==c["first_result"]["covered_target_individuals"]==sum(x["same"] for x in w["worlds"])==2599
    assert common["shifted_validation_covered_individuals"]==c["first_result"]["covered_validation_shift_individuals"]==sum(x["shift"] for x in w["worlds"])==757
    assert common["same_target_coverage"]==2599/2880
    assert common["shifted_coverage"]==757/2880
    assert common["post_result_precision_is_not_new_confirmatory_test"] is True
    assert common["sources_proven_biologically_independent"] is False


@pytest.mark.parametrize("n,rank,coverage",[
    (8,0,1.0),
    (9,1,0.9),
    (19,2,0.9),
    (30,3,28/31),
    (39,4,0.9),
])
def test_theorem_rank_and_discreteness_match_executable_bop_api(n,rank,coverage):
    envelope=fit_new_group_gain_lower_envelope(
        group_gains=[float(i) for i in range(n)],
        group_ids=[f"test_animal_{i}" for i in range(n)],
        source_design="fixed_predictor_groups",miscoverage=0.1,
    )
    assert envelope.finite_sample_rank==rank
    assert envelope.conservative_coverage_if_exchangeable==pytest.approx(coverage)
    assert envelope.bound_is_vacuous is (rank==0)
    assert envelope.inference_status=="conditional_rank_guarantee_only_if_group_scores_exchangeable"
    assert envelope.as_dict()["exchangeability_verified_by_software"] is False
    assert envelope.as_dict()["not_a_mean_gain_confidence_interval"] is True


def test_manuscript_does_not_claim_external_validation_or_novel_rank_theorem():
    body=PAPER.read_text(encoding="utf-8")
    note=PROOF.read_text(encoding="utf-8")
    matrix=_evidence()
    for phrase in (
        "WORKING_DRAFT__NOT_FOR_SUBMISSION",
        "empirical_state_prediction_mixed",
        "NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT",
        "NOT_ADMITTED",
        "27/30",
        "30/30",
        "2,599",
        "757",
        "0.902431",
        "0.262847",
        "not a new conformal result",
        "not the original BOP",
        "pooled training-fold marginal",
        "training-only species marginal",
    ):
        assert phrase.lower() in body.lower(),phrase
    assert "one-sided rank lemma" in note.lower()
    assert "can only make the bound more conservative" in note
    assert "does **not**" in note
    assert "standard_order_statistic_rank_coverage_is_not_new_theorem" in matrix["novelty_and_claim_guardrails"]
    assert matrix["software_integration"]["synthetic_only"] is True
    assert "10.1214/23-AOS2276" in body
    assert "10.1561/2200000101" in body
    assert "10.1198/016214506000001437" in body
    assert "10.1111/ecog.02881" in body


def test_paper_file_cannot_be_considered_an_admitted_new_external_source():
    m=_evidence()
    assert m["independent_dryad_source_gate"]["candidate"]=="NOT_ADMITTED"
    assert m["same_study_source_gate"]["gps_outcomes_read"] is False
    assert "historical_crossfitted_bop_gains_cannot_be_reused_as_frozen_deployment_calibration" in m["novelty_and_claim_guardrails"]
    assert "no_publication_claim_of_real_Dryad_external_validation" in m["novelty_and_claim_guardrails"]
    assert "manuscript_not_submission_ready_without_substantive_cross_dataset_empirical_demonstration_or_clear_methodological_distinctiveness" in m["novelty_and_claim_guardrails"]
