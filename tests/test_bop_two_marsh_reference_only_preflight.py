"""Source-only preflight tests. All individual identities here are synthetic.

Never read, download or simulate GPS/height/location event outcomes.
"""
from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import io
import json

import pytest

from scripts.bop_two_marsh_reference_only_preflight import (
    _contract, _rows, _summarize, classify_checked_reference_bytes,
    V1_PATH,V2_PATH,
)

HEADER=("tag-id","animal-id","animal-taxon","alt-project-id","study-site")


def _csv_bytes(study:str,animal_count:int,*, reuse_tag:bool=False,
               replace_animal:str|None=None)->bytes:
    file=io.StringIO(newline="")
    writer=csv.DictWriter(file,fieldnames=HEADER,lineterminator="\n")
    writer.writeheader()
    for idx in range(animal_count):
        animal=f"{study}-synthetic-animal-{idx:03d}"
        if replace_animal and idx==animal_count-1:
            animal=replace_animal
        tag=f"{study}-synthetic-tag-{idx:03d}"
        if reuse_tag and idx==animal_count-1:
            tag=f"{study}-synthetic-tag-000"
        writer.writerow({
            "tag-id":tag,"animal-id":animal,
            "animal-taxon":"Circus aeruginosus",
            "alt-project-id":study,"study-site":"SYNTHETIC_STUDY",
        })
    return file.getvalue().encode("utf-8")


def _artificial_inputs(*,reuse_tag=True,overlap=False):
    p={
        "MH_WATERLAND":_csv_bytes("MH_WATERLAND",7,reuse_tag=reuse_tag),
        "H_GRONINGEN":_csv_bytes(
            "H_GRONINGEN",4,
            replace_animal=("MH_WATERLAND-synthetic-animal-006" if overlap else None),
        ),
    }
    a,b=_contract()
    a=deepcopy(a);b=deepcopy(b)
    for rec in a["fixed_archive_versions"]:
        label=rec["study"]
        digest=hashlib.md5(p[label]).hexdigest()
        rec["reference_md5"]=digest
    # Unit fixtures ONLY; these are not source observations or a proposal
    # to replace the permanent pre-access recorded source MD5 values.
    return p,a,b


def test_original_contract_was_preaccess_source_only_and_still_fails_schema():
    a,b=_contract()
    assert a["frozen_date"]=="2026-10-28"
    assert a["source_access_allowlist"]==[
        "https://zenodo.org/records/10053583/files/MH_WATERLAND-reference-data.csv",
        "https://zenodo.org/records/10053658/files/H_GRONINGEN-reference-data.csv",
    ]
    assert a["access_constraints"]["no_GPS_event_files"] is True
    assert a["min_new_calibration_entities_per_stratum"]==9
    assert a["min_new_untouched_validation_entities_per_stratum"]==1
    assert [x["reference_md5"] for x in a["fixed_archive_versions"]]==[
        "b76cc93d9be67b814f1a3be646f84269",
        "944d7d2488914b1b528b76812dea48f9",
    ]
    assert b["created_after_source_header_access"] is True
    assert b["v1_schema_mismatch"].startswith("SOURCE_SCHEMA_HOLD")
    assert "animal-id" not in a["metadata_schema_policy"]["required_individual_field_candidates"]


def test_two_pinned_source_reference_fixtures_reveal_animal_tag_reuse_and_hold():
    inputs,a,b=_artificial_inputs(reuse_tag=True)
    answer=classify_checked_reference_bytes(inputs,v1=a,v2=b)
    assert answer["original_v1_terminal"]=="SOURCE_SCHEMA_HOLD"
    assert answer["source_access"]=="TWO_MD5_VERIFIED_REFERENCE_CSV_FILES_ONLY"
    assert answer["status"]=="REFERENCE_ID_AND_TAG_REUSE_AUDIT_ONLY"
    assert answer["external_rank_admission_status"]=="HOLD_POPULATION_AND_IDENTITY_EXCHANGEABILITY_UNVERIFIED"
    assert answer["upper_bound_distinct_candidate_animals_by_exact_string"]==11
    assert answer["identical_animal_id_strings_shared_across_studies"]==0
    assert answer["identical_tag_id_strings_shared_across_studies"]==0
    assert answer["within_study_rank_90pct_nonvacuous_any"] is False
    assert answer["hypothetical_pooled_count_at_least_10"] is True
    assert [x["unique_species_animals"] for x in answer["studies"]]==[7,4]
    assert [x["unique_tag_identifiers"] for x in answer["studies"]]==[6,4]
    assert [x["different_animals_sharing_a_tag_count"] for x in answer["studies"]]==[1,0]
    assert answer["historical_MH_ANTWERPEN_already_opened_and_excluded"] is True
    assert answer["GPS_height_or_location_events_accessed"] is False
    assert answer["new_external_prediction_claim"] is False
    assert answer["original_BOP_terminal"]=="empirical_state_prediction_mixed"
    doc=json.dumps(answer,ensure_ascii=False,allow_nan=False)
    assert "synthetic-animal" not in doc
    assert "synthetic-tag" not in doc
    assert "SYNTHETIC_STUDY" not in doc


