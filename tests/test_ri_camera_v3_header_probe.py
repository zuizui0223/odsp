"""RI camera v3 one-line schema audit, with no observed ecological records."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest

from odsp import ri_camera_v3_header_probe as probe
from odsp import ri_zipinfo_technical_recovery_v0 as zipguard

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"RI_CAMERA_V3_HEADER_ONLY_PROBE_CONTRACT.json").read_text())
ALIASES=json.loads(
    (ROOT/"ODSP_RI_SOLAR_CLOCK_TRANSFER_V0_CONTRACT.json").read_text()
)["source_schema_predeclared_aliases"]


def _archive(*, first_deployment="Site,Camera,YearSeason,Latitude,Longitude",
             first_detection="Site,Camera,YearSeason,Species,Date,Time",
             extra=None):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",compression=zipfile.ZIP_STORED) as archive:
        archive.writestr(
            "DataS1/RI_CameraSurvey_Deployments.csv",
            first_deployment+"\n" +
            "UNREAD_DEPLOYMENT_ROW,SECRET,2019 Winter,41,-71\n"
        )
        archive.writestr(
            "DataS1/RI_CameraSurvey_Detections.csv",
            first_detection+"\n" +
            "UNREAD_DETECTION_ROW,SECRET,2019 Winter,UNREAD_TAXON,21:15:00\n"
        )
        if extra:
            archive.writestr(*extra)
    return stream.getvalue()


def _inspect(raw,monkeypatch):
    md5=hashlib.md5(raw).hexdigest()
    monkeypatch.setattr(zipguard,"SOURCE_MD5",md5)
    monkeypatch.setattr(probe,"SOURCE_MD5",md5)
    plan=json.loads(json.dumps(PLAN))
    plan["source"]["md5"]=md5
    return probe.inspect_camera_archive_headers_only(raw,plan,ALIASES)


def test_both_headers_only_are_reported_and_no_data_values_leak(monkeypatch):
    result=_inspect(_archive(),monkeypatch)
    assert result["source_zip_member_count"]==2
    assert len(result["source_headers"])==2
    assert result["source_data_row_values_read_by_this_probe"] is False
    assert result["source_data_row_values_may_have_been_read_by_prior_v0_workflow"] is True
    assert result["heldout_scores_computed"] is False
    assert result["empirical_primary_qualified"] is False
    payload=json.dumps(result)
    assert "UNREAD_TAXON" not in payload
    assert "UNREAD_DETECTION_ROW" not in payload
    assert "UNREAD_DEPLOYMENT_ROW" not in payload
    assert result["source_headers"]["RI_CameraSurvey_Deployments.csv"][
        "frozen_alias_diagnostics"]["site"]["mapping_authorized"
    ] is True


def test_unknown_site_and_camera_schema_is_not_guessable(monkeypatch):
    result=_inspect(_archive(
        first_deployment="StationCode,LocationNumber,YearSeason,Latitude,Longitude",
        first_detection="StationCode,LocationNumber,YearSeason,Animal,Date,Time"
    ),monkeypatch)
    matching=result["source_headers"]["RI_CameraSurvey_Deployments.csv"][
        "frozen_alias_diagnostics"
    ]
    assert matching["site"]["mapping_authorized"] is False
    assert matching["camera"]["mapping_authorized"] is False
    assert result["original_v0_frozen_source_aliases_amended"] is False


def test_mutiple_site_aliases_are_detected_but_not_selected(monkeypatch):
    result=_inspect(_archive(
        first_deployment="Site,SiteID,Camera,YearSeason,Latitude,Longitude"
    ),monkeypatch)
    status=result["source_headers"]["RI_CameraSurvey_Deployments.csv"][
        "frozen_alias_diagnostics"]["site"]
    assert status["original_frozen_alias_match_count"]==2
    assert status["mapping_authorized"] is False


def test_member_metadata_failure_blocks_all_header_open(monkeypatch):
    with pytest.raises(ValueError,match="extra CSV"):
        _inspect(_archive(extra=("evil.csv","Species\nsecret\n")),monkeypatch)


def test_oversized_or_malformed_single_line_fails_closed(monkeypatch):
    too_long="A"*65537
    with pytest.raises(ValueError,match="exceeds frozen"):
        _inspect(_archive(first_deployment=too_long),monkeypatch)
    with pytest.raises(ValueError,match="unterminated quoted"):
        _inspect(_archive(first_deployment='Site,Camera,"badquote'),monkeypatch)


def test_missing_contract_or_frozen_source_identity_refuses_probe(monkeypatch):
    raw=_archive()
    frozen=json.loads(json.dumps(PLAN))
    with pytest.raises(ValueError,match="schema-probe"):
        probe.inspect_camera_archive_headers_only(raw,{**frozen,"contract_id":"other"},ALIASES)
    with pytest.raises(ValueError,match="source identity"):
        probe.inspect_camera_archive_headers_only(
            raw,{**frozen,"source":{**frozen["source"],"md5":"bad"}},ALIASES
        )
