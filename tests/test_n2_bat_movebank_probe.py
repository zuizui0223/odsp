from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "n2_bat_movebank_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("n2_bat_movebank_probe", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _csv(header, rows):
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(str(row.get(column, "")) for column in header))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _fake_event_bytes():
    header = [
        "timestamp",
        "location_lat",
        "location_long",
        "individual_local_identifier",
        "individual_id",
        "visible",
        "height_above_mean_sea_level",
    ]
    rows = []
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    for bat in range(8):
        step = 0
        for cell in range(5):
            for replicate in range(5):
                rows.append(
                    {
                        "timestamp": (start + timedelta(seconds=30 * step)).isoformat(),
                        "location_lat": "0.0",
                        "location_long": str(cell * 0.05 + bat * 0.00001),
                        "individual_local_identifier": f"bat-{bat}",
                        "individual_id": str(1000 + bat),
                        "visible": "true",
                        # Values are deliberately unique and conspicuous. The
                        # report must never expose or summarize them.
                        "height_above_mean_sea_level": str(777000000 + bat * 1000 + replicate),
                    }
                )
                step += 1
    return _csv(header, rows)


def test_mocked_live_report_never_exposes_height_values(monkeypatch):
    probe = _load_probe()
    study = _csv(
        ["id", "name", "license_type", "number_of_individuals", "number_of_deployed_locations", "sensor_type_ids"],
        [
            {
                "id": "312057662",
                "name": "mock bat study",
                "license_type": "CC_0",
                "number_of_individuals": "8",
                "number_of_deployed_locations": "200",
                "sensor_type_ids": "653",
            }
        ],
    )
    attributes = _csv(
        ["study_id", "sensor_type_id", "short_name", "data_type"],
        [
            {
                "study_id": "312057662",
                "sensor_type_id": "653",
                "short_name": "height_above_mean_sea_level",
                "data_type": "decimal",
            }
        ],
    )
    events = _fake_event_bytes()

    def fake_fetch(params):
        entity_type = params["entity_type"]
        if entity_type == "study":
            return study
        if entity_type == "study_attribute":
            return attributes
        if entity_type == "event":
            return events
        raise AssertionError(entity_type)

    monkeypatch.setattr(probe, "fetch_movebank", fake_fetch)
    monkeypatch.setattr(
        probe,
        "make_projector",
        lambda: (lambda lon, lat: (lon * 100000.0, lat * 100000.0)),
    )
    report = probe.build_report()

    assert report["outcome_metrics_computed"] is False
    assert report["scientific_terminal_decision"] is True
    assert report["terminal_category"] == "structurally_available"
    assert report["raw_event_values_persisted"] is False
    serialized = json.dumps(report, sort_keys=True)
    assert "777000000" not in serialized
    assert "777001000" not in serialized
    assert "height_min" not in serialized
    assert "height_max" not in serialized
    assert "height_mean" not in serialized
    assert "height_quantile" not in serialized


def test_transport_failure_is_explicitly_non_scientific(monkeypatch, tmp_path, capsys):
    probe = _load_probe()

    def fail():
        raise probe.TransportError("movebank_http_status_401")

    monkeypatch.setattr(probe, "build_report", fail)
    monkeypatch.setattr(
        sys,
        "argv",
        [str(SCRIPT_PATH), "--output", str(tmp_path / "receipt.json")],
    )
    exit_code = probe.main()
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload == {
        "outcome_metrics_computed": False,
        "reason": "movebank_http_status_401",
        "scientific_terminal_decision": False,
        "transport_probe": "unresolved",
    }
    assert not (tmp_path / "receipt.json").exists()


def test_html_license_response_is_classified_as_transport(monkeypatch):
    probe = _load_probe()

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"<html><body>License Terms: accept first</body></html>"

    monkeypatch.setattr(probe.urllib.request, "urlopen", lambda *args, **kwargs: Response())
    with pytest.raises(probe.TransportError, match="license_or_html"):
        probe.fetch_movebank({"entity_type": "event", "study_id": 312057662})


def test_report_keeps_forbidden_metric_names_only_as_boundary_declaration(monkeypatch):
    probe = _load_probe()
    payload = probe.unresolved_transport_payload("movebank_network_error")
    assert payload["outcome_metrics_computed"] is False
    assert payload["scientific_terminal_decision"] is False
    assert "terminal_category" not in payload
