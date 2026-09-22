#!/usr/bin/env python3
"""Render the validated N2 MEE v6 manuscript to anonymous review DOCX."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.render_n2_mee_review_docx_v4 import render as render_v4


def render(markdown: Path, output: Path, manifest: Path | None = None) -> dict[str, object]:
    result = dict(render_v4(markdown, output, None))
    result["role"] = "n2_mee_anonymous_review_docx_v6"
    result["source_version"] = 6
    result["renderer_implementation"] = "scripts/render_n2_mee_review_docx_v4.py"
    result["v4_visual_qa_inherited"] = False
    result["exact_upload_visual_approval_completed"] = False
    if manifest is not None:
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    print(json.dumps(render(args.input, args.output, args.manifest), sort_keys=True))


if __name__ == "__main__":
    main()
