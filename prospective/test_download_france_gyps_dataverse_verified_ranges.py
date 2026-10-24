"""Pure offline tests of exact published Dataverse byte-range assembly."""
import hashlib
import pytest
from prospective import download_france_gyps_dataverse_verified_ranges as m

def test_ranges_cover_entire_archive_without_overlap():
    x=m.planned_ranges(total=20,chunk=7)
    assert x==[(0,0,6),(1,7,13),(2,14,19)]
    assert sum(end-start+1 for i,start,end in x)==20

def test_invalid_requested_chunk_or_empty_source_denied():
    with pytest.raises(ValueError):
        m.planned_ranges(total=0,chunk=7)
    with pytest.raises(ValueError):
        m.planned_ranges(total=20,chunk=0)

def test_assembly_verifies_published_md5_without_loading_all_in_RAM(tmp_path,monkeypatch):
    data=b"abcdefghijklmnopqrs"
    monkeypatch.setattr(m,"TOTAL",len(data))
    monkeypatch.setattr(m,"MD5",hashlib.md5(data).hexdigest())
    parts=tmp_path/"parts";parts.mkdir()
    ranges=m.planned_ranges(total=len(data),chunk=7)
    for i,s,e in ranges:
        (parts/f"{i:04d}.part").write_bytes(data[s:e+1])
    target=tmp_path/"original.zip"
    size,hash_result=m.assemble(parts,target,ranges)
    assert size==len(data)
    assert target.read_bytes()==data
    assert hash_result==hashlib.md5(data).hexdigest()

def test_corrupt_download_part_rejected(tmp_path,monkeypatch):
    data=b"abcdefghijklmnopqrs"
    monkeypatch.setattr(m,"TOTAL",len(data))
    monkeypatch.setattr(m,"MD5",hashlib.md5(data).hexdigest())
    parts=tmp_path/"parts";parts.mkdir()
    rng=m.planned_ranges(total=len(data),chunk=7)
    for i,s,e in rng:
        b=bytearray(data[s:e+1])
        if i==1:b[0]=ord("Z")
        (parts/f"{i:04d}.part").write_bytes(b)
    outfile=tmp_path/"bad.zip"
    with pytest.raises(ValueError,match="published byte count/MD5"):
        m.assemble(parts,outfile,rng)
    assert not outfile.exists()