def test_same_animal_string_across_sources_is_detectable_but_not_a_crosswalk():
    inputs,a,b=_artificial_inputs(overlap=True)
    ans=classify_checked_reference_bytes(inputs,v1=a,v2=b)
    assert ans["identical_animal_id_strings_shared_across_studies"]==1
    assert ans["upper_bound_distinct_candidate_animals_by_exact_string"]==10
    assert ans["actual_same_animal_under_different_IDs_not_excluded"] is True
    assert ans["external_rank_admission_status"].startswith("HOLD_")


@pytest.mark.parametrize("attack,reason",[
    ("wrong_md5","MD5 mismatch"),
    ("gps_line","MD5 mismatch"),
    ("missing_file","exact two whitelisted"),
    ("duplicate_header","no unique header"),
    ("wrong_species","unexpected species"),
    ("wrong_study","does not match fixed study"),
    ("blank_id","empty or malformed"),
    ("missing_field","cannot parse required"),
])
def test_source_file_or_identity_tampering_never_promotes_external_data(attack,reason):
    inputs,a,b=_artificial_inputs()
    if attack=="wrong_md5":
        inputs["MH_WATERLAND"]+=b"\n"
    elif attack=="gps_line":
        inputs["MH_WATERLAND"]+=b"\nGPS,height-above-msl,12,33"
    elif attack=="missing_file":
        del inputs["H_GRONINGEN"]
    elif attack=="duplicate_header":
        inputs["MH_WATERLAND"]=inputs["MH_WATERLAND"].replace(
            b"tag-id,animal-id,animal-taxon,alt-project-id,study-site",
            b"tag-id,animal-id,animal-id,alt-project-id,study-site"
        )
        a["fixed_archive_versions"][0]["reference_md5"]=hashlib.md5(inputs["MH_WATERLAND"]).hexdigest()
    elif attack in ("wrong_species","wrong_study","blank_id","missing_field"):
        before=inputs["MH_WATERLAND"]
        if attack=="wrong_species":
            inputs["MH_WATERLAND"]=before.replace(b"Circus aeruginosus",b"Circus cyaneus",1)
        elif attack=="wrong_study":
            inputs["MH_WATERLAND"]=before.replace(b"MH_WATERLAND,SYNTHETIC_STUDY",b"ANOTHER_STUDY,SYNTHETIC_STUDY",1)
        elif attack=="blank_id":
            inputs["MH_WATERLAND"]=before.replace(b"MH_WATERLAND-synthetic-animal-000",b"",1)
        else:
            inputs["MH_WATERLAND"]=before.replace(b"animal-id",b"NO_ANIMAL_ID",1)
        a["fixed_archive_versions"][0]["reference_md5"]=hashlib.md5(inputs["MH_WATERLAND"]).hexdigest()
    with pytest.raises(ValueError,match=reason):
        classify_checked_reference_bytes(inputs,v1=a,v2=b)


def test_invalid_reference_csv_length_and_checksum_rejected_even_with_valid_schema():
    inputs,a,b=_artificial_inputs()
    with pytest.raises(ValueError,match="small"):
        _rows(b"x"*10_001,expected_md5=hashlib.md5(b"x"*10_001).hexdigest())
    with pytest.raises(ValueError,match="MD5"):
        _rows(inputs["H_GRONINGEN"],expected_md5="0"*32)


def test_file_roles_not_swapped():
    inputs,a,b=_artificial_inputs()
    swapped={
        "MH_WATERLAND":inputs["H_GRONINGEN"],
        "H_GRONINGEN":inputs["MH_WATERLAND"],
    }
    with pytest.raises(ValueError,match="MD5 mismatch"):
        classify_checked_reference_bytes(swapped,v1=a,v2=b)
