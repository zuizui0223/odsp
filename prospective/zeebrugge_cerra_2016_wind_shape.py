#!/usr/bin/env python3
"""CERRA site-wind conditional daily-centered flight-height shape estimator.

Pure numerical kernel and pre-declared month-block wind randomization.
Never claim that colony wind is the wind encountered at GPS flight position.
"""
from __future__ import annotations

from collections import defaultdict
import math
import numpy as np
from numba import njit

EDGES = np.array([-np.inf, -200., -100., -50., -25., 0., 25., 50.,
                  100., 200., np.inf])
STATE = {"low": 0, "high": 1, "middle": -1}


def center_into_hist(heights):
    h = np.asarray(list(heights), dtype=float)
    if h.ndim != 1 or len(h) == 0 or not np.all(np.isfinite(h)):
        raise ValueError("Expected nonempty finite height vector")
    labels = np.searchsorted(EDGES, h - np.median(h), side="right") - 1
    if np.any((labels < 0) | (labels >= 10)):
        raise AssertionError("Invalid frozen altitude bins")
    return np.bincount(labels, minlength=10)


def permute_wind_labels(regimes, weather, rng):
    """Preserve each grid-month state counts; share shuffle at shared CERRA cell."""
    shared = defaultdict(list)
    for site, info in weather.items():
        grid = (round(info["response_grid_latitude"], 6),
                round(info["response_grid_longitude"], 6))
        shared[grid].append(site)
    result = {site: dict(states) for site, states in regimes.items()}
    for grid, sites in sorted(shared.items()):
        monthly = defaultdict(set)
        for site in sites:
            for day in regimes[site]:
                monthly[day[:7]].add(day)
        for month, date_set in sorted(monthly.items()):
            days = sorted(date_set)
            shuffled_idx = rng.permutation(len(days))
            for site in sites:
                if not all(d in regimes[site] for d in days):
                    raise ValueError("Site CERRA coverage differs within one grid")
                original = [regimes[site][day] for day in days]
                for j, day in enumerate(days):
                    result[site][day] = original[int(shuffled_idx[j])]
    return result


def pack(sessions, sites_by_bird, regimes):
    bird_ids = sorted({s["bird"] for s in sessions})
    days = sorted({s["day"] for s in sessions})
    sites = sorted({sites_by_bird[b] for b in bird_ids})
    if not bird_ids or not days or not sites:
        raise ValueError("No qualifying bird-day sessions")
    if any(b not in sites_by_bird for b in bird_ids):
        raise ValueError("Bird lacks a source-confirmed site")
    pair_set = {(s["bird"], cell) for s in sessions for cell in s["hists"]}
    pairs = sorted(pair_set)
    bid = {b: i for i, b in enumerate(bird_ids)}
    did = {d: i for i, d in enumerate(days)}
    sid = {s: i for i, s in enumerate(sites)}
    pid = {pair: i for i, pair in enumerate(pairs)}
    indices = []
    hists = []
    unique_sessions = set()
    for s in sessions:
        bird, day = s["bird"], s["day"]
        if (bird, day) in unique_sessions:
            raise ValueError("Duplicate bird-day session")
        unique_sessions.add((bird, day))
        for cell, counts in sorted(s["hists"].items()):
            h = np.asarray(counts, np.int64)
            if h.shape != (10,) or np.any(h < 0):
                raise ValueError("Invalid fixed 10-bin height histogram")
            if h.sum() <= 0:
                continue
            indices.append([pid[bird, cell], bid[bird], did[day],
                            sid[sites_by_bird[bird]]])
            hists.append(h)
    if not indices:
        raise ValueError("No nonzero day-cell profiles")
    out = dict(indices=np.array(indices, dtype=np.int64),
               hist=np.array(hists, dtype=np.int64),
               birds=bird_ids, days=days, sites=sites, npairs=len(pairs))
    out["regimes"] = wind_table(out, regimes)
    return out


def wind_table(packed, regimes):
    mat = np.full((len(packed["sites"]), len(packed["days"])), -1,
                  dtype=np.int64)
    for i, site in enumerate(packed["sites"]):
        for j, day in enumerate(packed["days"]):
            mat[i, j] = STATE.get(regimes.get(site, {}).get(day), -1)
    return mat


