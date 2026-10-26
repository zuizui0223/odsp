from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest

from scripts.bop_v3_v2026_reference_roster_preflight_v1 import (
    CONTRACT, audit_reference_rosters, build_report,
    contract_from_bytes, parse_animals, _source_bytes,
)


def _contract():
    return contract_from_bytes(CONTRACT.read_bytes())


def _source(roster):
    stream=io.StringIO()
    writer=csv.writer(stream)
    writer.writerow(["animal-id","animal-taxon","deployment-id"])
    for identity,taxon in roster.items():
        writer.writerow([identity,taxon,"tag1"])
        writer.writerow([identity,taxon,"tag2"])
    return stream.getvalue().encode("utf-8")


def _old_and_new():
    old={"H200701":"Buteo buteo","H200730":"Buteo buteo"}
    old.update({f"OLD{i:03d}":"Circus cyaneus" for i in range(33)})
    new={f"OLD{i:03d}":"Circus cyaneus" for i in range(33)}
    new["H197221"]="Buteo buteo"
    new.update({f"NEW{i:03d}":"Circus pygargus" for i in range(11)})
    assert len(old)==35 and len(new)==45
    return old,new


def test_frozen_contract_allows_reference_data_and_no_gps_paths():
    c=_contract()
    assert [x["record_id"] for x in c["source_versions"]]==[10055071,17310324]
    assert c["only_authorized_download"].startswith("two pinned reference-data.csv")
    assert c["original_frozen_terminal"]=="empirical_state_prediction_mixed"
    assert c["source_versions"][0]["md5"]=="81e85243e38823db4bde56e315b596f8"
    assert c["source_versions"][1]["md5"]=="fc4623f4dd5f32ef228b3dae386b2c1a"


def test_provider_alias_removed_old_and_11_new_in_one_species():
    old,new=_old_and_new()
    analysis=audit_reference_rosters(old,new,_contract())
    assert analysis["overlapping_corrected_animal_ids"]==34
    assert analysis["new_id_candidates_count"]==11
    assert analysis["applied_known_alias_count"]==1
    assert analysis["old_removed_out_of_scope_count"]==1
    assert analysis["new_id_candidates_by_species"]=={"Circus pygargus":11}
    assert analysis["scientific_status"]=="METADATA_ONLY_CANDIDATE_NEEDS_OUTCOME_BLIND_GPS_ELIGIBILITY"
    assert analysis["original_empirical_BOP_terminal_changed"] is False


def test_new_id_total_does_not_infer_stratum_rank_support():
    old,new=_old_and_new()
    for i in range(11):
        new[f"NEW{i:03d}"] = (
            "Circus pygargus" if i<5 else "Circus aeruginosus"
        )
    audit=audit_reference_rosters(old,new,_contract())
    assert audit["new_id_candidates_count"]==11
    assert audit["scientific_status"]=="NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT"
    assert not any(audit["new_id_candidates_within_stratum_meet_min_count"].values())


def test_csv_deployment_repeats_are_not_independent_animals():
    old,new=_old_and_new()
    observed,metadata=parse_animals(
        _source(old), ["animal-id","animal-taxon"]
    )
    assert len(observed)==35
    assert metadata["distinct_animal_ids"]==35
    assert metadata["reference_rows"]==70
    assert len(metadata["identity_taxon_roster_sha256"])==64
    assert "H200701" not in json.dumps(metadata)


def test_source_only_full_audit_checks_frozen_public_individual_counts():
    old,new=_old_and_new()
    report=build_report(reference_bytes=(_source(old),_source(new)))
    assert report["gps_event_data_accessed"] is False
    assert report["old_original_terminal"]=="empirical_state_prediction_mixed"
    assert report["references"][0]["distinct_animal_ids"]==35
    assert report["references"][1]["distinct_animal_ids"]==45
    assert report["identity_audit"]["new_id_candidates_count"]==11
    assert "OLD000" not in json.dumps(report)
    assert "NEW000" not in json.dumps(report)


@pytest.mark.parametrize("mode,match",[
    ("missing_header","declared animal-id/animal-taxon"),
    ("empty_identity","missing animal identity"),
    ("taxon_conflict","conflicting taxa"),
])
def test_broken_reference_schema_fails_closed(mode,match):
    if mode=="missing_header":
        csv_bytes=b"tag-id,animal-taxon\nA,Buteo buteo\n"
    elif mode=="empty_identity":
        csv_bytes=b"animal-id,animal-taxon\n,Buteo buteo\n"
    else:
        csv_bytes=b"animal-id,animal-taxon\nA,Buteo buteo\nA,Circus cyaneus\n"
    with pytest.raises(ValueError,match=match):
        parse_animals(csv_bytes,["animal-id","animal-taxon"])


def test_changed_same_id_taxon_is_not_new_species():
    old,new=_old_and_new()
    new["OLD000"]="Buteo buteo"
    with pytest.raises(ValueError,match="changed species"):
        audit_reference_rosters(old,new,_contract())


def test_missing_recorded_alias_must_not_inflate_new_identity():
    old,new=_old_and_new()
    new.pop("H197221")
    with pytest.raises(ValueError,match="declared ID correction"):
        audit_reference_rosters(old,new,_contract())


def test_contract_cannot_be_redirected_to_gps_data_or_new_version():
    c=_contract()
    c["source_versions"][1]["url"]=(
        "https://zenodo.org/records/17310324/files/BOP_RODENT-gps-2025.csv.gz?download=1"
    )
    with pytest.raises(ValueError,match="exact two frozen reference"):
        contract_from_bytes(json.dumps(c).encode("utf-8"))


def test_reference_filename_rejects_gps_even_if_supplied_to_download_helper():
    c=_contract()
    modified=dict(c["source_versions"][0])
    modified["url"]="https://zenodo.org/records/10055071/files/BOP_RODENT-gps-2020.csv.gz?download=1"
    with pytest.raises(ValueError,match="disallowed GPS"):
        _source_bytes(modified,250000)
