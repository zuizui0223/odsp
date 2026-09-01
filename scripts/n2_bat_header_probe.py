#!/usr/bin/env python3
"""Print headers only from the checksum-pinned bat tracking CSV."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from n2_bat_repository_preflight import (
    MANIFEST,
    _by_role,
    canonical_name,
    download,
    verify_source,
)


def main() -> int:
    manifest = json.loads(Path(MANIFEST).read_text(encoding="utf-8"))
    spec = _by_role(manifest, "primary_tracking_event_stream")
    data = download(str(spec["content_url"]))
    verify_source(data, spec)
    reader = csv.reader(io.StringIO(data.decode("utf-8-sig")))
    header = next(reader)
    print(json.dumps({
        "filename": spec["filename"],
        "canonical_headers": [canonical_name(str(x)) for x in header],
        "rows_read": 0,
        "numeric_height_values_parsed": False,
        "outcome_metrics_computed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
