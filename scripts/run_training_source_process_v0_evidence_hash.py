"""Snapshot exact content hashes for the frozen source-v0 evidence plan v3."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

PLAN=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_EVIDENCE_PLAN_V3.json")

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    plan=json.loads(PLAN.read_text(encoding="utf-8"))
    rows=[]
    for name in plan["ordered_evidence_artifacts"]:
        p=Path(name)
        if not p.is_file():
            raise FileNotFoundError(p)
        rows.append({"artifact":name,"sha256":sha256(p)})
    payload={
        "schema_version":1,
        "contract_id":plan["contract_id"],
        "planned_route_key":plan["planned_route_key"],
        "planned_canonical_surface":plan["planned_canonical_surface"],
        "artifacts":rows,
    }
    Path("/tmp/training-source-process-v0-evidence-hashes.json").write_text(
        json.dumps(payload,indent=2,sort_keys=True)+"\n",
        encoding="utf-8",
    )
    print(json.dumps(payload,sort_keys=True))

if __name__=="__main__":
    main()
