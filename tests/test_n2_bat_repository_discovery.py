import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "n2_bat_repository_discovery.py"


def _load_discovery():
    spec = importlib.util.spec_from_file_location(
        "n2_bat_repository_discovery", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dspace_landing_discovers_mets_without_tracking_values(monkeypatch):
    discovery = _load_discovery()

    class Headers:
        def get(self, key, default=""):
            return "text/html; charset=utf-8" if key == "Content-Type" else default

    class Response:
        headers = Headers()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def geturl(self):
            return "https://www.datarepository.movebank.org/handle/10255/move.2048"

        def read(self, limit=-1):
            return b'''<!doctype html><html><body>
            <a href="/bitstream/handle/10255/move.2049/README.txt?sequence=1">README</a>
            <a href="/bitstream/handle/10255/move.2050/bat-gps.csv?sequence=1">data</a>
            </body></html>'''

    monkeypatch.setattr(discovery, "_request", lambda url: Response())
    payload = discovery.discover()
    assert payload["discovery_status"] == "resolved_landing"
    assert payload["mets_candidate_url"] == (
        "https://www.datarepository.movebank.org/metadata/handle/10255/"
        "move.2048/mets.xml"
    )
    assert len(payload["repository_links"]) == 2
    assert payload["tracking_values_downloaded"] is False
    assert payload["scientific_terminal_decision"] is False
    assert payload["outcome_metrics_computed"] is False
    serialized = json.dumps(payload, sort_keys=True)
    assert "height_distribution" not in serialized
    assert "H(Z|X,Y)" not in serialized


def test_non_dspace_landing_remains_metadata_only(monkeypatch):
    discovery = _load_discovery()

    class Headers:
        def get(self, key, default=""):
            return "text/html" if key == "Content-Type" else default

    class Response:
        headers = Headers()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def geturl(self):
            return "https://example.org/dataset/52nn82r9"

        def read(self, limit=-1):
            return b"<html><body><a href='/unrelated'>x</a></body></html>"

    monkeypatch.setattr(discovery, "_request", lambda url: Response())
    payload = discovery.discover()
    assert payload["discovery_status"] == "resolved_landing"
    assert payload["mets_candidate_url"] is None
    assert payload["repository_links"] == []
    assert payload["tracking_values_downloaded"] is False
