import pytest
from prospective.grus_grus_dryad_v4_manifest import parse_filelist,PILOT

def source():
    files=[]
    for i in range(32):
        name=f"{16000+i}_1HzGPS_and_ACC_annotated.csv"
        files.append({"path":name,"size":300+i,"digest":"a"*64,
            "_links":{"self":{"href":f"/api/v2/files/{5000+i}"}}})
    for i,(name,(fileid,sha,size)) in enumerate(PILOT.items()):
        files[i]={"path":name,"size":size,"digest":sha,
                 "_links":{"self":{"href":f"/api/v2/files/{fileid}"}}}
    # Restore exactly 32 original raw GPS file names by adding one for pilot
    # (README replaced one raw name)
    files.append({"path":"16500_1HzGPS_and_ACC_annotated.csv","size":300,
                  "digest":"b"*64,"_links":{"self":{"href":"/api/v2/files/6023"}}})
    for i in range(4):
        files.append({"path":f"other{i}.csv","size":100,
                      "digest":"c"*64,"_links":{"self":{"href":f"/api/v2/files/{6100+i}"}}})
    assert len(files)==37
    assert sum("1HzGPS_and_ACC_annotated" in f["path"] for f in files)==32
    return {"total":37,"_embedded":{"stash:files":files}}


def test_37_files_32_bird_source_notalts():
    o=parse_filelist(source())
    assert o["record_files"]==37
    assert o["raw_individual_1Hz_csv_files"]==32
    assert o["native_GPS_height_values_read"] is False
    assert o["files"]["README.md"]["official_file_id"]=="2905498"


def test_partial_pagination_fails_not_32_birds():
    x=source();x["_embedded"]["stash:files"].pop()
    with pytest.raises(ValueError,match="incomplete"):
        parse_filelist(x)


def test_source_hash_change_fails():
    x=source();x["_embedded"]["stash:files"][1]["digest"]="c"*64
    with pytest.raises(ValueError,match="pilot"):
        parse_filelist(x)


def test_archived_source_publication_44_birds_not_raw_CSV_count():
    r=parse_filelist(source())
    assert r["source_reported_tracking_birds"]==44
    assert r["raw_individual_1Hz_csv_files"]!=r["source_reported_tracking_birds"]
