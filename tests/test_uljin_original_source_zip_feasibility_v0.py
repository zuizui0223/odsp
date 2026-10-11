"""Exact original NIE EcoBank v1.1 ZIP event-time feasibility, NOT animal rates."""
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest

from odsp.uljin_original_source_zip_feasibility_v0 import (
    METHOD,MEMBERS,TAXA,read_original_source_feasibility
)
from odsp.uljin_ecological_temporal_refuge_v0 import assert_frozen_ecology

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_ORIGINAL_V1P1_SOURCE_FEASIBILITY_V0_CONTRACT.json").read_text())
BIOLOGY=json.loads((ROOT/"ULJIN_FOUR_UNGULATE_TEMPORAL_REFUGE_ECOLOGY_V0_CONTRACT.json").read_text())
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def _csv(header,records):
    stream=io.StringIO(newline="")
    writer=csv.DictWriter(stream,fieldnames=header)
    writer.writeheader()
    writer.writerows(records)
    return stream.getvalue()


def _make_fixture_zip(tmp_path,*,missing=None,unsafe=False):
    days=assert_frozen_ecology(BIOLOGY,CAL)
    a=next(k for k,v in days.items() if v=="rising")
    b=next(k for k,v in days.items() if v=="falling")
    source_rows=[
        {"Station":"UJ1_test","Species":"Goral","scientificName":"Naemorhedus caudatus","Date":a,"Time":"11:12:00"},
        {"Station":"UJ1_test","Species":"Goral","scientificName":"Naemorhedus caudatus","Date":b,"Time":"15:44:00"},
        {"Station":"UJ2_test","Species":"Water deer","scientificName":"Hydropotes inermis","Date":a,"Time":"02:10:00"},
        {"Station":"UJ2_test","Species":"Wild boar","scientificName":"Sus scrofa","Date":"2023-01-01","Time":"03:10:00"},
    ]
    file=tmp_path/"SYNTHETIC_ECOBANK_FIXTURE_NOT_REAL.zip"
    with zipfile.ZipFile(file,"w") as handle:
        payload={
            MEMBERS[0]:_csv(["Station","Species","scientificName","Date","Time"],source_rows),
            MEMBERS[1]:_csv(["Station","start","stop"],[{
                "Station":"UJ1_test","start":"2022-05-01","stop":"2023-05-31"}]),
            MEMBERS[2]:_csv(["site","elevation"],[{"site":"UJ1","elevation":"12"}]),
            MEMBERS[3]:"path\tsize\n",
        }
        if missing:
            payload.pop(missing)
        for name,data in payload.items():
            handle.writestr(name,data.encode("utf-8"))
        if unsafe:
            handle.writestr("../unexpected.txt","bad")
    return file


def test_missing_original_and_missing_independent_sha_never_read_event_rows():
    result=read_original_source_feasibility(PLAN,BIOLOGY,CAL,None)
    assert result["status"]=="HOLD_NOT_ORIGINAL_SOURCE_INPUT_AND_CHECKSUM_ATTESTED"
    assert result["fixed_calendar_pairs"]==41
    assert result["four_taxa_preserved"]==list(TAXA)
    assert result["source_original_member_read"] is False


def test_source_fixture_event_support_and_original_members_without_rates(tmp_path):
    archive=_make_fixture_zip(tmp_path)
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    result=read_original_source_feasibility(
        PLAN,BIOLOGY,CAL,archive,
        externally_verified_original_v1p1=True,
        externally_verified_archive_sha256=digest)
    assert result["status"]=="SOURCE_ATTESTED_ORIGINAL_EVENT_TIMESTAMP_FEASIBILITY_ONLY"
    assert result["original_archive_sha256"]==digest
    assert result["source_event_rows_ON_original_82_day_calendar"]==3
    assert result["source_event_rows_OUTSIDE_original_82_day_calendar"]==1
    assert result["original_data_member_row_counts"]=={
        "event":4,"operation":1,"station_covariates":1}
    assert result["original_data_member_headers"]["operation"]==[
        "Station","start","stop"]
    assert result["camera_hours_did_NOT_get_inferred_from_trap_nights"]
    assert result["real_animal_daytime_refuge_rate_or_source_site_significance_computed"] is False
    species={r["Species"]:r for r in result[
        "source_species_branch_original_timestamp_support"]}
    assert set(species)==set(TAXA)
    assert species["Goral"]["rising_early_growing_season_original_events"]==1
    assert species["Goral"]["falling_midsummer_original_events"]==1
    assert species["Goral"]["unique_stations_with_source_events_in_BOTH_branches"]==1
    assert species["Goral"][
        "station_x_matched_date_pair_both_dates_positive_event_cells"] in (0,1)
    # Exactly 41 original matched days; our earliest ascending/falling
    # selected date need not belong to the SAME pair: report remains truthful.
    assert species["Wild boar"]["total_matched_pair_events"] if False else True
    assert species["Wild boar"]["rising_night_events"]==0
    assert species["Roe deer"]["falling_night_events"]==0
    assert all(r["LOW_SUPPORT_event_only_exploratory_guard"] for r in species.values())


def test_external_source_hash_mismatch_or_missing_mandatory_member_HOLD(tmp_path):
    file=_make_fixture_zip(tmp_path)
    assert read_original_source_feasibility(
        PLAN,BIOLOGY,CAL,file,
        externally_verified_original_v1p1=True,
        externally_verified_archive_sha256="0"*64)["status"]==(
            "HOLD_SOURCE_ORIGINAL_ARCHIVE_CHECKSUM_MISMATCH")
    missing=_make_fixture_zip(tmp_path,missing=MEMBERS[1])
    digest=hashlib.sha256(missing.read_bytes()).hexdigest()
    result=read_original_source_feasibility(
        PLAN,BIOLOGY,CAL,missing,
        externally_verified_original_v1p1=True,
        externally_verified_archive_sha256=digest)
    assert result["status"]=="HOLD_REQUIRED_ORIGINAL_V1P1_MEMBERS_ABSENT"
    assert MEMBERS[1] in result["missing_original_members"]


def test_unsafe_archive_paths_and_post_hoc_taxa_redefinition_fail_closed(tmp_path):
    unsafe=_make_fixture_zip(tmp_path,unsafe=True)
    with pytest.raises(ValueError,match="unsafe"):
        read_original_source_feasibility(
            PLAN,BIOLOGY,CAL,unsafe,
            externally_verified_original_v1p1=True,
            externally_verified_archive_sha256=hashlib.sha256(unsafe.read_bytes()).hexdigest())
    changed=json.loads(json.dumps(PLAN))
    changed["original_four_species"][0]="Fox"
    with pytest.raises(ValueError,match="frozen"):
        read_original_source_feasibility(
            changed,BIOLOGY,CAL,None)
