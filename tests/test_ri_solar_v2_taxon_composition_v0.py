"""Hash-locked original-result-only composition diagnostics.

Tests use fabricated original-result JSON, not original wildlife data.
Only official CI reads the first exact empirical receipt by pinned SHA256.
"""
from __future__ import annotations

import hashlib
import json
import math

import pytest

from odsp.ri_solar_v2_taxon_composition_v0 import (
    METHOD_VERSION, analyze_pinned_taxonomic_receipt,
)


def _fixture():
    one=lambda val,sites:{
        "unique_physical_site_count":sites,
        "metrics":{"solar_over_clock":{"mean":val}}
    }
    original={
        "method_version":"odsp-ri-solar-vs-clock-yearseason-v2-exploratory",
        "status":"EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE",
        "scored_heldout_events":19916,
        "heldout_site_count":43,
        "primary_heldout_solar_clock":{"season_groups":{
            "winter":one(.02745845931504319,43),
            "summer":one(-.0325742873706785,43),
        }},
        "species_secondary_descriptive":{
            "sciurus carolinensis":{
                "scored_images_after_dedup":120,
                "winter":one(.05,11),"summer":one(-.06,12),
            },
            "vulpes vulpes":{
                "scored_images_after_dedup":260,
                "winter":one(-.02,12),"summer":one(.04,14),
            },
            "aves sp.":{
                "scored_images_after_dedup":1200,
                "winter":one(.03,14),"summer":one(.02,10),
            },
            "neovison vison":{
                "scored_images_after_dedup":10,
                "winter":one(.02,12),"summer":one(.01,12),
            },
        }
    }
    raw=json.dumps(original,sort_keys=True).encode()
    plan={
        "schema_version":1,
        "analysis_id":"ri-solar-v2-postoutcome-taxon-composition-sensitivity-v0",
        "status":"POST_OUTCOME_DESCRIPTIVE_EXPLORATION_NOT_CONFIRMATORY",
        "no_significance_tests_or_resampled_p_values":True,
        "never_reclassify_v0_v1_v2_or_any_qualified_route":True,
        "input":{
            "original_receipt_json_sha256":hashlib.sha256(raw).hexdigest(),
            "first_frozen_v2_result_run":37747931559,
            "known_primary_winter_solar_gain":.02745845931504319,
            "known_primary_summer_solar_gain":-.0325742873706785,
        },
        "minimum_each_season_site_count":8,
        "minimum_total_taxon_scored_events":100,
        "explicit_taxa_nonmammal_or_non_species":[
            "aves sp.","meleagris gallopavo",
            "rodentia sp.","canis familiaris",
        ]
    }
    return raw,plan


def test_provisional_taxon_equal_mean_does_not_promote_missing_year_support():
    raw,plan=_fixture()
    d=analyze_pinned_taxonomic_receipt(raw,plan)
    assert d["method_version"]==METHOD_VERSION
    assert d["original_status_unchanged"]=="EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE"
    assert d["original_both_season_solar_superiority_supported"] is False
    assert d["taxon_screen"]["provisional_site_event_pass_count"]==2
    assert d["taxon_screen"]["fully_eligible_taxa_count"] is None
    assert d["taxon_screen"]["status"]=="HOLD_CANNOT_VERIFY_PER_TAXON_TWO_FUTURE_YEAR_RULE"
    assert d["taxon_screen"]["per_taxon_future_year_count_available"] is False
    assert d["provisional_taxon_equal_weight"]["winter_mean"]==pytest.approx(.015)
    assert d["provisional_taxon_equal_weight"]["summer_mean"]==pytest.approx(-.01)
    assert d["provisional_taxon_equal_weight"]["winter_positive_summer_negative_count"]==1
    assert d["provisional_taxon_equal_weight"]["winter_negative_summer_positive_count"]==1
    assert d["provisional_taxon_equal_weight"]["significance_or_coverage_certified"] is False
    assert d["provisional_taxon_equal_weight"]["composition_explains_sign_reversal_established"] is False
    assert d["original_ecological_v0_v1_v2_inference_reclassified"] is False
    assert d["no_raw_zenodo_source_reopened"] is True
    assert d["known_nonwild_or_unresolved_taxa_event_total"]==1200
    json.dumps(d,allow_nan=False)


def test_hash_mismatch_or_original_status_change_fails_closed():
    raw,plan=_fixture()
    with pytest.raises(ValueError,match="SHA256"):
        analyze_pinned_taxonomic_receipt(raw+b"\n",plan)
    tamper=json.loads(raw)
    tamper["status"]="EXPLORATORY_SOLAR_TRANSPORT_SIGNAL"
    other=json.dumps(tamper).encode()
    plan["input"]["original_receipt_json_sha256"]=hashlib.sha256(other).hexdigest()
    with pytest.raises(ValueError,match="scientific status"):
        analyze_pinned_taxonomic_receipt(other,plan)


def test_primary_result_not_redefined_as_equal_taxon_average():
    raw,plan=_fixture()
    d=analyze_pinned_taxonomic_receipt(raw,plan)
    assert d["original_all_site_weighted_gains"]["winter"]==pytest.approx(
        .02745845931504319
    )
    assert d["provisional_taxon_equal_weight"]["winter_mean"]!=d[
        "original_all_site_weighted_gains"
    ]["winter"]
    assert d["provisional_taxon_equal_weight"]["not_original_primary_estimand"] is True
    assert d["exact_matched_site_or_within_taxon_season_composition_decomposition_identified"] is False


def test_new_screen_rules_or_nonfinite_scores_rejected():
    raw,plan=_fixture()
    plan["minimum_each_season_site_count"]=2
    with pytest.raises(ValueError,match="thresholds altered"):
        analyze_pinned_taxonomic_receipt(raw,plan)
    raw,plan=_fixture()
    obj=json.loads(raw)
    obj["species_secondary_descriptive"]["vulpes vulpes"]["summer"][
        "metrics"
    ]["solar_over_clock"]["mean"]=float("nan")
    tampered=json.dumps(obj).encode()
    plan["input"]["original_receipt_json_sha256"]=hashlib.sha256(tampered).hexdigest()
    with pytest.raises(ValueError,match="finite"):
        analyze_pinned_taxonomic_receipt(tampered,plan)
