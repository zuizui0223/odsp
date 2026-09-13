from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_public_package_metadata_is_consistent_at_0_11_0():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "odsp-niche-geometry"' in pyproject
    assert 'version = "0.11.0"' in pyproject
    assert 'readme = "PYPI_README.md"' in pyproject
    assert 'odsp = "odsp.cli:main"' in pyproject
    assert 'release = ["build>=1.2", "twine>=6"]' in pyproject

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert "version: 0.11.0" in citation
    assert "license: MIT" in citation

    zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert zenodo["upload_type"] == "software"
    assert zenodo["version"] == "0.11.0"
    assert zenodo["license"] == "MIT"


def test_pypi_landing_page_exposes_install_scope_and_contract_path():
    text = (ROOT / "PYPI_README.md").read_text(encoding="utf-8")
    assert 'pip install "odsp-niche-geometry[predict]"' in text
    assert "odsp run --contract endpoint.json" in text
    assert "random forest" in text
    assert "multinomial logistic regression" in text
    assert "not** a replacement" in text
    assert "using_odsp_from_r.md" in text


def test_r_guide_uses_reticulate_and_same_contract_runner():
    text = (ROOT / "docs" / "using_odsp_from_r.md").read_text(encoding="utf-8")
    assert 'virtualenv_create("r-odsp")' in text
    assert '"odsp-niche-geometry[predict]"' in text
    assert 'import("odsp.cli"' in text
    assert '"--contract"' in text
    assert "receipt$result$gain_category" in text
    assert "random_forest" in text
    assert "multinomial_logit" in text


def test_release_workflow_uses_oidc_and_supports_one_click_dispatch():
    text = (ROOT / ".github" / "workflows" / "publish-pypi.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch:" in text
    assert "default: '0.11.0'" in text
    assert "id-token: write" in text
    assert "pypa/gh-action-pypi-publish@release/v1" in text
    assert "name: pypi" in text
    assert "needs: [build, publish]" in text
    assert "gh release create" in text
    assert "--verify-tag" in text
    assert "--target \"${GITHUB_SHA}\"" in text
    assert "requested version" in text


def test_package_build_workflow_tests_built_wheel_not_only_editable_checkout():
    text = (ROOT / ".github" / "workflows" / "package-build.yml").read_text(
        encoding="utf-8"
    )
    assert "python -m build" in text
    assert "python -m twine check dist/*" in text
    assert "python -m venv /tmp/odsp-wheel" in text
    assert "pip install dist/*.whl" in text
    assert "/tmp/odsp-wheel/bin/odsp --help" in text
    assert re.search(r"version\('odsp-niche-geometry'\).*0\.11\.0", text)
