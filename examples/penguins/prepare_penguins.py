#!/usr/bin/env python3
"""Prepare a pinned complete-case Palmer Penguins table for the ODSP vignette."""
import csv
from pathlib import Path
from urllib.request import urlopen

SOURCE = "https://raw.githubusercontent.com/allisonhorst/palmerpenguins/8957207b78d6ccd1b4654a9dd9c9041b657478ab/inst/extdata/penguins.csv"
OUT = Path(__file__).with_name("penguins_complete.csv")
FEATURES = ("bill_length_mm", "bill_depth_mm", "flipper_length_mm", "body_mass_g")


def main():
    text = urlopen(SOURCE, timeout=30).read().decode("utf-8")
    rows = list(csv.DictReader(text.splitlines()))
    kept = []
    for i, row in enumerate(rows):
        if row["sex"] in {"male", "female"} and all(row[x] not in {"", "NA"} for x in FEATURES):
            kept.append({"row_id": f"penguin-{i:03d}", **{k: row[k] for k in ("island", "sex", "year", *FEATURES)}})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=kept[0].keys())
        writer.writeheader(); writer.writerows(kept)
    print(f"wrote {len(kept)} complete cases to {OUT}")


if __name__ == "__main__":
    main()
