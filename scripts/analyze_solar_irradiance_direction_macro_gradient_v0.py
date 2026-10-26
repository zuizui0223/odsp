"""Exploratory macroecology of ERA5 shortwave and sun-relative GPS travel.

Uses ONLY the two already-frozen original 24-source sets and their derived
source-gridyear context results. Does not download/reselect animal records.
All tests are descriptive and conditional on the available field-study sample.
The previously registered external nonreplication verdict is immutable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
EARLY = ROOT / "research/SOLAR_AZIMUTH_24_SOURCE_MULTI_POPULATION_ERA5_V0_FIRST_ALL_RESULTS_20261025.json"
LATE = ROOT / "research/SOLAR_RADIATION_EXTERNAL_24_SOURCE_FIRST_ALL_RESULTS_20261025.json"
AUDIT = ROOT / "research/SOLAR_RADIATION_TWO_24_SOURCE_NONREPLICATION_DIAGNOSTIC_FIRST_RESULT_20261025.json"
COVARIATES = {
    "mean_shortwave_Wm2": "shortwave_Wm2",
    "mean_temperature_C": "temperature_2m_C",
    "mean_wind_speed_100m_ms": "wind_speed_100m_ms",
    "mean_wind_sun_cos": "wind_sun_cos",
    "abs_latitude_15degree_band_midpoint": "latitude",
}
BOOT = 5000
SEED = 20261026


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def average(values):
    if not values or any(not finite(v) for v in values):
        raise ValueError("Undefined or non-finite value in observed source mean")
    return mean(values)


def ranks(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    ans = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        midrank = (i + j + 1) / 2.0
        for t in order[i:j]:
            ans[t] = midrank
        i = j
    return ans


def spearman(x, y):
    if len(x) != len(y) or len(x) < 3 or any(not finite(v) for v in x + y):
        return None
    a, b = ranks(x), ranks(y)
    ma, mb = mean(a), mean(b)
    xx = sum((v - ma) ** 2 for v in a)
    yy = sum((v - mb) ** 2 for v in b)
    if xx == 0 or yy == 0:
        return None
    return sum((u - ma) * (v - mb) for u, v in zip(a, b)) / math.sqrt(xx * yy)


def interval(samples):
    if not samples:
        return None
    samples = sorted(samples)
    return [samples[int(0.025 * len(samples))],
            samples[min(len(samples) - 1, int(0.975 * len(samples)) - 1)]]


def bootstrap_rho(rows, cov, seed, draws=BOOT):
    if len(rows) < 5:
        return None
    rng = random.Random(seed)
    values = []
    for _ in range(draws):
        sample = [rows[rng.randrange(len(rows))] for _ in range(len(rows))]
        r = spearman([x["slope"] for x in sample], [x[cov] for x in sample])
        if r is not None:
            values.append(r)
    return {"descriptive_source_resampling_95": interval(values),
            "defined_resamples": len(values), "attempted_resamples": draws}


def source_contexts(original_group):
    contexts = []
    for t in original_group["source_taxa"]:
        for item in t["source_gridyear_weather_contexts"]:
            w = item.get("within_animal_clock_month_weather_associations")
            s = (w or {}).get("shortwave_Wm2")
            slope = (s or {}).get("mean")
            if slope is None:
                continue
            climate = item.get("environmental_group_means")
            lat = item.get("geographic_latitude_band_not_coordinate")
            if not climate or not lat:
                raise ValueError("Defined original shortwave slope lacks climate/latitude")
            b = lat.get("absolute_latitude_band_degrees")
            if not b or len(b) != 2 or b[0] < 0 or b[1] > 90:
                raise ValueError("Invalid source coarse latitude band")
            row = {"taxon": t["taxon"], "slope": slope,
                   "latitude": mean(b),
                   "year": item.get("original_UTC_observation_year")}
            for field in set(COVARIATES.values()) - {"latitude"}:
                value = (climate.get(field) or {}).get("mean")
                if not finite(value):
                    raise ValueError("Missing or non-finite original ERA5 context mean: " + field)
                row[field] = value
            if not finite(slope):
                raise ValueError("Non-finite source original animal shortwave slope")
            contexts.append(row)
    return contexts


def build_rows(earlier, external, audit):
    a, b = earlier["source_groups"], external["all_external_first_source_results"]
    if len(a) != 24 or len(b) != 24:
        raise ValueError("Original fixed source denominator is not 24 + 24")
    by_id = {r["source"]: r for r in audit["all_original_studies_anonymized_source_descriptions"]}
    if len(by_id) != 48 or len({s["source_package_uuid"] for s in a + b}) != 48:
        raise ValueError("Original field study source overlap/denominator changed")
    rows, pair_rows, frame = [], [], []
    for cohort, sources in (("earlier", a), ("external", b)):
        for group in sources:
            sid = group["source_package_uuid"]
            diag = by_id[sid]
            if diag["cohort"] != cohort:
                raise ValueError("Cohort mismatch with immutable original source diagnostic")
            c = source_contexts(group)
            slope = diag["source_mean_rad_slope_per_100W"]
            if (slope is None) != (len(c) == 0):
                raise ValueError("Source shortwave support no longer matches frozen diagnostic")
            if slope is not None and (not finite(slope) or abs(mean(x["slope"] for x in c) - slope) > 1e-10):
                raise ValueError("Original source slope fails exact-ish source context replay")
            masked = hashlib.sha256(sid.encode("utf-8")).hexdigest()[:12]
            frame.append({
                "source_hash": masked,
                "source_cohort": cohort,
                "shortwave_coefficient_status": "DEFINED" if slope is not None else "UNAVAILABLE",
                "num_contexts_with_shortwave_slope": len(c),
                "taxonomic_class": diag["class"] if slope is not None else None,
            })
            if slope is None:
                continue
            study = {"source_hash": masked, "cohort": cohort,
                     "class": diag["class"], "slope": slope,
                     "context_count": len(c)}
            for key, field in COVARIATES.items():
                study[key] = average([x[field] for x in c])
            rows.append(study)
            by_taxon = defaultdict(list)
            for x in c:
                by_taxon[x["taxon"]].append(x)
            for taxon, taxon_ctx in by_taxon.items():
                # The original protocol samples at most two source grid-years per taxon.
                if len(taxon_ctx) > 2:
                    raise ValueError("More than two original context samples in a taxon")
                if len(taxon_ctx) == 2:
                    pair_rows.append({"source_hash": masked, "cohort": cohort,
                                      "class": diag["class"], "taxon": taxon,
                                      "first": taxon_ctx[0], "second": taxon_ctx[1]})
    if len(rows) != 20 or len(pair_rows) != 14:
        raise ValueError("Changed macroecological support: expected 20 source slopes and 14 same-taxon pairs")
    if sum(x["cohort"] == "earlier" for x in rows) != 10:
        raise ValueError("Original study-sample radiation support changed")
    return rows, pair_rows, frame


def between_source_associations(rows, draws=BOOT):
    results = {}
    for i, cov in enumerate(COVARIATES):
        cohorts = {}
        for j, subset in enumerate((rows,
                                    [r for r in rows if r["cohort"] == "earlier"],
                                    [r for r in rows if r["cohort"] == "external"])):
            label = ("pooled", "earlier", "external")[j]
            r = spearman([x["slope"] for x in subset], [x[cov] for x in subset])
            loo = [spearman([q["slope"] for q in subset if q is not row],
                            [q[cov] for q in subset if q is not row]) for row in subset]
            if r is None or any(v is None for v in loo):
                raise ValueError("Source rank correlation or leave-one-out is undefined")
            cohorts[label] = {"source_studies": len(subset), "spearman_rho": r,
                              "leave_one_study_out_range": [min(loo), max(loo)],
                              **bootstrap_rho(subset, cov, SEED + 100 * i + j, draws)}
        results[cov] = cohorts
    return results


def within_study_context_pairs(pairs, draws=BOOT):
    results = {}
    for i, (name, field) in enumerate(COVARIATES.items()):
        by_source = defaultdict(list)
        contrast = []
        for p in pairs:
            a, b = p["first"], p["second"]
            if a[field] == b[field]:
                continue
            hi, lo = (a, b) if a[field] > b[field] else (b, a)
            by_source[p["source_hash"]].append(hi["slope"] - lo["slope"])
            contrast.append(abs(a[field] - b[field]))
        aggregate = [mean(d) for d in by_source.values()]
        rng = random.Random(SEED + i + 2000)
        boots = [mean(aggregate[rng.randrange(len(aggregate))]
                      for _ in aggregate) for _ in range(draws)] if len(aggregate) >= 5 else []
        results[name] = {
            "same_taxon_original_context_pairs": sum(map(len, by_source.values())),
            "original_study_sources": len(aggregate),
            "mean_change_in_shortwave_slope_in_higher_context": mean(aggregate) if aggregate else None,
            "positive_study_source_mean_deltas": sum(x > 0 for x in aggregate),
            "negative_study_source_mean_deltas": sum(x < 0 for x in aggregate),
            "original_study_resampling_95": interval(boots),
            "mean_absolute_environment_difference": mean(contrast) if contrast else None,
        }
    return results


def run(early=EARLY, late=LATE, diagnostic=AUDIT, draws=BOOT):
    a, b, d = load(early), load(late), load(diagnostic)
    if d["prior_frozen_external_replication_decision_UNCHANGED"] != \
            "NEGATIVE_DIRECTION_NOT_REPLICATED_IN_HELDOUT_SOURCE_SAMPLE":
        raise ValueError("Registered source replication decision was modified")
    rows, pairs, frame = build_rows(a, b, d)
    return {
        "version": "solar-irradiance-direction-macro-gradient-v0",
        "date": "2026-10-26",
        "inference": "POSTHOC_DESCRIPTIVE_OBSERVATIONAL_SOURCE_SAMPLE_ONLY",
        "preregistered_external_verdict_UNCHANGED":
            d["prior_frozen_external_replication_decision_UNCHANGED"],
        "source_denominator": {"earlier": 24, "external": 24, "total": 48,
                               "defined_source_radiation_slopes": len(rows),
                               "undefined_source_radiation_slopes": len(frame) - len(rows)},
        "between_original_study_source_correlations": between_source_associations(rows, draws),
        "within_original_study_same_taxon_context_comparisons": within_study_context_pairs(pairs, draws),
        "source_sample_support": frame,
        "ecological_interpretation_ceiling": [
            "Study source is the highest independent sampling unit; two taxa in one archive are not independent source studies.",
            "The 48 archived studies were not a probability sample of world biomes or taxa.",
            "Correlations and source bootstrap intervals are descriptive, selected after both original solar radiation outcomes.",
            "Source mean ERA5 weather and 15-degree latitude bands are proxies, not animal exposure or measured solar elevation.",
            "Within-study same-taxon paired contexts are not independent populations and cannot isolate sun elevation, route or individual history.",
            "No causal sun compass, thermoregulation, habitat selection or global radiation avoidance mechanism is identified.",
            "Full original raw animal GPS, individual identifiers, and exact locations/times are never emitted.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "research/SOLAR_IRRADIANCE_DIRECTION_MACRO_GRADIENT_FIRST_RESULT_20261026.json")
    parser.add_argument("--draws", type=int, default=BOOT)
    args = parser.parse_args()
    if args.draws < 10:
        parser.error("--draws must be >= 10")
    result = run(draws=args.draws)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("48 original source studies; 20 defined source slopes; 14 original within-taxon context pairs")
    for key, r in result["between_original_study_source_correlations"].items():
        print(key, r["pooled"]["spearman_rho"], r["earlier"]["spearman_rho"], r["external"]["spearman_rho"])
    print("FROZEN_REPLICATION_VERDICT_UNCHANGED")


if __name__ == "__main__":
    main()
