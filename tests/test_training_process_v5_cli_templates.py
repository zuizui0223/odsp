from __future__ import annotations

import json
from pathlib import Path

from odsp.training_process_external_contract import _validate_contract
from odsp.training_process_external_freeze_v1 import _normalize_plan
from odsp.training_process_freeze_manifest import validate_training_process_freeze_plan
from odsp.training_process_managed_generation import validate_managed_generation_plan


ROOT = Path("examples/training_process_v5")


def _load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_training_process_template_matches_freeze_schema():
    plan = validate_training_process_freeze_plan(
        _load("training-process-plan.template.json")
    )
    assert plan["training_process_id"] == "my-training-process-v1"
    assert len(plan["refit_ids"]) == 8


def test_managed_generation_template_matches_schema():
    plan = validate_managed_generation_plan(
        _load("managed-generation-plan.template.json")
    )
    assert plan["training_process_id"] == "my-training-process-v1"
    assert "{membership_path}" in "\n".join(plan["command"])


def test_external_freeze_template_matches_schema():
    plan = _normalize_plan(_load("external-freeze-plan.template.json"))
    assert plan["external_dataset_id"] == "my-untouched-external-v1"
    assert len(plan["levels"]) == 3
    assert plan["certification"]["minimum_refits"] == 8
    assert plan["certification"]["minimum_blocks_per_group"] == 8


def test_external_run_template_matches_contract_schema():
    contract = _validate_contract(_load("external-run.template.json"))
    assert contract["external_roster"]["format"] == "csv"
    assert contract["external_outcomes_first_accessed_at_utc"].endswith("Z")
