from pathlib import Path
import json

from audit_cross_taxon_metadata import GPS_REQUIRED, audit


def test_only_metadata_is_opened(tmp_path: Path):
    package = {
        "id": "example",
        "resources": [
            {"name": "gps-2017", "schema": {
                "fields": [{"name": name} for name in sorted(GPS_REQUIRED)]
            }}
        ],
    }
    (tmp_path / "datapackage.json").write_text(json.dumps(package))
    (tmp_path / "reference.csv").write_text(
        "animal-id,animal-taxon,deploy-on-date\n"
        "a,Larus fuscus,2017-05-24\n"
        "b,Larus fuscus,2018-05-24\n"
        "a,Larus fuscus,2019-05-24\n"
    )
    result = audit(tmp_path / "datapackage.json", tmp_path / "reference.csv")
    assert result["reference_rows"] == 3
    assert result["distinct_animal_ids"] == 2
    assert result["schema_candidate"] is True
    assert result["independent_sessions_tested"] is False
    assert result["animal_vertical_values_opened"] is False
    assert result["ecological_outcomes_computed"] is False


def test_schema_missing_height_not_candidate(tmp_path: Path):
    package = {
        "resources": [{"name": "gps-2017", "schema": {
            "fields": [{"name": name} for name in sorted(GPS_REQUIRED - {"height-above-msl"})]
        }}]
    }
    (tmp_path / "datapackage.json").write_text(json.dumps(package))
    (tmp_path / "reference.csv").write_text(
        "animal-id,animal-taxon,deploy-on-date\na,Larus fuscus,2017-05-24\n"
    )
    assert audit(tmp_path / "datapackage.json", tmp_path / "reference.csv")["schema_candidate"] is False
