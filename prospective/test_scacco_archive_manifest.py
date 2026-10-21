from prospective.scacco_archive_manifest import parse_record, RECORD_ID,DOI

def synthetic():
    return {
      "id":RECORD_ID,"doi":DOI,
      "metadata":{"title":"Test record","publication_date":"2026-08-01",
                  "license":{"id":"cc-by-4.0"}},
      "files":[
        {"key":"Data.zip","size":120000000,"checksum":"md5:"+"a"*32},
        {"key":"Readme_Metadata.txt","size":1000,"checksum":"md5:"+"b"*32},
        {"key":"Table_allDatasets_contacts_permits.pdf","size":230,"checksum":"md5:"+"c"*32}
      ],
      "access":{"record":"public","files":"public"}
    }

def test_frozen_source_metadata_validates():
    j=parse_record(synthetic())
    assert j["source"].endswith(str(RECORD_ID))
    assert j["files"]["Data.zip"]["bytes"]==120000000
    assert j["license_id"]=="cc-by-4.0"
    assert j["stage"]=="ARCHIVE_MANIFEST_ONLY"
    assert j["native_gps_altitude_values_read"] is False

def test_wrong_doi_fails():
    x=synthetic()
    x["doi"]="10.5281/zenodo.1"
    import pytest
    with pytest.raises(ValueError,match="DOI"):
        parse_record(x)

def test_missing_checksum_does_not_silently_accept():
    x=synthetic()
    x["files"][0]["checksum"]=None
    import pytest
    with pytest.raises(ValueError,match="checksum"):
        parse_record(x)

def test_no_unexpected_missing_files():
    x=synthetic()
    x["files"]=[f for f in x["files"] if f["key"]!="Data.zip"]
    import pytest
    with pytest.raises(ValueError,match="drifted"):
        parse_record(x)
