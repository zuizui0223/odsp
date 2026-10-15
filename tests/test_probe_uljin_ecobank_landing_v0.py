"""No source download/biology: test exact authority and sanitized metadata semantics."""
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "probe_uljin_ecobank_landing_v0.py"
spec = importlib.util.spec_from_file_location("uljin_official_metadata_probe", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_official_html_does_not_claim_zip_bytes():
    html = (
        '<html><a href="/rdm/fileDownload.do?path=someToken" '
        'onclick="fileDownload(9876, \'ephemeral-token\')">'
        'Uljin_camera_trap_ungulates_public_dataset_v1.1_20260305_EcoBank_revised.zip'
        '</a><td>1.1</td></html>'
    ).encode()
    output = module.inspect_page_bytes(html, final_url=module.URL)
    assert output["status"] == "OFFICIAL_LANDING_ZIP_LISTED_BYTES_NOT_DOWNLOADED"
    assert output["portal_version_history_mentions_v1p1"]
    assert not output["original_zip_bytes_read"]
    assert not output["independent_sha256_attested"]
    assert "ephemeral-token" not in str(output)
    assert "someToken" not in str(output)
    assert output["download_controls_redacted"]


def test_off_host_redirect_fails_closed():
    assert module.inspect_page_bytes(b"irrelevant", final_url="https://example.com/a")["status"] == "HOLD_NON_OFFICIAL_FINAL_URL"


def test_no_filename_stays_hold():
    assert module.inspect_page_bytes(b"<html><p>NO FILE HERE</p></html>", final_url=module.URL)["status"] == "HOLD_OFFICIAL_LANDING_ZIP_NAME_NOT_FOUND"
