import hashlib
import io
import importlib.util
import zipfile
from pathlib import Path
import pytest

p=Path(__file__).resolve().parents[1]/"scripts"/"inspect_uljin_published_supp2_solar_overlap_v0.py"
s=importlib.util.spec_from_file_location("source2",p)
m=importlib.util.module_from_spec(s)
s.loader.exec_module(m)


def mk(filename,data):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z: z.writestr(filename,data)
    return b.getvalue()


def test_safe_published_solar_overlap_only(monkeypatch):
    b=mk("solar_overlap.csv","Species1,Species2,Delta\nWater deer,Wild boar,0.633\n")
    monkeypatch.setattr(m,"MD5",hashlib.md5(b).hexdigest())
    o=m.analyze(b)
    assert o["tables"][0]["rows"][0]["Delta"]=="0.633"
    assert not o["original_41_mirror_dates_tested"]
    assert not o["independent_replication_claimed"]


def test_no_protected_station_fields_exposed(monkeypatch):
    b=mk("solar.csv","Station,longitude,Value\nUJ1-private,129.4,8\n")
    monkeypatch.setattr(m,"MD5",hashlib.md5(b).hexdigest())
    o=m.analyze(b)
    assert o["tables"][0]["status"]=="HOLD_SENSITIVE_SOURCE_FIELD"
    assert "UJ1-private" not in str(o)


def test_expected_publisher_md5_required():
    with pytest.raises(ValueError,match="HASH_MISMATCH"):
        m.analyze(mk("solar.csv","a,b\n1,2\n"))
