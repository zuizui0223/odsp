"""The public repository inventory must remain complete and metadata-only."""

import copy
import json

import pytest

from scripts.collect_movebank_seasonal_catalog import (
    COLLECTION_UUID,
    build_catalog,
    fetch_pages,
    read_raw_archive,
    write_raw_archive,
)


def page(number=0, total_pages=1, total_elements=1, item_uuid="item-1"):
    return {
        "scope": COLLECTION_UUID,
        "_embedded": {
            "searchResult": {
                "page": {
                    "number": number,
                    "size": 25,
                    "totalPages": total_pages,
                    "totalElements": total_elements,
                },
                "_embedded": {
                    "objects": [
                        {
                            "_embedded": {
                                "indexableObject": {
                                    "uuid": item_uuid,
                                    "id": item_uuid,
                                    "name": "A tracked taxon",
                                    "handle": "10255/example",
                                    "entityType": "Datapackage",
                                    "inArchive": True,
                                    "discoverable": True,
                                    "withdrawn": False,
                                    "lastModified": "2026-01-01T00:00:00Z",
                                    "metadata": {
                                        "dc.identifier.doi": [
                                            {"value": "doi:10.5441/a"},
                                            {"value": "doi:10.5441/b"},
                                        ],
                                        "dc.rights": [
                                            {"value": "CC0 1.0 Universal"},
                                            {"value": "Attribution 4.0 International"},
                                        ],
                                        "dc.rights.uri": [
                                            {"value": "https://creativecommons.org/publicdomain/zero/1.0/"},
                                            {"value": "https://creativecommons.org/licenses/by/4.0/"},
                                        ],
                                        "dc.date.issued": [{"value": "2026-01-01"}],
                                        "dc.date.accessioned": [{"value": "2026-02-01T00:00:00Z"}],
                                        "dc.type": [{"value": "Article"}],
                                        "dwc.ScientificName": [{"value": "Taxon one"}],
                                        "sensor.name": [{"value": "GPS"}],
                                        "mdr.animal.count": [{"value": "20"}],
                                        "mdr.location.count": [{"value": "1000"}],
                                        "mdr.study.id": [{"value": "123"}],
                                    },
                                }
                            }
                        }
                    ]
                },
            }
        },
    }


def encoded(*pages):
    return [json.dumps(p).encode("utf-8") for p in pages]


def two_valid_pages():
    first = page(number=0, total_pages=2, total_elements=26, item_uuid="one-0")
    objects = first["_embedded"]["searchResult"]["_embedded"]["objects"]
    template = objects[0]
    for n in range(1, 25):
        hit = copy.deepcopy(template)
        item = hit["_embedded"]["indexableObject"]
        item["uuid"] = item["id"] = f"one-{n}"
        objects.append(hit)
    second = page(number=1, total_pages=2, total_elements=26, item_uuid="two")
    return first, second


def test_preserves_multiple_licenses_dois_and_publication_dates():
    catalog, manifest = build_catalog(encoded(page()), snapshot_date="2026-10-19")
    row = catalog["packages"][0]
    assert row["dois"] == ["doi:10.5441/a", "doi:10.5441/b"]
    assert row["licenses"] == ["CC0 1.0 Universal", "Attribution 4.0 International"]
    assert len(row["license_uris"]) == 2
    assert row["publication_dates"] == ["2026-01-01"]
    assert row["repository_accession_dates"] == ["2026-02-01T00:00:00Z"]
    assert "observation_start" not in row
    assert row["reported_animal_count"] == 20
    assert catalog["metadata_semantics"]["reported_animal_count"] != "unique animals"
    assert catalog["package_count"] == 1  # dc.type=Article is still a Datapackage entity
    assert manifest["unique_package_uuids"] == 1
    assert manifest["snapshot_date"] == "2026-10-19"
    assert manifest["source_query_template"].endswith("&size=25&page={page}")
    assert manifest["biological_outcomes_computed"] is False


@pytest.mark.parametrize("corruption, message", [
    ("missing_page", "Missing discovery page"),
    ("duplicate_page", "Duplicate or out-of-order page index"),
    ("changed_total", "Changing totals"),
    ("wrong_scope", "Wrong collection scope"),
    ("wrong_entity", "Unexpected entity type"),
    ("duplicate_uuid", "Duplicate or inconsistent package UUID"),
])
def test_rejects_incomplete_or_inconsistent_discovery_pages(corruption, message):
    pages = list(two_valid_pages())
    assert build_catalog(encoded(*pages))[0]["package_count"] == 26
    if corruption == "missing_page":
        pages = pages[:1]
    elif corruption == "duplicate_page":
        pages[1]["_embedded"]["searchResult"]["page"]["number"] = 0
    elif corruption == "changed_total":
        pages[1]["_embedded"]["searchResult"]["page"]["totalElements"] = 27
    elif corruption == "wrong_scope":
        pages[1]["scope"] = "another-collection"
    elif corruption == "wrong_entity":
        pages[1]["_embedded"]["searchResult"]["_embedded"]["objects"][0]["_embedded"]["indexableObject"]["entityType"] = "Datafile"
    elif corruption == "duplicate_uuid":
        item = pages[1]["_embedded"]["searchResult"]["_embedded"]["objects"][0]["_embedded"]["indexableObject"]
        item["uuid"] = item["id"] = "one-0"
    with pytest.raises(ValueError, match=message):
        build_catalog(encoded(*pages))


def test_deterministic_archive_replays_original_page_bytes(tmp_path):
    raw = encoded(page())
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"
    write_raw_archive(raw, first)
    write_raw_archive(raw, second)
    assert first.read_bytes() == second.read_bytes()
    assert read_raw_archive(first) == raw
    assert build_catalog(read_raw_archive(first))[0] == build_catalog(raw)[0]


def test_fetch_visits_every_reported_page_in_order(monkeypatch):
    expected = encoded(*two_valid_pages())
    requests = []

    class Response:
        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return self.body

    def open_url(request, timeout):
        requests.append((request.full_url, timeout))
        return Response(expected[len(requests) - 1])

    monkeypatch.setattr("urllib.request.urlopen", open_url)
    assert fetch_pages(timeout=5) == expected
    assert [url.rsplit("page=", 1)[1] for url, _ in requests] == ["0", "1"]
