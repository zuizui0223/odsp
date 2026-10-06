from __future__ import annotations

import json
from pathlib import Path

import odsp.cli as cli


def test_training_process_freeze_routes_existing_manifest_builder(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "create_training_process_freeze_manifest",
        lambda plan, manifest: {
            "runner": "process-freeze",
            "plan": str(plan),
            "manifest": str(manifest),
        },
    )
    code = cli.main(
        [
            "experimental",
            "training-process",
            "freeze",
            "--plan",
            "process-plan.json",
            "--manifest-out",
            "process-freeze.json",
            "--out",
            "-",
        ]
    )
    assert code == 0
    assert json.loads(capsys.readouterr().out)["runner"] == "process-freeze"


def test_training_process_generate_routes_managed_execution(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "run_managed_training_process_generation",
        lambda plan, root, receipt: {
            "runner": "managed-generate",
            "plan": str(plan),
            "root": str(root),
            "receipt": str(receipt),
        },
    )
    code = cli.main(
        [
            "experimental",
            "training-process",
            "generate",
            "--plan",
            "managed-plan.json",
            "--output-root",
            "generated",
            "--receipt-out",
            "generation-receipt.json",
            "--out",
            "-",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "plan": "managed-plan.json",
        "receipt": "generation-receipt.json",
        "root": "generated",
        "runner": "managed-generate",
    }


def test_training_process_external_freeze_routes_process_specific_builder(
    monkeypatch, capsys
):
    monkeypatch.setattr(
        cli,
        "create_training_process_v5_external_freeze",
        lambda plan, manifest, receipt: {
            "runner": "process-external-freeze",
            "plan": str(plan),
            "manifest": str(manifest),
            "receipt": str(receipt),
        },
    )
    code = cli.main(
        [
            "experimental",
            "training-process",
            "external-freeze",
            "--plan",
            "external-plan.json",
            "--manifest-out",
            "external-freeze.json",
            "--receipt-out",
            "external-freeze-receipt.json",
            "--out",
            "-",
        ]
    )
    assert code == 0
    assert json.loads(capsys.readouterr().out)["runner"] == (
        "process-external-freeze"
    )


def test_training_process_external_score_routes_managed_scoring(monkeypatch, capsys):
    captured = {}

    def fake_score(manifest, receipt, roster, **kwargs):
        captured.update(
            {
                "manifest": str(manifest),
                "receipt": str(receipt),
                "roster": str(roster),
                **{key: str(value) for key, value in kwargs.items()},
            }
        )
        return {"runner": "managed-score"}

    monkeypatch.setattr(cli, "run_managed_external_scoring_v1", fake_score)
    code = cli.main(
        [
            "experimental",
            "training-process",
            "external-score",
            "--freeze-manifest",
            "freeze.json",
            "--freeze-receipt",
            "freeze-receipt.json",
            "--external-roster",
            "external-roster.csv",
            "--external-roster-format",
            "csv",
            "--managed-generation-receipt",
            "generation.json",
            "--generated-model-root",
            "models",
            "--validation-data",
            "external.csv",
            "--output-root",
            "scores",
            "--score-bundle-out",
            "score-bundle.json",
            "--scoring-receipt-out",
            "scoring-receipt.json",
            "--out",
            "-",
        ]
    )
    assert code == 0
    assert json.loads(capsys.readouterr().out)["runner"] == "managed-score"
    assert captured["external_roster_format"] == "csv"
    assert captured["managed_generation_receipt_path"] == "generation.json"
    assert captured["generated_model_root"] == "models"
    assert captured["validation_data_path"] == "external.csv"
    assert captured["score_bundle_out"] == "score-bundle.json"


def test_training_process_external_run_uses_contract_wrapper(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "run_training_process_v5_external_contract",
        lambda path: {"runner": "process-external-run", "contract": str(path)},
    )
    code = cli.main(
        [
            "experimental",
            "training-process",
            "external-run",
            "--contract",
            "external-run.json",
            "--out",
            "-",
        ]
    )
    assert code == 0
    assert json.loads(capsys.readouterr().out) == {
        "contract": "external-run.json",
        "runner": "process-external-run",
    }


def test_training_process_cli_does_not_add_new_top_level_command():
    help_text = cli.build_parser().format_help()
    assert "{run,transfer,experimental}" in help_text
    assert "training-process" not in help_text

    experimental = cli.build_parser().parse_args(
        [
            "experimental",
            "training-process",
            "external-run",
            "--contract",
            "x.json",
        ]
    )
    assert experimental.command == "experimental"
    assert experimental.experimental_command == "training-process"
    assert experimental.training_process_command == "external-run"