@njit(cache=True)
def _kernel(indices, hist, site_wind, n_birds, n_days, n_pairs):
    # In each individual × 5km cell, day-weighted donor profiles.
    pooled_sum = np.zeros((n_pairs, 10), np.float64)
    conditional_sum = np.zeros((n_pairs, 2, 10), np.float64)
    all_profile_n = np.zeros(n_pairs, np.int64)
    state_profile_n = np.zeros((n_pairs, 2), np.int64)
    state_event_n = np.zeros((n_pairs, 2), np.int64)
    for r in range(len(hist)):
        pair, bird, day, site = indices[r]
        state = site_wind[site, day]
        total = 0
        for k in range(10):
            total += hist[r, k]
        all_profile_n[pair] += 1
        denominator = total + 5.0
        for k in range(10):
            pooled_sum[pair, k] += (hist[r, k] + .5) / denominator
        if state >= 0:
            state_profile_n[pair, state] += 1
            state_event_n[pair, state] += total
            for k in range(10):
                conditional_sum[pair, state, k] += (hist[r, k] + .5) / denominator

    scored_count = np.zeros((n_birds, n_days, 2), np.int64)
    gain_sum = np.zeros((n_birds, n_days, 2), np.float64)
    for r in range(len(hist)):
        pair, bird, day, site = indices[r]
        state = site_wind[site, day]
        if state < 0:
            continue
        total = 0
        for k in range(10):
            total += hist[r, k]
        if state_event_n[pair, state] - total < 10:
            continue
        if state_event_n[pair, 1 - state] < 10:
            continue
        if state_profile_n[pair, state] <= 1 or all_profile_n[pair] <= 1:
            continue
        total_gain = 0.0
        valid = True
        for k in range(10):
            if hist[r, k] == 0:
                continue
            own_profile_prob = (hist[r, k] + .5) / (total + 5.0)
            p_pooled = ((pooled_sum[pair, k] - own_profile_prob)
                        / (all_profile_n[pair] - 1))
            p_state = ((conditional_sum[pair, state, k] - own_profile_prob)
                       / (state_profile_n[pair, state] - 1))
            if p_pooled <= 0 or p_state <= 0:
                valid = False
                break
            total_gain += hist[r, k] * (np.log(p_state) - np.log(p_pooled))
        if not valid:
            continue
        scored_count[bird, day, state] += total
        gain_sum[bird, day, state] += total_gain

    per_bird = np.full(n_birds, np.nan)
    days_low = np.zeros(n_birds, np.int64)
    days_high = np.zeros(n_birds, np.int64)
    fixes = np.zeros(n_birds, np.int64)
    for bird in range(n_birds):
        sum_gains = np.zeros(2)
        count_days = np.zeros(2, np.int64)
        count_fixes = np.zeros(2, np.int64)
        for day in range(n_days):
            for state in range(2):
                count = scored_count[bird, day, state]
                if count >= 20:
                    sum_gains[state] += gain_sum[bird, day, state] / count
                    count_days[state] += 1
                    count_fixes[state] += count
        if count_days[0] >= 2 and count_days[1] >= 2:
            per_bird[bird] = .5 * (sum_gains[0] / count_days[0]
                                   + sum_gains[1] / count_days[1])
            days_low[bird] = count_days[0]
            days_high[bird] = count_days[1]
            fixes[bird] = count_fixes[0] + count_fixes[1]

    eligible = 0
    total_gains = 0.0
    total_days = 0
    total_fixes = 0
    for bird in range(n_birds):
        if np.isfinite(per_bird[bird]):
            eligible += 1
            total_gains += per_bird[bird]
            total_days += days_low[bird] + days_high[bird]
            total_fixes += fixes[bird]
    mean_gain = total_gains / eligible if eligible else np.nan
    return mean_gain, eligible, total_days, total_fixes, per_bird, days_low, days_high, fixes


def score_packed(packed, regimes):
    mat = wind_table(packed, regimes)
    a = _kernel(packed["indices"], packed["hist"], mat,
                len(packed["birds"]), len(packed["days"]), packed["npairs"])
    return dict(mean_gain=float(a[0]) if np.isfinite(a[0]) else None,
                eligible_birds=int(a[1]), eligible_bird_days=int(a[2]),
                scored_fixes=int(a[3]),
                per_bird={
                    packed["birds"][i]: dict(gain=float(a[4][i]),
                                             low_days=int(a[5][i]),
                                             high_days=int(a[6][i]),
                                             scored_fixes=int(a[7][i]))
                    for i in range(len(packed["birds"])) if np.isfinite(a[4][i])
                })


def score_context(sessions, sites_by_bird, regimes):
    return score_packed(pack(sessions, sites_by_bird, regimes), regimes)
