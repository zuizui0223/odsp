#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from odsp.evaluation_access_provenance_benchmark import run_evaluation_access_provenance_benchmark


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--output", type=Path, required=True); a = p.parse_args()
    r = run_evaluation_access_provenance_benchmark()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(r, sort_keys=True))
    if not r["passed"]:
        raise SystemExit(1)


if __name__ == "__main__": main()
