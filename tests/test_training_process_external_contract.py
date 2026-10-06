from __future__ import annotations

import json
from pathlib import Path

import pytest

import odsp.training_process_external_contract as contract


def _write_contract(tmp_path: Path) -> Path:
    (tmp_path / "external-roster.csv").write_text(
        "row_id,group_id,block_id,sample_weight\n"
        "v1,g1,b1,1\n"
        "v2,g1,b2,2\n",
        encoding="utf-8",
    )
    (tmp_path / "freeze-manifest.json").write_text(
        json.dumps({"refit_ids": ["r02", "r01"]}),
        encoding="utf-8",
    )
    payload = {
        "schema_version": 1,
        "external_freeze_manifest_path": "freeze-manifest.json",
        "external_freeze_receipt_path": "freeze-receipt.json",
        "managed_scoring_receipt_path": "scoring-receipt.json",
        "score_bundle_path": "score-bundle.json",
        "validation_data_path": "external-data.csv",
        "external_roster": {
            "path": "external-roster.csv",
            "format": "csv",
        },
        "training_process_manifest_path": "process-manifest.json",
        "managed_generation_receipt_path": "generation-receipt.json",
        "training_roster_path": "training-roster.csv",
        "external_outcomes_first_accessed_at_utc": "2026-10-06T00:00:00Z",
    }
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_external_contract_reconstructs_frozen_design_and_refits(tmp_path, monkeypatch):
    path = _write_contract(tmp_path)
    captured = {}

    class Result:
        def as_dict(self):
            return {"receipt_type": "fake"}

    def fake_endpoint(
        freeze_manifest,
        freeze_receipt,
        scoring_receipt,
        bundle,
        validation_data,
        groups,
        **kwargs,
    ):
        captured.update(
            {
                "freeze_manifest": freeze_manifest,
                "freeze_receipt": freeze_receipt,
                "scoring_receipt": scoring_receipt,
                "bundle": bundle,
                "validation_data": validation_data,
                "groups": groups,
                **kwargs,
            }
        )
        return Result()

    monkeypatch.setattr(
        contract,
        "run_untouched_external_training_process_v5",
        fake_endpoint,
    )
    result = contract.run_training_process_v5_external_contract(path)

    assert result == {"receipt_type": "fake"}
    assert captured["groups"] == ("g1", "g1")
    assert captured["blocks"] == ("b1", "b2")
    assert captured["validation_row_ids"] == ("v1", "v2")
    assert captured["sample_weight"] == (1.0, 2.0)
    assert captured["refit_ids"] == ("r02", "r01")
    assert captured["external_outcomes_first_accessed_at_utc"] == (
        "2026-10-06T00:00:00Z"
    )
    assert captured["freeze_manifest"] == tmp_path / "freeze-manifest.json"
    assert captured["training_roster_path"] == tmp_path / "training-roster.csv"


def test_external_contract_rejects_unknown_fields(tmp_path):
    path = _write_contract(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["score_tensor"] = "caller-supplied.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown"):
        contract.run_training_process_v5_external_contract(path)


def test_external_contract_rejects_duplicate_frozen_refit_ids(tmp_path):
    path = _write_contract(tmp_path)
    manifest = tmp_path / "freeze-manifest.json"
    manifest.write_text(
        json.dumps({"refit_ids": ["r01", "r01"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unique"):
        contract.run_training_process_v5_external_contract(path)
