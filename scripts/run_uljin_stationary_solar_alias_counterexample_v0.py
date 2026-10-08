#!/usr/bin/env python3
"""First reproducible SOURCE-FREE solar aliasing counterexample receipt."""
import hashlib
import json
from pathlib import Path

from odsp.uljin_stationary_solar_alias_counterexample_v0 import (
    stationary_solar_aliasing_control,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "ULJIN_STATIONARY_SOLAR_ALIAS_NEGATIVE_CONTROL_V0_CONTRACT.json"
OUTPUT = ROOT / "ULJIN_STATIONARY_SOLAR_ALIAS_NEGATIVE_CONTROL_V0_FIRST_RECEIPT.json"


def main() -> int:
    source = CONTRACT.read_bytes()
    frozen = json.loads(source)
    if (
        frozen.get("contract_id") != "uljin_stationary_solar_alias_counterexample_v0"
        or frozen.get("stage") != "FROZEN_SOURCE_FREE_BEFORE_FIRST_NEGATIVE_CONTROL_RESULT"
        or frozen.get("original_mirror_pair") != ["2022-05-01", "2022-08-13"]
        or frozen.get("source_event_access_permitted") is not False
    ):
        raise ValueError("independent source-free negative-control contract changed")
    out = stationary_solar_aliasing_control()
    out["contract_sha256"] = hashlib.sha256(source).hexdigest()
    if (
        out["oracle_clock_bin_shape_logscore_advantage"] <= 0
        or abs(out["oracle_solar_bin_shape_logscore_advantage"]) > 1e-10
    ):
        raise ValueError("negative-control gate failed")
    OUTPUT.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "status": out["status"],
        "civil_clock_oracle_gain": out["oracle_clock_bin_shape_logscore_advantage"],
        "solar_phase_oracle_gain": out["oracle_solar_bin_shape_logscore_advantage"],
        "animal_and_operation_rows_accessed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
