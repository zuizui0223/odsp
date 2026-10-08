"""Frozen public-archive structure and event cleaning regressions."""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

import pytest

from odsp import ri_solar_source_v0 as source


# Read the pre-result frozen aliases instead of accidentally testing a
# narrower, incompatible duplicate alias table (old test omitted SiteID).
ROOT = Path(__file__).resolve().parents[1]
ALIASES = json.loads(
    (ROOT / "ODSP_RI_SOLAR_CLOCK_TRANSFER_V0_CONTRACT.json").read_text()
)["source_schema_predeclared_aliases"]


def test_yearseason_is_explicit_not_inferred_from_photo_calendar_year():
    assert source._parse_season("Winter_2022")==("winter",2022)
    assert source._parse_season("2023 Summer")==("summer",2023)
    assert source._parse_season("2023_Spring") is None
    assert source._parse_season("2025 Summer") is None


def test_source_v3_is_image_level_and_dedup_rule_is_predeclared():
    assert source.SOURCE_MD5 == "c66943e6c2a9aab0abce2a1eba8ce02e"
    assert source.EXPECTED_MEMBERS == {
        "RI_CameraSurvey_Deployments.csv",
        "RI_CameraSurvey_Detections.csv",
    }
    assert "human" in source.EXCLUDED_NAMES
    assert "unidentified" in source.EXCLUDED_NAMES


def test_strict_schema_and_timestamps_do_not_guess_missing_fields():
    aliases=dict(ALIASES)
    matched,rows=source._schema(
        [{"Site":"s","Camera":"c","Species":"raccoon",
          "YearSeason":"Winter_2022","Date":"2022-12-20",
          "Time":"21:15:00"}],
        aliases,
        required=("site","camera","species","yearseason"),
        one_of_datetime=True,
    )
    assert matched["site"]=="Site"
    assert matched["detection_date"]=="Date"
    assert source._parse_clock_datetime(rows[0],matched)==datetime(
        2022,12,20,21,15
    )
    with pytest.raises(ValueError,match="date and local clock-time"):
        source._schema(
            [{"Site":"s","Camera":"c","Species":"raccoon",
              "YearSeason":"Winter_2022"}],
            aliases,
            required=("site","camera","species","yearseason"),
            one_of_datetime=True,
        )


def test_ambiguous_column_aliases_fail_without_posthoc_inference():
    row={"Site":"s","SiteID":"different","Camera":"c","Species":"fox",
         "YearSeason":"Winter_2022","Date":"2022-12-01","Time":"19:00"}
    with pytest.raises(ValueError,match="ambiguous"):
        source._schema([row],ALIASES,required=("site","camera","species","yearseason"))


def test_dst_ambiguous_and_nonexistent_clock_times_fail_closed():
    # America/New_York spring gap and autumn duplicated hour.
    assert source._dst_clock_hour_maybe_invalid(
        datetime(2022,3,13,2,30)
    )
    assert source._dst_clock_hour_maybe_invalid(
        datetime(2022,11,6,1,30)
    )
    assert not source._dst_clock_hour_maybe_invalid(
        datetime(2022,7,15,18,30)
    )


def test_timestamp_format_unknown_does_not_estimate_solar_phase():
    aliases=dict(ALIASES)
    names,rows=source._schema(
        [{"Site":"s","Camera":"c","Species":"fox",
          "YearSeason":"Winter_2022","Date":"unknown",
          "Time":"21:15:00"}],
        aliases,required=("site","camera","species","yearseason"),
        one_of_datetime=True
    )
    assert source._parse_clock_datetime(rows[0],names) is None


def test_zip_file_source_hash_mismatch_fails_before_outcomes():
    with pytest.raises(ValueError,match="MD5"):
        source._member_zip_csv(b"fake source archive")
