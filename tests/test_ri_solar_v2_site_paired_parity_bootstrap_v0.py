"""Known-truth site bootstrap geometry, no Rhode Island observations here."""
from __future__ import annotations

from datetime import date
import json
import math
from pathlib import Path

import pytest

from odsp.ri_solar_clock_transfer_v0 import DielEvent,site_is_sealed
from odsp.ri_solar_v2_site_paired_parity_bootstrap_v0 import (
    VERSION,paired_site_season_parity_interval,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads(
    (ROOT/"RI_SOLAR_V2_SITE_PAIRED_SEASON_PARITY_BOOTSTRAP_CONTRACT.json").read_text()
)


def _sites(n=43):
    result=[]
    for i in range(1000):
        name=f"synthetic-heldout-site-{i:04d}"
        if site_is_sealed(name):
            result.append(name)
            if len(result)==n:
                return result
    raise AssertionError("synthetic site hash fixture failed")


def _rows():
    scores=[]
    for site in _sites():
        for year in (2022,2023):
            for season in ("winter","summer"):
                e=DielEvent(
                    site_id=site,
                    species="synthetic-mammal",
                    season=season,
                    season_year=year,
                    day=date(year,1 if season=="winter" else 7,10),
                    clock_hour=8.,
                    latitude=41.4,
                    longitude=-71.5,
                )
                scores.append((e,{
                    "solar_over_clock":.2 if season=="winter" else -.1,
                    "solar_season_over_solar":.01,
                    "clock_season_over_clock":.05,
                }))
    return scores


def _plan():
    p=json.loads(json.dumps(PLAN))
    p["first_original"]["winter_solar_minus_clock"]=.2
    p["first_original"]["summer_solar_minus_clock"]=-.1
    p["first_original"]["winter_pooled_solar_95_lower"]=.2
    p["first_original"]["summer_pooled_solar_95_lower"]=-.1
    return p


def test_predeclared_same_physical_site_weights_preserve_joint_covariance():
    out=paired_site_season_parity_interval(_rows(),_plan())
    assert out["method_version"]==VERSION
    assert out["scored_events"]==172
    assert out["original_heldout_sites"]==43
    assert out["bootstrap_draws"]==2000
    assert out["bootstrap_random_sites_reused_across_seasons"]
    winter=out["season_groups"]["winter"]
    summer=out["season_groups"]["summer"]
    assert winter["conditional_solar_season_minus_clock_season_mean"]==pytest.approx(.16)
    assert summer["conditional_solar_season_minus_clock_season_mean"]==pytest.approx(-.14)
    assert winter["paired_site_multiplier_bootstrap_95_percentile_lower"]==pytest.approx(.16)
    assert winter["paired_site_multiplier_bootstrap_95_percentile_upper"]==pytest.approx(.16)
    assert summer["paired_site_multiplier_bootstrap_95_percentile_lower"]==pytest.approx(-.14)
    assert summer["paired_site_multiplier_bootstrap_95_percentile_upper"]==pytest.approx(-.14)
    assert out["original_result_exactly_replayed_before_new_interval"]
    assert out["original_primary_both_seasons_solar_superiority_supported"] is False
    assert out["all_confirmatory_claims_prohibited"] is True
    json.dumps(out,allow_nan=False)


def test_year_repeat_does_not_create_additional_site_replication():
    full=_rows()
    duplicated=full+full
    # Duplicating every event preserves within-year means, and therefore
    # each site's contribution; site count remains 43, not 86.
    original=paired_site_season_parity_interval(full,_plan())
    repeated=paired_site_season_parity_interval(duplicated,_plan())
    for season in ("winter","summer"):
        assert original["season_groups"][season]==repeated["season_groups"][season]


def test_original_replay_mismatch_and_wrong_site_support_fail_closed():
    p=_plan()
    p["first_original"]["winter_pooled_solar_95_lower"]=.195
    with pytest.raises(ValueError,match="original same-site mean or bootstrap"):
        paired_site_season_parity_interval(_rows(),p)
    with pytest.raises(ValueError,match="changed original heldout site"):
        paired_site_season_parity_interval(
            [row for row in _rows() if row[0].site_id!=_sites()[0]],
            _plan()
        )


def test_after_outcome_bootstrap_alpha_and_seed_immutable():
    p=_plan()
    p["bootstrap"]["percentiles_two_sided"]=[.05,.95]
    with pytest.raises(ValueError,match="frozen paired bootstrap changed"):
        paired_site_season_parity_interval(_rows(),p)


def test_missing_scoring_component_blocks_new_interval():
    rows=_rows()
    del rows[0][1]["solar_season_over_solar"]
    with pytest.raises(ValueError,match="invalid original scoring cell"):
        paired_site_season_parity_interval(rows,_plan())
