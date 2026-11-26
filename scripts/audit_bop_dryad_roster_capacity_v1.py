"""Source-free cardinality and fixed-n power audit for BOP/Dryad.

All results are conditional on the published counts describing distinct
biological animals, stable taxon assignment, and Data_1a being a subset of
the 280-animal source. Counts do not identify animals or prove sampling IID.
"""
from fractions import Fraction
from math import comb
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    "dryad_contract": (
        "research/BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_CONTRACT.json",
        "8c64697f1a5cfa1441344285205c6651a843bc98",
    ),
    "bop_roster": (
        "research/BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_FIRST_RESULT.json",
        "8112156ac82bfe3302e34f2e5d142bab61458b4c",
    ),
    "dryad_recheck": (
        "BOP_DRYAD_FIRST_ARTIFACT_RECHECK_V3_RECEIPT.json",
        "c4d75029b0ad9038bf96c7cc57a031a1384d2aa2",
    ),
}
TAXA = ("Circus pygargus", "Circus cyaneus", "Circus aeruginosus", "Buteo buteo")
CONTENT = Fraction(9, 10)
ALPHA = Fraction(1, 20)
NEEDED = 30


def checked_json(root, relpath, sha):
    raw = (root / relpath).read_bytes()
    blob = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
    if blob != sha:
        raise ValueError(f"immutable source blob mismatch: {relpath}")
    return json.loads(raw)


def _count(value):
    if type(value) is not int or value < 0:
        raise ValueError("counts must be nonnegative exact integers")
    return value


def novelty_bounds(source_counts, excluded_counts, retained_total, taxa):
    """Sharp marginal bounds, and sharp joint total for the chosen taxa.

    No known forced overlap. Each same-species excluded roster is an upper
    bound on the number of source animals that could overlap. A shared global
    omission budget must be subtracted ONCE for the joint total.
    """
    total = sum(_count(v) for v in source_counts.values())
    for v in excluded_counts.values():
        _count(v)
    retained = _count(retained_total)
    if retained > total or not taxa or len(set(taxa)) != len(taxa):
        raise ValueError("inconsistent retained total or duplicate target taxa")
    if any(s not in source_counts or s not in excluded_counts for s in taxa):
        raise ValueError("every target taxon needs explicit source and exclusion counts")
    omitted = total - retained
    nonoverlap_whole = {
        s: max(0, source_counts[s] - excluded_counts[s]) for s in taxa
    }
    per_taxon = {
        s: {
            "published_total": source_counts[s],
            "excluded_roster_upper_bound": excluded_counts[s],
            "data_1a_novel_lower": max(0, nonoverlap_whole[s] - omitted),
            "data_1a_novel_upper": min(source_counts[s], retained),
        } for s in taxa
    }
    return {
        "global_omission_budget": omitted,
        "taxa": per_taxon,
        "joint_novel_lower": max(0, sum(nonoverlap_whole.values()) - omitted),
        "joint_novel_upper": min(sum(source_counts[s] for s in taxa), retained),
        "joint_not_a_pooled_species_content_sample": True,
    }


def failure_limit(n):
    """Largest nonpositive count with exact one-sided binomial p <= .05."""
    n = _count(n)
    term = CONTENT ** n
    tail = Fraction(0)
    for x in range(n + 1):
        tail += term
        if tail > ALPHA:
            return x - 1
        term *= Fraction(n - x, 9 * (x + 1))
    return n


def exact_power(n, p):
    """Prospective power under IID Bernoulli gain-positive probability p."""
    if not isinstance(p, Fraction) or not 0 <= p <= 1:
        raise ValueError("power alternative must be an exact probability")
    k = failure_limit(n)
    return sum(
        (Fraction(comb(n, x)) * p ** (n - x) * (1 - p) ** x
         for x in range(k + 1)), Fraction(0)
    )


