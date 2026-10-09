"""Proper IID reference camera calibration still may NOT transport to wildlife.

A focal camera detects NEAR true independent reference passages with .9
and FAR with .3. When a reference passage DISTANCE is IID near/far
Bernoulli(.5), its focal detection outcome is IID Bernoulli(.6);
thus four separate Binomial(2n,.6) Clopper-Pearson q intervals are
legitimate for THAT reference population. In the target wild
population seasonal approach-distance mixing differs, so even
infinitely precise reference q=.6 need not describe q_target.

Re-use the exact original PR251 fixed-margin animal event data and
properly target-standardized distance-conditioned sensor calibration.
Parent first results are replay-locked. Simulate a separate INDEPENDENT
IID source reference stream with a new offset SeedSequence, avoiding
the parent invalid pooled heterogeneous-binomial assumption.

NO actual EcoBank animal, source operation or q reference records.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
import numpy as np

from .uljin_q_transport_distance_mix_v0 import (
    WORLDS,NS,REPS,SEED,NEAR,FAR,WREF,
    q_effective,detector_crossproduct,cp_band,
    detector_gamma_upper,trial
)
from .uljin_independent_q_split_alpha_v0 import _tail_from_margins

METHOD="uljin_iid_reference_camera_q_transport_v1"
OFFSET=734
ALPHA_CAL=.025
ALPHA_ANIMAL=.025


def frozen_guard(plan:Mapping[str,object],parent:Mapping[str,object])->None:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
            "FROZEN_POST_HETEROGENEOUS_POOL_FIRST_RESULTS_BEFORE_VALID_REFERENCE_OUTCOME"
        or plan.get("parent_pr")!=251
        or plan.get("parent_frozen_contract_sha")!=
            "eb10c25bb1211fbf046b71ecd68e14f44cfce331"
        or plan.get("comparator_reference",{}).get(
            "random_seed_extra_reference")!=
            "SeedSequence([2026100916,world_index,n_index,replicate_index,734]) independent from prior complete old reference/wildlife draws"
        or plan.get("replications")!={
            "original_seed":SEED,"worlds":4,
            "calibration_n_per_q_distance_cell":list(NS),
            "world_replicates":REPS,"total":2400
        }
        or parent.get("record_type")!=
            "FIRST_PRE_FROZEN_ULJIN_DISTANCE_MIX_Q_TRANSPORT_V0_TERMINAL_SOURCE_FREE"
        or parent.get("first_scored_ci_run")!=37896564231
        or len(parent.get("source_free_cases",[]))!=4
    ):
        raise ValueError("frozen valid-IID-reference q-transport contract/provenance changed")


def iid_reference_trial(wi:int,ni:int,rep:int)->dict[str,object]:
    if not(0<=wi<len(WORLDS) and 0<=ni<len(NS) and 0<=rep<REPS):
        raise ValueError("reference simulation outside precommitted source frame")
    name,latent,mix,source=WORLDS[wi]
    parent=trial(wi,ni,rep)
    n=NS[ni]
    rng=np.random.default_rng(
        np.random.SeedSequence([SEED,wi,ni,rep,OFFSET]))
    # Proof: independently choose near~Bernoulli(.5) for every
    # reference passage; then detector Bernoulli(q_near or q_far).
    # Each focal outcome is IID Bernoulli(.5*.9+.5*.3)=Bernoulli(.6).
    # Generating its sufficient statistic directly as Binomial(2n,.6)
    # is EXACTLY the IID source mixture law, not an approximation.
    q_reference=float(q_effective(NEAR,FAR,WREF)[0])
    assert abs(q_reference-.6)<1e-12
    wins=tuple(int(v) for v in rng.binomial(2*n,q_reference,size=4))
    lo,hi=cp_band(wins,2*n,ALPHA_CAL)
    B=detector_gamma_upper(lo,hi)
    p=(_tail_from_margins(source,parent["detected_event_counts"][2],B)
       if math.isfinite(B) else 1.)
    return {
        "truth":name,
        "same_parent_animal_count_table":parent["detected_event_counts"],
        "proper_iid_reference_50p50_mix_four_cell_q_covered":
            bool(np.all(lo<=q_reference) and np.all(q_reference<=hi)),
        "proper_iid_reference_q_gamma_upper":B,
        "proper_iid_reference_HOLD":not math.isfinite(B),
        "proper_iid_reference_falsely_or_truly_certifies":(
            math.isfinite(B) and p<ALPHA_ANIMAL),
        "parent_target_standardized_certifies":
            parent["transported_CP_certifies"],
        "parent_target_q_mix_joint_coverage":
            parent["transport_all_12_joint_coverage"],
        "parent_heterogeneous_pooled_reference_certifies":
            parent["reference_naive_CP_certifies"],
        "true_target_detector_gamma":
            parent["true_target_detector_gamma"],
    }


def iid_reference_transport_full_panel(
    plan:Mapping[str,object],parent:Mapping[str,object],
    *,_test_replicates:int|None=None
)->dict[str,object]:
    frozen_guard(plan,parent)
    reps=REPS if _test_replicates is None else _test_replicates
    if type(reps) is not int or not 1<=reps<=REPS:
        raise ValueError("preflight world count outside frozen original bound")
    old={z["world"]:z for z in parent["source_free_cases"]}
    records=[]
    for wi,(name,latent,mix,source) in enumerate(WORLDS):
        for ni,n in enumerate(NS):
            rows=[iid_reference_trial(wi,ni,r) for r in range(reps)]
            def fraction(field):
                return sum(bool(x[field]) for x in rows)/reps
            valid_cert=fraction("proper_iid_reference_falsely_or_truly_certifies")
            corrected=fraction("parent_target_standardized_certifies")
            old_invalid=fraction("parent_heterogeneous_pooled_reference_certifies")
            coverage=fraction("proper_iid_reference_50p50_mix_four_cell_q_covered")
            paired=np.asarray([
                int(z["proper_iid_reference_falsely_or_truly_certifies"])-
                int(z["parent_target_standardized_certifies"])
                for z in rows],dtype=float)
            if reps==REPS:
                if (abs(corrected-old[name]["target_standardized"][ni])>1e-12
                    or abs(old_invalid-old[name]["naive"][ni])>1e-12
                    or abs(fraction("parent_target_q_mix_joint_coverage")-
                           old[name]["joint_12_coverage"][ni])>1e-12):
                    raise ValueError("v0 original first source-free result replay failed")
            finite=[z["proper_iid_reference_q_gamma_upper"] for z in rows
                    if math.isfinite(z["proper_iid_reference_q_gamma_upper"])]
            records.append({
                "world":name,
                "true_latent_encounter_OR":latent,
                "n_reference_per_distance_q_cell_from_parent":n,
                "n_iid_reference_mixture_opportunities_PER_4_CLOCK_CELLS":2*n,
                "first_source_free_original_animal_counts_reused":True,
                "replicates":reps,
                "truth_detector_crossproduct":rows[0]["true_target_detector_gamma"],
                "correct_source_q_crossproduct":1.,
                "iid_source_reference_four_q_simultaneous_coverage":coverage,
                "proper_iid_source_reference_certification_fraction":valid_cert,
                "target_distance_standardized_certification_fraction":corrected,
                "original_invalid_heterogeneous_pooled_certification_fraction":old_invalid,
                "paired_iid_reference_minus_target_standardized_fraction":
                    float(paired.mean()),
                "paired_mc_se":(float(paired.std(ddof=1)/math.sqrt(reps))
                               if reps>1 else None),
                "iid_reference_q_lower_zero_HOLD_fraction":
                    fraction("proper_iid_reference_HOLD"),
                "median_finite_iid_source_reference_B":
                    (float(np.median(finite)) if finite else None),
            })
    if len(records)!=12:
        raise ValueError("lost frozen transport-source experiment")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":("SOURCE_FREE_VALID_IID_Q_REFERENCE_TRANSPORT_PANEL"
                  if reps==REPS else "SOURCE_FREE_VALID_IID_Q_PREFLIGHT"),
        "total_worlds":12*reps,
        "parent_all_first_frozen_source_free_outcomes_replayed":reps==REPS,
        "fully_correct_iid_source_reference_q_binomial_model":True,
        "source_reference_q_CP_simultaneous_coverage_guaranteed":.975,
        "reference_q_is_NOT_target_animal_opportunity_q_if_distance_mix_differs":True,
        "original_camera_target_distances_independently_observed":False,
        "case_results":records,
        "no_real_Uljin_animal_or_operator_data_read":True,
        "previous_qualified_ODSP_routes_unmodified":True
    }
