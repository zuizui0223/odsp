import importlib.util
import json
from pathlib import Path
from statistics import NormalDist
import math

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"run_uljin_published_table3_species_contrasts_v0.py"
spec=importlib.util.spec_from_file_location("table3",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def valid():
    return json.loads((ROOT/"ULJIN_PUBLISHED_TABLE3_SEASONAL_SPECIES_CONTRAST_V0.json").read_text())


def test_full_four_species_and_six_familywise_comparisons():
    a=m.audit(valid())
    assert a["status"]=="EXPLORATORY_PUBLISHED_TABLE3_CONDITIONAL_DETECTION_ONLY"
    assert len(a["comparisons"])==6
    assert sum(r["family_sign_distinguished_under_approximation"] for r in a["comparisons"])==1
    assert not a["confirmatory_preregistration_claimed"]
    assert not a["latent_animal_activity_or_causal_claim"]


def test_water_deer_vs_wild_boar_se_unknown_covariance_conservative():
    a=m.audit(valid())
    p=next(r for r in a["comparisons"] if r["species_a"]=="Water deer" and r["species_b"]=="Wild boar")
    assert abs(p["season_detection_logit_beta_difference_a_minus_b"]-2.122)<1e-10
    assert abs(p["cross_species_se_upper_bound"]-0.625)<1e-10
    assert abs(p["six_pair_bonferroni_adjusted_p_upper_bound"]-0.00411471)<2e-5
    lo,hi=p["fwer95_worst_cov_wald_ci"]
    assert .47<lo<.48 and 3.76<hi<3.78
    assert p["family_sign_distinguished_under_approximation"]
    assert p["shared_best_supported_model"]
    assert abs(p["ratio_of_model_season_detection_odds_ratios"]-math.exp(2.122))<1e-5


def test_invalid_source_claims_and_taxon_selection_fail_closed():
    c=valid()
    c["original_2022_41_pair_animal_evidence"]=True
    try: m.audit(c)
    except ValueError: pass
    else: raise AssertionError("source-data status must be conserved")
    c=valid()
    c["coefficients"].pop()
    try: m.audit(c)
    except ValueError: pass
    else: raise AssertionError("all four species must remain")


def test_assumed_covariance_variance_no_larger_than_sum_se_sq():
    water,boar=.378,.247
    for rho in (-1,-.8,0,.8,1):
        var=water**2+boar**2-2*rho*water*boar
        assert var <= (water+boar)**2+1e-12
    assert abs(m.STANDARD_NORMAL.inv_cdf(1-0.05/(2*6))-NormalDist().inv_cdf(1-0.05/12))<1e-12
