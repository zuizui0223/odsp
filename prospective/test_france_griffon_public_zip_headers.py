import pytest
import io,zipfile
from prospective.france_griffon_public_zip_headers import detect_fields

def test_headers_only_known_movebank_tags_and_3d_coords():
    x=detect_fields(["timestamp","individual-local-identifier",
                    "location-long","location-lat","height-above-msl",
                    "ground-speed"])
    assert x["could_support_native_3d_tracking"]
    assert x["numeric_native_height_values_opened"] is False
    assert x["height_column_names_only"]==["height-above-msl"]

def test_only_2d_fields_is_not_native_3d_source():
    x=detect_fields(["timestamp","animal-id","longitude","latitude"])
    assert not x["could_support_native_3d_tracking"]
    assert x["height_column_names_only"]==[]

def test_unknown_source_table_does_not_fake_gps_xy():
    x=detect_fields(["area","count","site","date"])
    assert not x["could_support_native_3d_tracking"]

def test_tag_id_cannot_be_mistaken_for_height():
    x=detect_fields(["tag-id","lat","lon","timestamp","velocity"])
    assert x["animal_or_tag_columns"]
    assert not x["height_column_names_only"]
