"""Synthetic tests for post-exposure matched site/taxon descriptive contrast.

No Rhode Island wildlife data or scored result is read by these tests.
"""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import pytest

from odsp.ri_solar_v2_matched_site_taxon_v0 import (
    METHOD,describe_matched_site_taxon_pairs,
)
from odsp.ri_solar_clock_transfer_v0 import DielEvent,site_is_sealed

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"RI_SOLAR_V2_MATCHED_SITE_TAXON_V0_CONTRACT.json").read_text())


def _heldout_sites(n=5):
    out=[]
    for i in range(1000):
        candidate=f"heldout-demo-site-{i:04d}"
        if site_is_sealed(candidate):
            out.append(candidate)
            if len(out)==n:
                return out
    raise AssertionError("could not make enough sealed synthetic sites")


def _scored(sites, taxa=("synthetic mammal","aves sp."),years=(2022,2023),
            events_per_unit=5):
    records=[]
    for site in sites:
        for taxon in taxa:
            for year in years:
                for season in ("winter","summer"):
                    for i in range(events_per_unit):
                        ev=DielEvent(
                            site_id=site,species=taxon,
                            season=season,season_year=year,
                            day=date(year,1 if season=="winter" else 7,20),
                            clock_hour=float(8+i),latitude=41.5,longitude=-71.6
                        )
                        # Species contrast must stay within the same
                        # physical site: no taxon turnover needed.
                        gain=(.2 if season=="winter" else -.1)
                        if taxon=="aves sp.":
                            gain=-.03 if season=="winter" else .02
                        records.append((ev,{"solar_over_clock":gain}))
    return records


def test_matched_site_taxon_detects_within_pair_season_difference_without_pvalues():
    scores=_scored(_heldout_sites(5))
    d=describe_matched_site_taxon_pairs(scores,PLAN)
    assert d["method_version"]==METHOD
    assert d["matched_site_taxon_pairs"]==10
    assert d["physical_sites_with_at_least_one_paired_taxon"]==5
    assert d["taxa_with_at_least_one_matched_pair"]==2
    assert d["all_reported_matched_pairs"]["winter_equal_cell_mean"]==pytest.approx(.085)
    assert d["all_reported_matched_pairs"]["summer_equal_cell_mean"]==pytest.approx(-.04)
    assert d["all_reported_matched_pairs"]["winter_minus_summer_mean"]==pytest.approx(.125)
    assert d["site_balanced_matched_pairs"]["winter_minus_summer"]==pytest.approx(.125)
    assert d["taxon_balanced_matched_pairs"]["winter_minus_summer"]==pytest.approx(.125)
    assert d["wild_identified_mammal_like_matched_pairs_count"]==5
    assert d["wild_identified_mammal_like_site_pair_descriptive"][
        "winter_minus_summer_mean"]==pytest.approx(.3)
    assert d["taxon_year_support_across_all_scored_events"][
        "synthetic mammal"]["observed_both_2022_2023"] is True
    assert d["same_site_taxon_paired_winter_summer_verified"] is True
    assert d["causal_solar_mechanism_identified"] is False
    assert d["all_new_p_values_or_confirmatory_interval_computed"] is False
    assert d["no_individual_site_ids_or_detection_time_values_output"] is True
    result=json.dumps(d,allow_nan=False)
    assert "heldout-demo-site-" not in result


def test_pair_requires_both_seasons_at_the_same_physical_site():
    scored=_scored(_heldout_sites(5))
    # Remove all summer detections of one taxon at one physical site.
    site=scored[0][0].site_id
    excluded=[
        (e,x) for e,x in scored
        if not (e.site_id==site and e.species=="synthetic mammal" and e.season=="summer")
    ]
    d=describe_matched_site_taxon_pairs(excluded,PLAN)
    assert d["matched_site_taxon_pairs"]==9


def test_pair_site_floor_fail_closed_without_changing_threshold():
    with pytest.raises(ValueError,match="insufficient predeclared matched"):
        describe_matched_site_taxon_pairs(_scored(_heldout_sites(3)),PLAN)


def test_year_support_is_visible_but_not_confused_with_matching():
    d=describe_matched_site_taxon_pairs(
        _scored(_heldout_sites(5),years=(2022,)),PLAN
    )
    assert d["taxon_year_support_across_all_scored_events"][
        "synthetic mammal"]["observed_future_year_count"]==1
    assert d["taxon_year_support_across_all_scored_events"][
        "synthetic mammal"]["observed_both_2022_2023"] is False
    assert d["matched_site_taxon_pairs"]==10


def test_postoutcome_changed_pair_threshold_or_unsealed_source_rejected():
    frozen=json.loads(json.dumps(PLAN))
    frozen["matched_cell_rule"]["min_dedup_scored_events_in_each_season"]=1
    with pytest.raises(ValueError,match="thresholds changed"):
        describe_matched_site_taxon_pairs(_scored(_heldout_sites(5)),frozen)
    site="train-only-not-heldout"
    while site_is_sealed(site):
        site+="-x"
    event=DielEvent(site_id=site,species="synthetic mammal",
        season="winter",season_year=2022,day=date(2022,1,1),
        clock_hour=4.5,latitude=41.5,longitude=-71.5)
    with pytest.raises(ValueError,match="nonheldout"):
        describe_matched_site_taxon_pairs(
            _scored(_heldout_sites(5))+[(event,{"solar_over_clock":.2})],
            PLAN
        )
