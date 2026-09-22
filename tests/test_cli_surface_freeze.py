from __future__ import annotations

import json

import odsp.cli as cli


def test_public_help_surface_is_run_transfer_experimental_only():
    help_text = cli.build_parser().format_help()

    assert "{run,transfer,experimental}" in help_text
    assert "fit a bundled reference learner" in help_text
    assert "audit externally generated held-out score columns" in help_text
    assert "advanced governance and pre-outcome freeze operations" in help_text

    for legacy in (
        "transfer-refits",
        "method-route",
        "freeze-refits-external",
        "transfer-refits-external",
        "freeze-refits-external-paired",
        "transfer-refits-external-paired",
        "freeze-refits-external-paired-lattice",
        "transfer-refits-external-paired-lattice",
    ):
        assert legacy not in help_text


def test_transfer_variant_routes_refits_without_new_top_level_command(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "run_refit_information_transfer_contract",
        lambda path: {"runner": "refits", "contract": str(path)},
    )

    code = cli.main(
        [
            "transfer",
            "--variant",
            "refits",
            "--contract",
            "endpoint.json",
            "--out",
            "-",
        ]
    )

    assert code == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt == {"contract": "endpoint.json", "runner": "refits"}


def test_transfer_variant_routes_paired_lattice_without_new_top_level_command(
    monkeypatch, capsys
):
    monkeypatch.setattr(
        cli,
        "run_untouched_external_paired_all_refit_lattice_contract_v4",
        lambda path: {"runner": "paired-lattice", "contract": str(path)},
    )

    code = cli.main(
        [
            "transfer",
            "--variant",
            "external-paired-lattice",
            "--contract",
            "endpoint.json",
            "--out",
            "-",
        ]
    )

    assert code == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["runner"] == "paired-lattice"


def test_experimental_freeze_routes_existing_manifest_builder(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "create_paired_external_lattice_freeze_manifest",
        lambda plan, manifest: {
            "runner": "freeze-paired-lattice",
            "plan": str(plan),
            "manifest": str(manifest),
        },
    )

    code = cli.main(
        [
            "experimental",
            "freeze",
            "--variant",
            "paired-lattice",
            "--plan",
            "plan.json",
            "--manifest-out",
            "freeze.json",
            "--out",
            "-",
        ]
    )

    assert code == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["runner"] == "freeze-paired-lattice"


def test_legacy_command_spelling_remains_executable(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "run_refit_information_transfer_contract",
        lambda path: {"runner": "legacy-refits", "contract": str(path)},
    )

    code = cli.main(
        [
            "transfer-refits",
            "--contract",
            "endpoint.json",
            "--out",
            "-",
        ]
    )

    assert code == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["runner"] == "legacy-refits"
