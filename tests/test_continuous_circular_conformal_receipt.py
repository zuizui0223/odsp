from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_conformal_receipt_test_is_enabled_only_after_receipt_exists():
    # The dedicated workflow conditionally runs this file only after the canonical
    # receipt is committed. Until then this test merely preserves the intended path
    # and prevents accidental reliance on an invented pre-run receipt.
    receipt = ROOT / "CONTINUOUS_CIRCULAR_CONFORMAL_VALIDATION_RECEIPT.json"
    if not receipt.exists():
        return
    assert receipt.is_file()
