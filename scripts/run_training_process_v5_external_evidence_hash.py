"""Print SHA256 for the frozen final training-process v5 external evidence set."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

PLAN=Path("ODSP_TRAINING_PROCESS_V5_EXTERNAL_EVIDENCE_HASH_PLAN.json")

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    plan=json.loads(PLAN.read_text(encoding="utf-8"))
    rows=[]
    for name in plan["artifacts"]:
        p=Path(name)
        if not p.is_file():
            raise FileNotFoundError(p)
        rows.append({"artifact":name,"sha256":sha256(p)})
    payload={
        "schema_version":1,
        "contract_id":plan["contract_id"],
        "route_key":plan["route_key"],
        "artifacts":rows,
    }
    print(json.dumps(payload,sort_keys=True))

if __name__=="__main__":
    main()
