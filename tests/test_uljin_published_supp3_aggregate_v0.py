"""Synthetic ZIP regression checks; never pass test fixtures as biology."""
import hashlib
import io
import json
import zipfile
import pytest
import importlib.util
from pathlib import Path
FILE=Path(__file__).resolve().parents[1]/"scripts"/"inspect_uljin_published_supp3_aggregate_v0.py"
sp=importlib.util.spec_from_file_location("published_supp3",FILE)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)


def mkzip(files):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        for k,v in files.items(): z.writestr(k,v)
    return b.getvalue()


def test_valid_public_summary_synthetic_fixture_never_original(monkeypatch):
    raw=mkzip({"public/s3.tsv":"species\tperiod\tdetections_per_100_hours\nGoral\tday\t12.4\n"})
    monkeypatch.setattr(m,"ZENODO_MD5",hashlib.md5(raw).hexdigest())
    o=m.inspect(raw)
    assert o["status"]=="VERIFIED_ZENODO_SUPPL3_NOT_ECOBANK_ORIGINAL"
    assert o["tables"][0]["rows"][0]["detections_per_100_hours"]=="12.4"
    assert not o["original_source_2022_41_pairs_loaded"]
    assert not o["new_biological_hypothesis_tested"]


def test_location_data_never_exposed(monkeypatch):
    raw=mkzip({"rates.tsv":"species\tstation\tlat\tcount\nGoral\tPRIVATE_1\t37.0\t8\n"})
    monkeypatch.setattr(m,"ZENODO_MD5",hashlib.md5(raw).hexdigest())
    o=m.inspect(raw)
    assert o["tables"][0]["status"]=="HOLD_GEO_OR_STATION_IDENTIFIERS"
    assert o["tables"][0]["rows"] is None
    assert "PRIVATE_1" not in json.dumps(o)


def test_published_checksum_mismatch_fails_closed():
    raw=mkzip({"rates.tsv":"species\tzone\nGoral\tnight\n"})
    with pytest.raises(ValueError,match="MD5"):
        m.inspect(raw)


def test_path_traversal_fails_even_when_fixture_hash_matches(monkeypatch):
    raw=mkzip({"../sneaky.tsv":"species\trate\nGoral\t4\n"})
    monkeypatch.setattr(m,"ZENODO_MD5",hashlib.md5(raw).hexdigest())
    with pytest.raises(ValueError,match="UNSAFE"):
        m.inspect(raw)
