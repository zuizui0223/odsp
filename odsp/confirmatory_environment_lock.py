"""Runtime dependency identity lock for confirmatory ODSP implementations.

The source-content lock freezes ODSP's own Python implementation.  This layer
complements it by freezing the interpreter family/version and the installed
third-party distribution versions actually referenced by the canonical
implementation's recursively discovered ODSP source closure.

The v1 lock intentionally does not claim bitwise reproducibility and does not
freeze operating-system, machine, BLAS, compiler, or external-library source
identity.
"""
from __future__ import annotations

import ast
from importlib import metadata
from pathlib import Path
import sys
from typing import Mapping

from .confirmatory_implementation_lock import (
    implementation_source_paths_for_surface,
)


ENVIRONMENT_LOCK_ID = "odsp-confirmatory-runtime-environment-lock-v1"
_REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
_STDLIB_MODULES = frozenset(sys.stdlib_module_names)


def _normalized_distribution_name(value: str) -> str:
    return str(value).strip().lower().replace("_", "-")


def _external_import_modules_for_surface(surface: str) -> tuple[str, ...]:
    modules: set[str] = set()
    for relative in implementation_source_paths_for_surface(surface):
        source = (_REPOSITORY_ROOT / relative).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                top = str(name).split(".", 1)[0]
                if (
                    not top
                    or top == "odsp"
                    or top == "__future__"
                    or top in _STDLIB_MODULES
                ):
                    continue
                modules.add(top)
    return tuple(sorted(modules))


def _distribution_versions_for_modules(
    modules: tuple[str, ...],
) -> tuple[dict[str, str], ...]:
    package_map = metadata.packages_distributions()
    distribution_names: set[str] = set()
    for module in modules:
        candidates = package_map.get(module) or ()
        if not candidates:
            raise ValueError(
                "confirmatory runtime environment cannot map external import "
                f"{module!r} to an installed distribution"
            )
        for candidate in candidates:
            name = str(candidate).strip()
            if not name:
                raise ValueError(
                    "confirmatory runtime environment found an empty distribution "
                    f"name for external import {module!r}"
                )
            distribution_names.add(name)

    rows: list[dict[str, str]] = []
    for distribution in sorted(
        distribution_names,
        key=_normalized_distribution_name,
    ):
        try:
            version = metadata.version(distribution)
        except metadata.PackageNotFoundError as exc:
            raise ValueError(
                "confirmatory runtime environment distribution is not installed: "
                f"{distribution}"
            ) from exc
        normalized = _normalized_distribution_name(distribution)
        if not normalized or not str(version).strip():
            raise ValueError(
                "confirmatory runtime environment distribution identity is invalid"
            )
        rows.append({"name": normalized, "version": str(version).strip()})
    return tuple(rows)


def runtime_environment_snapshot_for_surface(
    surface: str,
) -> dict[str, object]:
    """Return the runtime dependency snapshot for one canonical surface."""

    modules = _external_import_modules_for_surface(surface)
    distributions = _distribution_versions_for_modules(modules)
    return {
        "python": {
            "implementation": str(sys.implementation.name),
            "major": int(sys.version_info.major),
            "minor": int(sys.version_info.minor),
        },
        "external_modules": list(modules),
        "distributions": [dict(row) for row in distributions],
    }


def normalize_runtime_environment_snapshot(raw: object) -> dict[str, object]:
    """Validate a frozen runtime environment snapshot without trusting it."""

    if not isinstance(raw, Mapping):
        raise ValueError(
            "freeze manifest confirmatory_route.runtime_environment_snapshot "
            "must be a JSON object"
        )
    if set(raw) != {"python", "external_modules", "distributions"}:
        raise ValueError(
            "freeze manifest confirmatory_route.runtime_environment_snapshot fields "
            "must be exactly ['distributions', 'external_modules', 'python']"
        )

    python = raw["python"]
    if not isinstance(python, Mapping) or set(python) != {
        "implementation",
        "major",
        "minor",
    }:
        raise ValueError(
            "runtime environment python identity fields must be exactly "
            "['implementation', 'major', 'minor']"
        )
    implementation = python["implementation"]
    if not isinstance(implementation, str) or not implementation.strip():
        raise ValueError("runtime environment python implementation must be text")
    major = python["major"]
    minor = python["minor"]
    if (
        isinstance(major, bool)
        or not isinstance(major, int)
        or major < 1
        or isinstance(minor, bool)
        or not isinstance(minor, int)
        or minor < 0
    ):
        raise ValueError(
            "runtime environment python major/minor versions must be integers"
        )

    modules_raw = raw["external_modules"]
    if not isinstance(modules_raw, list):
        raise ValueError("runtime environment external_modules must be a JSON array")
    modules: list[str] = []
    for index, item in enumerate(modules_raw):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"runtime environment external_modules[{index}] must be text"
            )
        modules.append(item.strip())
    if modules != sorted(modules) or len(modules) != len(set(modules)):
        raise ValueError(
            "runtime environment external_modules must be sorted and unique"
        )

    rows_raw = raw["distributions"]
    if not isinstance(rows_raw, list):
        raise ValueError("runtime environment distributions must be a JSON array")
    rows: list[dict[str, str]] = []
    for index, item in enumerate(rows_raw):
        if not isinstance(item, Mapping) or set(item) != {"name", "version"}:
            raise ValueError(
                f"runtime environment distributions[{index}] must contain name/version"
            )
        name = item["name"]
        version = item["version"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"runtime environment distributions[{index}].name must be text"
            )
        if not isinstance(version, str) or not version.strip():
            raise ValueError(
                f"runtime environment distributions[{index}].version must be text"
            )
        normalized = _normalized_distribution_name(name)
        if name.strip() != normalized:
            raise ValueError(
                "runtime environment distribution names must be lowercase normalized text"
            )
        rows.append({"name": normalized, "version": version.strip()})
    names = [row["name"] for row in rows]
    if names != sorted(names) or len(names) != len(set(names)):
        raise ValueError(
            "runtime environment distributions must be sorted and unique by name"
        )

    return {
        "python": {
            "implementation": implementation.strip(),
            "major": int(major),
            "minor": int(minor),
        },
        "external_modules": modules,
        "distributions": rows,
    }
