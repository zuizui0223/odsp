"""Central-directory-only RI technical recovery safety tests.

All ZIP bytes here are fabricated and contain no animal outcome data.
"""
from __future__ import annotations

import hashlib
import io
import stat
import zipfile

import pytest

from odsp import ri_zipinfo_technical_recovery_v0 as m


def _archive(extra=(), *, compressed=zipfile.ZIP_STORED) -> bytes:
    output=io.BytesIO()
    with zipfile.ZipFile(output,"w",compression=compressed) as z:
        z.writestr("DataS1/RI_CameraSurvey_Deployments.csv","a,b\\n1,2\\n")
        z.writestr("DataS1/RI_CameraSurvey_Detections.csv","a,b\\n3,4\\n")
        for name,bytes_ in extra:
            z.writestr(name,bytes_)
    return output.getvalue()


def _audit_synthetic(raw, monkeypatch):
    monkeypatch.setattr(m,"SOURCE_MD5",hashlib.md5(raw).hexdigest())
    return m.inspect_ri_pinned_zip_central_directory(raw)


def test_two_known_zip_members_pass_without_decompression(monkeypatch):
    raw=_archive()
    def forbidden_open(*args,**kwargs):
        raise AssertionError("no ZIP source member may be opened by structural audit")
    monkeypatch.setattr(zipfile.ZipFile,"open",forbidden_open)
    out=_audit_synthetic(raw,monkeypatch)
    assert out.archive_md5_verified
    assert out.expected_csv_member_count==2
    assert out.expected_named_members_present_exactly_once
    assert out.content_or_detection_values_read is False
    assert out.csv_member_contents_decompressed is False
    assert out.source_schema_or_estimand_modified is False
    assert out.recovery_eligibility=="TECHNICAL_ZIP_RECOVERY_ELIGIBLE"


def test_real_source_md5_mismatch_stops_before_any_member(monkeypatch):
    raw=_archive()
    monkeypatch.setattr(m,"SOURCE_MD5","a"*32)
    with pytest.raises(ValueError,match="MD5 mismatch"):
        m.inspect_ri_pinned_zip_central_directory(raw)


@pytest.mark.parametrize("name,payload,reason",[
    ("data/third_source.csv","x,y\\n2,3\\n","extra CSV"),
    ("../DataS1/README.md","sneaky","safe relative"),
    ("/unsafe.txt","sneaky","safe relative"),
    ("DataS1/RI_CameraSurvey_Detections.csv","dup","exactly two|duplicate"),
])
def test_unfrozen_sources_cannot_expand_archive_set(
    monkeypatch,name,payload,reason,
):
    raw=_archive([(name,payload)])
    with pytest.raises(ValueError,match=reason):
        _audit_synthetic(raw,monkeypatch)


def test_ancillary_txt_allowed_but_never_read(monkeypatch):
    raw=_archive([("DataS1/README.txt","ancillary non-outcome note")])
    out=_audit_synthetic(raw,monkeypatch)
    assert out.ancillary_non_csv_entry_count==1
    assert out.expected_csv_member_count==2


def test_compressed_archive_ratio_guard_rejects_zip_bomb(monkeypatch):
    raw=_archive(
        [("DataS1/note.txt","z"*200000)],compressed=zipfile.ZIP_DEFLATED
    )
    with pytest.raises(ValueError,match="expansion ratio"):
        _audit_synthetic(raw,monkeypatch)


def test_failed_member_count_fails_without_reading_content(monkeypatch):
    raw=_archive([(f"logs/log-{i}.txt","x") for i in range(79)])
    with pytest.raises(ValueError,match="member count"):
        _audit_synthetic(raw,monkeypatch)


def test_source_contract_has_locked_recovery_only_bounds():
    assert m.SOURCE_MD5=="c66943e6c2a9aab0abce2a1eba8ce02e"
    assert m.MAX_ARCHIVE==75_000_000
    assert m.MAX_MEMBERS==80
    assert m.MAX_TOTAL_EXPANDED==600_000_000
    assert m.MAX_MEMBER_EXPANDED==500_000_000
    assert m.MAX_EXPANSION_RATIO==60.0
