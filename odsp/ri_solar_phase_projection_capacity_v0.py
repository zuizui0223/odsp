"""Structural representational limit of binned solar-phase predictions.

The original RI model fits six solar-phase histogram probabilities p and
uses a date/site-specific six-by-six row-stochastic projection M to
predict the SAME six civil-clock bins: q_j = sum_k p_k M[k,j].

Although a civil-clock histogram and solar-phase histogram have the
same NOMINAL number of learned bins, a solar-projected q must lie in the
convex hull of rows of M. In particular q_j <= max_k M[k,j].
When max_k M[k,j] < 1, no solar-phase distribution can concentrate
all probability in clock bin j, while a direct clock histogram can.

This is a deterministic model-class limitation, not an empirical
animal response, not a test of sunlight causality or statistical novelty.
"""
from __future__ import annotations

from datetime import date
import math
from typing import Any

import numpy as np

from .ri_solar_clock_transfer_v0 import (
    solar_phase_to_civil_bin_matrix,
    sunrise_sunset_local,
)

METHOD="ri_solar_phase_to_clock_projection_capacity_v0"


def capacity_bounds_for_day(
    day:date,
    latitude:float,
    longitude:float,
)->dict[str,Any]:
    """Geometric upper cap on each civil-clock bin, without outcomes."""
    if not isinstance(day,date):
        raise ValueError("day must be a date")
    sr,ss=sunrise_sunset_local(day,latitude,longitude)
    M=solar_phase_to_civil_bin_matrix(sr,ss)
    if M.shape!=(6,6) or not np.allclose(M.sum(axis=1),1,atol=1e-12):
        raise ValueError("original solar phase projection not row stochastic")
    caps=np.max(M,axis=0)
    if not np.all(np.isfinite(caps)) or np.any(caps<0) or np.any(caps>1+1e-12):
        raise ValueError("invalid projection capacity bounds")
    return {
        "schema_version":1,
        "method_version":METHOD,
        "date":day.isoformat(),
        "latitude_used_in_illustration":float(latitude),
        "longitude_used_in_illustration":float(longitude),
        "astronomical_sunrise_local_hour":sr,
        "astronomical_sunset_local_hour":ss,
        "clock_bin_labels":["00-04","04-08","08-12","12-16","16-20","20-24"],
        "maximum_possible_solar_model_probability_per_clock_bin":caps.tolist(),
        "minimum_clock_bin_cap":float(caps.min()),
        "number_of_clock_bins_with_unreachable_probability_one":int(
            np.count_nonzero(caps<1-1e-10)
        ),
        "same_parameter_count_proves_same_clock_space_expressivity":False,
        "direct_clock_histogram_projection_restriction_present":False,
        "solar_coordinate_histogram_projection_restriction_present":True,
        "empirical_animal_activity_inferred":False,
        "photoperiod_mechanism_falsified":False,
        "original_ecological_v2_results_reclassified":False,
    }
