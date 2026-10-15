#!/usr/bin/env python3
"""Exploratory covariance-robust contrast audit of PUBLISHED Table 3 coefficients.

NOT source event analysis; does not read protected locations or original
camera timestamps. Conservative for all possible cross-species estimate
correlations *within the asymptotic normal and given-SE approximation*.
No upstream model-selection uncertainty, ecological mechanism or timing.
"""
from __future__ import annotations

from itertools import combinations
from math import erfc, exp, sqrt
from pathlib import Path
from statistics import NormalDist
import argparse
import json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_PUBLISHED_TABLE3_SEASONAL_SPECIES_CONTRAST_V0.json"
STANDARD_NORMAL=NormalDist()


def audit(contract:dict)->dict:
    if contract.get("schema_version")!=1 or contract.get("contract_id")!="uljin_published_table3_species_season_detection_correlation_bound_v0":
        raise ValueError("wrong published-source contract")
    if contract.get("analysis_class")!="POST_PUBLICATION_EXPLORATORY_REANALYSIS_NOT_PREREGISTERED" or contract.get("original_2022_41_pair_animal_evidence") is not False:
        raise ValueError("published outcome must not be mislabelled preregistered/original 41-pair")
    rows=contract["coefficients"]
    if [r["species"] for r in rows]!=["Goral","Water deer","Roe deer","Wild boar"]:
        raise ValueError("all four original species required, no outcome selection")
    if any(r["se"] <= 0 for r in rows) or len({r["species"] for r in rows})!=4:
        raise ValueError("invalid reported SE or duplicated taxa")
    alpha=float(contract["comparison"]["alpha_family"])
    if not 0 < alpha < 1:
        raise ValueError("invalid family alpha")
    if contract["comparison"]["cross_species_covariance"]!="UNKNOWN_BOUND_BY_CAUCHY_SCHWARZ":
        raise ValueError("cross-species dependency assumption not allowed")
    pairs=list(combinations(rows,2))
    if len(pairs)!=6:
        raise ValueError("six unordered species contrasts are required")
    zcritical=STANDARD_NORMAL.inv_cdf(1-alpha/(2*len(pairs)))
    result=[]
    for a,b in pairs:
        delta=round(float(a["beta"])-float(b["beta"]),12)
        se_bound=float(a["se"])+float(b["se"])
        z=abs(delta)/se_bound
        p_unadj_upper_bound=erfc(z/sqrt(2))
        p_fwer_bound=min(1.0,len(pairs)*p_unadj_upper_bound)
        lo=delta-zcritical*se_bound
        hi=delta+zcritical*se_bound
        result.append({
            "species_a":a["species"],
            "species_b":b["species"],
            "season_detection_logit_beta_difference_a_minus_b":delta,
            "cross_species_se_upper_bound":round(se_bound,12),
            "z_lower_bound_abs":round(z,8),
            "normal_two_sided_p_upper_bound":round(p_unadj_upper_bound,9),
            "six_pair_bonferroni_adjusted_p_upper_bound":round(p_fwer_bound,9),
            "fwer95_worst_cov_wald_ci":[round(lo,6),round(hi,6)],
            "ratio_of_model_season_detection_odds_ratios":round(exp(delta),6),
            "family_sign_distinguished_under_approximation":lo>0 or hi<0,
            "shared_best_supported_model":a["best_model"]==b["best_model"],
        })
    return {
        "status":"EXPLORATORY_PUBLISHED_TABLE3_CONDITIONAL_DETECTION_ONLY",
        "article_doi":contract["data_source"]["article_doi"],
        "frozen_original_mirror_data_not_analyzed":True,
        "source_beta_or_se_reestimated":False,
        "seasonal_covariate":"summer vs winter; NOT early-May-June vs July-August",
        "dependency_bound":"se_delta <= se_a+se_b by Cauchy-Schwarz",
        "normal_approximation_and_reported_standard_errors_assumed":True,
        "upstream_model_selection_uncertainty_included":False,
        "confirmatory_preregistration_claimed":False,
        "all_six_pairs_retained":True,
        "bonferroni_critical_z":round(zcritical,9),
        "comparisons":result,
        "latent_animal_activity_or_causal_claim":False
    }


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--contract",type=Path,default=CONTRACT)
    a=parser.parse_args()
    print(json.dumps(audit(json.loads(a.contract.read_text())),indent=2,sort_keys=True))


if __name__=="__main__":
    main()
