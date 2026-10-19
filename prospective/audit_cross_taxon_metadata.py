#!/usr/bin/env python3
"""Pre-outcome metadata screening for cross-taxon ecological comparisons.

Reads only Frictionless datapackage schema and a reference-data CSV. It never
reads GPS heights, diving depths, or ecological outcome statistics. A schema
candidate is NOT an admitted individual-session panel.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

GPS_REQUIRED = {
    "timestamp",
    "location-long",
    "location-lat",
    "height-above-msl",
    "individual-local-identifier",
}


def audit(datapackage: Path, reference_csv: Path) -> dict:
    package = json.loads(datapackage.read_text(encoding="utf-8"))
    supported_gps_resources = []
    for res in package.get("resources", []):
        fields = {
            f.get("name")
            for f in (res.get("schema") or {}).get("fields", [])
            if f.get("name")
        }
        if GPS_REQUIRED.issubset(fields):
            supported_gps_resources.append(str(res.get("name", "unnamed")))

    with reference_csv.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"animal-id", "animal-taxon", "deploy-on-date"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("reference metadata are missing: " + repr(
                sorted(required - set(reader.fieldnames or []))
            ))
        individuals = set()
        species = Counter()
        years = Counter()
        nrows = 0
        for record in reader:
            nrows += 1
            animal_id = (record.get("animal-id") or "").strip()
            taxon = (record.get("animal-taxon") or "").strip()
            deploy_date = (record.get("deploy-on-date") or "").strip()
            if animal_id:
                individuals.add(animal_id)
            if taxon:
                species[taxon] += 1
            if deploy_date:
                years[deploy_date[:4]] += 1

    return {
        "dataset_id": package.get("id"),
        "audit_type": "metadata_and_schema_only",
        "reference_rows": nrows,
        "distinct_animal_ids": len(individuals),
        "reference_taxon_rows": dict(sorted(species.items())),
        "deployment_start_year_rows": dict(sorted(years.items())),
        "gps_schema_resources": sorted(supported_gps_resources),
        "gps_schema_required_fields": sorted(GPS_REQUIRED),
        "schema_candidate": bool(individuals and supported_gps_resources),
        "independent_sessions_tested": False,
        "animal_vertical_values_opened": False,
        "ecological_outcomes_computed": False,
        "admission": "NOT_ADMITTED_metadata_screen_only",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datapackage", required=True, type=Path)
    parser.add_argument("--reference-csv", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.datapackage, args.reference_csv)
    serialized = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
