"""Source-content identity lock for confirmatory ODSP implementations.

The lock follows the canonical surface's recursive ODSP-internal Python import
closure without importing or executing those modules.  The resulting ordered
source path + SHA256 snapshot is suitable for pre-outcome freezing and exact
runtime comparison.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Iterable


IMPLEMENTATION_LOCK_ID = "odsp-confirmatory-implementation-lock-v1"
_PACKAGE_NAME = "odsp"
_PACKAGE_ROOT = Path(__file__).resolve().parent
_REPOSITORY_ROOT = _PACKAGE_ROOT.parent


def _module_path(module_name: str) -> Path | None:
    if module_name == _PACKAGE_NAME:
        candidate = _PACKAGE_ROOT / "__init__.py"
        return candidate if candidate.is_file() else None
    prefix = _PACKAGE_NAME + "."
    if not module_name.startswith(prefix):
        return None
    parts = module_name[len(prefix) :].split(".")
    file_candidate = _PACKAGE_ROOT.joinpath(*parts).with_suffix(".py")
    if file_candidate.is_file():
        return file_candidate
    package_candidate = _PACKAGE_ROOT.joinpath(*parts) / "__init__.py"
    if package_candidate.is_file():
        return package_candidate
    return None


def _candidate_module(module_name: str) -> str | None:
    return module_name if _module_path(module_name) is not None else None


def _relative_import_base(module_name: str, level: int) -> list[str]:
    parts = module_name.split(".")
    if level < 1 or level >= len(parts):
        raise ValueError(
            f"invalid relative import level {level} in implementation module {module_name}"
        )
    return parts[:-level]


def _odsp_imports(module_name: str, tree: ast.AST) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name == _PACKAGE_NAME or name.startswith(_PACKAGE_NAME + "."):
                    candidate = _candidate_module(name)
                    if candidate is not None:
                        imports.add(candidate)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = _relative_import_base(module_name, node.level)
                if node.module:
                    target = ".".join(base + node.module.split("."))
                    candidate = _candidate_module(target)
                    if candidate is not None:
                        imports.add(candidate)
                else:
                    for alias in node.names:
                        if alias.name == "*":
                            raise ValueError(
                                "wildcard relative import is not allowed in confirmatory "
                                f"implementation closure: {module_name}"
                            )
                        target = ".".join(base + alias.name.split("."))
                        candidate = _candidate_module(target)
                        if candidate is not None:
                            imports.add(candidate)
            elif node.module:
                target = node.module
                if target == _PACKAGE_NAME:
                    for alias in node.names:
                        if alias.name == "*":
                            raise ValueError(
                                "wildcard odsp import is not allowed in confirmatory "
                                f"implementation closure: {module_name}"
                            )
                        candidate = _candidate_module(
                            _PACKAGE_NAME + "." + alias.name
                        )
                        if candidate is not None:
                            imports.add(candidate)
                elif target.startswith(_PACKAGE_NAME + "."):
                    candidate = _candidate_module(target)
                    if candidate is not None:
                        imports.add(candidate)
        elif isinstance(node, ast.Call):
            dynamic = False
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                dynamic = True
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "importlib"
            ):
                dynamic = True
            if dynamic:
                raise ValueError(
                    "dynamic imports are not allowed in confirmatory implementation "
                    f"closure: {module_name}"
                )
    return imports


def _module_name_from_surface(surface: str) -> str:
    value = str(surface).strip()
    if not value or "." not in value:
        raise ValueError("canonical surface must be a fully qualified odsp callable")
    module_name, _callable = value.rsplit(".", 1)
    if not module_name.startswith(_PACKAGE_NAME + "."):
        raise ValueError("canonical surface must resolve inside the odsp package")
    if _module_path(module_name) is None:
        raise ValueError(
            f"canonical surface module does not exist inside odsp: {module_name}"
        )
    return module_name


def implementation_source_paths_for_surface(surface: str) -> tuple[str, ...]:
    """Return the deterministic recursive ODSP source closure for one surface."""

    root = _module_name_from_surface(surface)
    pending = [root]
    seen: set[str] = set()
    paths: set[str] = set()

    while pending:
        module_name = pending.pop()
        if module_name in seen:
            continue
        seen.add(module_name)
        path = _module_path(module_name)
        if path is None:
            raise ValueError(
                f"ODSP implementation dependency could not be resolved: {module_name}"
            )
        try:
            relative = path.resolve().relative_to(_REPOSITORY_ROOT.resolve())
        except ValueError as exc:
            raise ValueError(
                f"ODSP implementation source escaped package root: {path}"
            ) from exc
        relative_text = relative.as_posix()
        if not relative_text.startswith("odsp/"):
            raise ValueError(
                f"ODSP implementation source escaped package root: {relative_text}"
            )
        paths.add(relative_text)

        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=relative_text)
        except SyntaxError as exc:
            raise ValueError(
                f"cannot parse ODSP implementation source: {relative_text}"
            ) from exc
        for dependency in sorted(_odsp_imports(module_name, tree), reverse=True):
            if dependency not in seen:
                pending.append(dependency)

    return tuple(sorted(paths))


def implementation_source_snapshot_for_surface(
    surface: str,
) -> tuple[dict[str, str], ...]:
    """Return ordered source path + SHA256 pairs for one canonical surface."""

    snapshot: list[dict[str, str]] = []
    for relative in implementation_source_paths_for_surface(surface):
        path = _REPOSITORY_ROOT / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        snapshot.append({"path": relative, "sha256": digest})
    if not snapshot:
        raise ValueError("confirmatory implementation source snapshot is empty")
    return tuple(snapshot)
