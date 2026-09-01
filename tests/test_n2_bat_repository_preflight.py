import hashlib

from scripts.n2_bat_repository_preflight import (
    canonical_name,
    parse_csv,
    verify_source,
)


def test_movebank_hyphen_headers_are_canonicalized_without_values():
    data = (
        b"timestamp,location-lat,location-long,height-above-ellipsoid,"
        b"individual-local-identifier\n"
        b"2020-01-01 00:00:00,1,2,DO_NOT_PARSE,BAT1\n"
    )
    headers, rows = parse_csv(data)
    assert "height_above_ellipsoid" in headers
    assert "individual_local_identifier" in headers
    assert rows[0]["height_above_ellipsoid"] == "DO_NOT_PARSE"


def test_header_canonicalization_is_structural_only():
    assert canonical_name("Height-Above-Ellipsoid") == "height_above_ellipsoid"
    assert canonical_name("location long") == "location_long"


def test_verify_source_uses_frozen_size_and_md5():
    data = b"abc"
    verify_source(
        data,
        {
            "filename": "x.csv",
            "size_bytes": 3,
            "checksum_type": "MD5",
            "checksum": hashlib.md5(data).hexdigest(),
        },
    )
