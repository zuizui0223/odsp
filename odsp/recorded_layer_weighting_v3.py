"""Descriptive weighting-dependent information for already recorded two-layer counts.

NOT a true biological x-y-z niche or sensor-q-corrected bat-height model.
"""
from __future__ import annotations
import math
from typing import Mapping, Any


def observed_two_layer_weighting(
    counts: Mapping[str, tuple[int, int]],
    *,
    minimum_active_count_for_guard: int = 20,
) -> dict[str, Any]:
    """Evaluate 2 different *declared reference measures*: observed mass versus
    equal weight for each acoustically active class; no smoothing or p-values.
    """
    if not counts or minimum_active_count_for_guard < 1:
        raise ValueError("invalid count field or count guard")
    for key,values in counts.items():
        if not isinstance(key,str) or not key.strip() or len(values)!=2:
            raise ValueError("class labels and two layer counts required")
        if any(not isinstance(v,int) or v<0 for v in values):
            raise ValueError("counts must be nonnegative integer detected events")
    observed=[(label,a,b) for label,(a,b) in counts.items() if a+b>0]
    if len(observed)<2:
        raise ValueError("at least two classes must have detections in the two layers")

    def entropy(ps):
        return -math.fsum(x*math.log(x) for x in ps if x>0)

    def weighted_mi(active, weights):
        if len(active)<2:
            return None
        norm=sum(weights)
        w=[x/norm for x in weights]
        f=[a/(a+b) for _,a,b in active]
        g=[b/(a+b) for _,a,b in active]
        layer=(math.fsum(x*y for x,y in zip(w,f)),
               math.fsum(x*y for x,y in zip(w,g)))
        h=entropy(layer)
        cond=math.fsum(ws*entropy((fs,gs)) for ws,fs,gs in zip(w,f,g))
        direct=math.fsum(
            ws*prob*math.log(prob/marginal)
            for ws,fs,gs in zip(w,f,g)
            for prob,marginal in zip((fs,gs),layer)
            if prob>0
        )
        # The direct KL and entropy decomposition independently reconcile.
        if abs(direct-(h-cond))>1e-10:
            raise RuntimeError("information identity inconsistent with weights")
        if direct < -1e-12:
            raise RuntimeError("mutual information numerically negative")
        return {
            "information_nats":max(0.0,direct),
            "recorded_layer_entropy_nats":h,
            "fraction_recorded_layer_entropy_explained":max(0.0,direct)/h if h>0 else None,
            "num_active_acoustic_labels":len(active),
            "number_weighted_effective_acoustic_labels":math.exp(entropy(w)),
            "layer_fractions":[float(p) for p in layer],
            "info_identity_abs_error":abs(direct-(h-cond)),
        }

    masses=[a+b for _,a,b in observed]
    all_mass=weighted_mi(observed,masses)
    all_equal=weighted_mi(observed,[1]*len(observed))
    guarded=[row for row in observed if row[1]+row[2]>=minimum_active_count_for_guard]
    guard=weighted_mi(guarded,[1]*len(guarded)) if len(guarded)>=2 else None

    return {
        "num_published_or_source_labels":len(counts),
        "num_active_two_layer_labels":len(observed),
        "num_zero_both_layer_labels":len(counts)-len(observed),
        "total_recorded_events_in_two_layers":sum(masses),
        "two_layer_mass_weighted":all_mass,
        "two_layer_acoustic_label_equal_weighted":all_equal,
        "same_source_label_min_count_guard":minimum_active_count_for_guard,
        "label_equal_at_least_20_recorded_events":guard,
        "conditional_entropy_or_heldout_gain_claimed":False,
        "detection_calibrated_true_vertical_use":False,
        "reference_change_equals_different_population_target":True,
    }