def best_fixed_n_power(max_n, p):
    """Enumerate all fixed designs; discreteness makes power nonmonotone.

    This is an optimistic design ceiling, not permission to select n after
    observing gains or to stop at a favorable significance result.
    """
    max_n = _count(max_n)
    if max_n < NEEDED - 1:
        return None
    score, n = max((exact_power(n, p), -n) for n in range(NEEDED - 1, max_n + 1))
    n = -n
    return {
        "best_fixed_calibration_n": n,
        "maximum_nonpositive_count": failure_limit(n),
        "maximum_power": float(score),
    }


def audit(root=ROOT):
    sources = {k: checked_json(root, *v) for k, v in INPUTS.items()}
    dryad = sources["dryad_contract"]["candidate"]["readme_public_metadata"]
    counts = dryad["species_counts"]
    total = dryad["dataset_total_tagged_individuals"]
    retained = dryad["data_1a_distinct_individuals"]
    if sum(counts.values()) != total or (total, retained) != (280, 271):
        raise ValueError("published aggregate denominator mismatch")
    roster = sources["bop_roster"]
    if roster["source_version_dois"] != [
        "10.5281/zenodo.10055071", "10.5281/zenodo.17310324"
    ]:
        raise ValueError("unexpected BOP reference versions")
    references = roster["references"]
    if len(references) != 2:
        raise ValueError("unexpected number of roster versions")
    scenarios = {}
    for name, ref, expected_total in zip(("v3", "v2026"), references, (35, 45)):
        exclusion = ref["species_counts"]
        if sum(exclusion.values()) != expected_total or ref["distinct_animal_ids"] != expected_total:
            raise ValueError("BOP reference count denominator mismatch")
        bound = novelty_bounds(counts, exclusion, retained, TAXA)
        for row in bound["taxa"].values():
            lo = row["data_1a_novel_lower"]
            hi = row["data_1a_novel_upper"]
            row["count_capacity_at_least_30_under_stated_assumptions"] = lo >= NEEDED
            row["additional_exclusion_budget_if_lower_at_least_30"] = (
                lo - NEEDED if lo >= NEEDED else None
            )
            row["optimistic_max_calibration_n_with_one_reserved"] = max(0, hi - 1)
        scenarios[name] = bound
    prior = sources["dryad_recheck"]["subsequent_verification"]
    if prior["small_sidecars_source_status"] != "HTTP_403_ALL_THREE":
        raise ValueError("unexpected prior source access receipt")
    # All fixed n <= whole-source count - one reserved validation animal.
    # Choose these numerical alternatives for planning only, not as estimates.
    power = {
        s: {
            str(p): best_fixed_n_power(counts[s] - 1, p)
            for p in (Fraction(19, 20), Fraction(49, 50))
        } for s in TAXA
    }
    return {
        "schema_version": 1,
        "stage": "aggregate_count_and_design_power_after_metadata_exploration",
        "input_git_blob_sha1s": {k: v[1] for k, v in INPUTS.items()},
        "published_total": total,
        "data_1a_published_total": retained,
        "scenarios": scenarios,
        "power": {
            "null_positive_fraction": str(CONTENT),
            "alpha": str(ALPHA),
            "reserved_validation_animals": 1,
            "optimistic_fixed_design_ceiling_by_species": power,
            "iid_assumption_required": True,
            "not_a_post_outcome_sample_size_rule": True,
        },
        "prior_small_sidecar_access_status": prior["small_sidecars_source_status"],
        "no_new_provider_request": True,
        "no_gps_or_target_outcome_read": True,
        "canonical_identity_resolved": False,
        "usable_feature_and_altitude_eligibility_verified": False,
        "real_source_admitted": False,
        "historic_bop_terminal": "empirical_state_prediction_mixed",
        "historic_dryad_rf_terminal": "NOT_ADMITTED",
        "new_common_input_terminal": "HOLD_METADATA_OR_PERMISSION",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True, indent=2, allow_nan=False))
