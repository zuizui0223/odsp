"""Code-only archive reading, zip-bomb/path/byte provenance adversarial tests."""
from __future__ import annotations
import hashlib
import io
import json
import zipfile
from copy import deepcopy

import pytest

from scripts.bop_red_kite_2024_package_code_only_v1 import (
    CONTRACT,_load_frozen,_digest,extract_R_sources,source_pattern_hits,
    summarize,
)


def mock_zip(files:dict[str,bytes])->bytes:
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as f:
        for name,raw in files.items():
            f.writestr(name,raw)
    return out.getvalue()


def setup_fixture(*,ending=b"\n",change=False):
    ref=b"data_prep <- function(minlocs=800) {\n number_of_fixes > minlocs\n}\n"
    data_prep=ref.replace(b"\n",ending)
    if change:
        data_prep=data_prep.replace(b"> minlocs",b">= minlocs")
    z=mock_zip({
        "NestTool/R/data_prep.R":data_prep,
        "NestTool/R/example.R":b"hour<-floor_date(x,'hour')\n",
        "NestTool/data/models.RData":b"\x00\xffSECRET_BREEDING_DATA_DO_NOT_DECODE",
        "NestTool/inst/source.csv":b"\xff\xfeNEVER_READ_ME",
    })
    script=b"length(unique(GERseasondata$bird_id))\nGERseasondata %>% filter(year_id %in% unique(GER_data_input$summary$year_id))\n"
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    c["authorized_downloads"][0]["size_bytes"]=len(z)
    c["authorized_downloads"][0]["provider_md5"]=hashlib.md5(z).hexdigest()
    c["authorized_downloads"][1]["size_bytes"]=len(script)
    c["authorized_downloads"][1]["provider_md5"]=hashlib.md5(script).hexdigest()
    c["reference_source"]["git_blob_sha1"]=_digest(ref)["git_blob_sha1"]
    return z,script,ref,c


def test_real_pre_access_code_source_whitelist_and_historical_git_ref_pinned():
    c=_load_frozen()
    assert [x["name"] for x in c["authorized_downloads"]]==[
        "NestTool-1.0.0.zip","NestTool_archived_full_analysis.r"
    ]
    assert c["authorized_downloads"][0]["provider_md5"]=="b172b87191f00f221e9d0151c61d65a6"
    assert c["reference_source"]["git_blob_sha1"]=="3fa42eddbfb852d5dbc29364281bffef8410563e"
    assert c["strict_access"]["no_CSV_or_GPS_file_downloads"] is True
    assert c["strict_access"]["no_model_or_RData_RDS_binary_member_extraction"] is True
    assert c["no_claim_promotion"]["BOP_historical_terminal"]=="empirical_state_prediction_mixed"
    assert c["no_claim_promotion"]["red_kite_biological_terminal"]=="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"


def test_synthetic_code_only_byte_match_excludes_sensitive_binary_members():
    z,script,ref,c=setup_fixture()
    out=summarize(z,script,ref,c)
    assert out["status"]=="PACKAGE_CODE_EXACT_GIT_MATCH"
    assert out["zip"]["provider_md5_verified"] is True
    assert out["zip"]["R_member_count"]==2
    assert out["data_prep_exact_bytes_equal"] is True
    assert out["data_prep_equal_after_EOL_normalization"] is True
    assert out["zip_R_data_prep_member_path"]=="NestTool/R/data_prep.R"
    assert out["zip_data_prep_static_patterns"]["number_of_fixes > minlocs"]==[2]
    assert out["archived_top_level_script"]["pattern_line_numbers"]["length(unique(GERseasondata$bird_id))"]==[1]
    assert out["no_GPS_or_reproductive_labels_accessed"] is True
    payload=json.dumps(out,sort_keys=True)
    assert "SECRET_BREEDING_DATA" not in payload
    assert "NEVER_READ_ME" not in payload
    assert "number_of_fixes > minlocs\n" not in payload


def test_normalized_newline_vs_real_source_change_are_different_termini():
    z,script,ref,c=setup_fixture(ending=b"\r\n")
    out=summarize(z,script,ref,c)
    assert out["status"]=="PACKAGE_CODE_EOL_ONLY_DIFFERENCE"
    assert out["data_prep_exact_bytes_equal"] is False
    assert out["data_prep_equal_after_EOL_normalization"] is True
    z,script,ref,c=setup_fixture(change=True)
    out=summarize(z,script,ref,c)
    assert out["status"]=="PACKAGE_CODE_DIFFERENCE"
    assert out["data_prep_equal_after_EOL_normalization"] is False


@pytest.mark.parametrize("name",[
    "../R/data_prep.R",
    "/tmp/R/data_prep.R",
    r"NestTool\R\data_prep.R",
    "NestTool/R/../../R/data_prep.R",
])
def test_archive_path_traversal_or_windows_absolute_is_not_allowed(name):
    z=mock_zip({name:b"number_of_fixes > minlocs\n"})
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    with pytest.raises(ValueError,match="unsafe"):
        extract_R_sources(z,c["strict_access"])


def test_duplicate_data_prep_sources_and_missing_code_fail_closed():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    many=mock_zip({"NestTool/R/data_prep.R":b"x\n","Other/R/data_prep.R":b"y\n"})
    with pytest.raises(ValueError,match="one and only one"):
        extract_R_sources(many,c["strict_access"])
    empty=mock_zip({"NestTool/data/secret.csv":b"should not parse"})
    with pytest.raises(ValueError,match="one and only one"):
        extract_R_sources(empty,c["strict_access"])


def test_decompression_cap_enforced_before_member_decode():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    z=mock_zip({"NestTool/R/data_prep.R":b"a"*(1048576+1)})
    with pytest.raises(ValueError,match="per-member"):
        extract_R_sources(z,c["strict_access"])


def test_wrong_source_MD5_or_historical_git_blob_fails():
    z,script,ref,c=setup_fixture()
    changed=deepcopy(c)
    changed["authorized_downloads"][0]["provider_md5"]="0"*32
    with pytest.raises(ValueError,match="unmodified official archive CODE data"):
        summarize(z,script,ref,changed)
    changed=deepcopy(c)
    changed["reference_source"]["git_blob_sha1"]="0"*40
    with pytest.raises(ValueError,match="blob bytes"):
        summarize(z,script,ref,changed)


def test_static_pattern_positions_are_bounded_and_do_not_export_lines():
    src=(b"subsampling here\n"*20)
    hits=source_pattern_hits(src,["subsampl","absent"],max_lines=8)
    assert hits["subsampl"]==list(range(1,9))
    assert hits["absent"]==[]
