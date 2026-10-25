"""Registry-first solar-azimuth macroecology audit and fixed-source pilot.

Modes:
  frame   -- purely metadata: all 437 Movebank public packages.
  pilot   -- all three previously registered original UTC GPS CSVs.
  utah    -- all four published taxa in one original ZIP (time-only fix choice).
  wyoming -- both original published taxa in the second, independent source.

Pilot sources have already been used for OTHER scientific endpoints and are therefore
post-exposure exploratory for this new response, never untouched confirmation.
Raw coordinates, UTC fixes and individual IDs never leave the runner.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

from odsp.solar_azimuth_macro_v0 import analyze_taxon
from scripts.movebank_native_ecology_20261019 import (
    CATALOG, PILOT, HERE, checksum_and_download, original_files
)
from scripts.movebank_solar_movement_20261019 import load_events
from scripts.movebank_utah_four_taxa_solar_20261019 import (
    CONTRACT as UTAH_CONTRACT, extract_time_only_original_source
)
from scripts.movebank_wyoming_two_ungulates_20261022 import (
    CONTRACT as WYOMING_CONTRACT, streaming_time_selected_csv
)

PROTOCOL = HERE / "research/GLOBAL_SOLAR_AZIMUTH_MACRO_V0_CONTRACT.json"
SCHEMA = "global-original-gps-solar-azimuth-macro-v0"
SOURCE_REPORT = "original_source_solar_azimuth_group_results.json"


def frame_rows(packages):
    rows = []
    for p in packages:
        sensors = {str(s).strip().lower() for s in (p.get("sensor_names") or [])}
        hires = "gps" in sensors or "gnss" in sensors
        argos = "argos doppler shift" in sensors
        named = [x for x in (p.get("scientific_names") or []) if isinstance(x, str) and x.strip()]
        animals = p.get("reported_animal_count")
        locations = p.get("reported_location_count")
        priority = bool(hires and isinstance(animals, (int, float)) and animals >= 5
                        and isinstance(locations, (int, float)) and locations >= 10000)
        rows.append({
            "package_uuid": p["package_uuid"], "sensor_class":
                ("GPS_GNSS" if hires else "ARGOS_ONLY" if argos else "OTHER_OR_MISSING"),
            "strict_GPS": "gps" in sensors,
            "species_labels": named,
            "reported_animals": animals,
            "reported_locations": locations,
            "metadata_only_priority": priority,
            "licenses": p.get("licenses") or [],
            "dois": p.get("dois") or [],
            "study_ids": p.get("study_ids") or p.get("movebank_study_ids") or [],
            "schema_and_trajectory_qualified": False,
            "reason": "Original files, unit independency, timestamp precision, positional accuracy and actual movement interval not yet screened"
        })
    return rows


def frame_summary(rows):
    gps = [r for r in rows if r["sensor_class"] == "GPS_GNSS"]
    broad = [r for r in rows if r["sensor_class"] in ("GPS_GNSS", "ARGOS_ONLY")]
    return {
        "snapshot_public_package_count": len(rows),
        "strict_GPS_packages": sum(r["strict_GPS"] for r in rows),
        "GPS_or_GNSS_packages": len(gps),
        "Argos_only_packages": sum(r["sensor_class"] == "ARGOS_ONLY" for r in rows),
        "broader_tracking_sensor_candidates": len(broad),
        "GPS_GNSS_distinct_scientific_name_labels": len({
            x for r in gps for x in r["species_labels"]
        }),
        "broad_tracking_distinct_scientific_name_labels": len({
            x for r in broad for x in r["species_labels"]
        }),
        "GPS_GNSS_metadata_priority_10000locations_5animals": sum(
            r["metadata_only_priority"] for r in gps),
        "original_tracks_qualified_by_this_census": 0,
        "ecological_effects_measured_by_this_census": 0,
        "interpretation": "Public package/sensor metadata only; not unique animal populations, habitat replicates, qualified wildlife taxa or available movement-step directions."
    }


def offline_frame(out: Path):
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    ps = cat["packages"]
    if len(ps) != 437 or len({p["package_uuid"] for p in ps}) != 437:
        raise ValueError("Previous complete public package catalog must remain exact")
    rows = frame_rows(ps)
    summary = frame_summary(rows)
    # Only registry-level metadata; NO raw GPS fixes.
    (out / "source_census.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (out / "source_prioritization.csv").open("w", newline="", encoding="utf-8") as fd:
        wr = csv.writer(fd)
        wr.writerow(["package_uuid", "sensor_class", "strict_gps",
                     "metadata_priority_only", "reported_animals", "reported_locations",
                     "original_names", "license_metadata", "dois"])
        for r in rows:
            wr.writerow([r["package_uuid"], r["sensor_class"], r["strict_GPS"],
                         r["metadata_only_priority"], r["reported_animals"],
                         r["reported_locations"], json.dumps(r["species_labels"]),
                         json.dumps(r["licenses"]), json.dumps(r["dois"])])
    return summary


def verified_original(spec: dict, out: Path, *, zipped: bool) -> Path:
    uuid = spec["package_uuid"]
    bitstream = spec.get("original_csv_bitstream_uuid", spec.get("original_bitstream_uuid"))
    md5 = spec.get("original_csv_md5", spec.get("original_md5"))
    files = [x for x in original_files(uuid) if x["bitstream_uuid"] == bitstream]
    if len(files) != 1 or files[0]["checksum"]["value"].lower() != md5.lower():
        raise ValueError("Original provider bitstream identity or MD5 does not match")
    expected_bytes = spec.get("original_bytes")
    if expected_bytes is not None and files[0]["bytes"] != expected_bytes:
        raise ValueError("Original provider bytes changed")
    path = out / ("private_original.zip" if zipped else "private_original.csv")
    checksum_and_download(files[0], path)
    return path


def each_source(stage: str, out: Path) -> dict:
    cohorts = []
    private_path = None
    try:
        if stage == "pilot":
            sources = json.loads(PILOT.read_text(encoding="utf-8"))["sources"]
            for p in sources:
                private_path = None
                entry = {"taxon": p["taxon"], "source": p["label"], "doi": p["doi"],
                         "source_status": "hold", "sensor": "original-GPS"}
                try:
                    private_path = verified_original(p, out, zipped=False)
                    animals, nrows, invalid = load_events(private_path)
                    entry.update(source_status="provider_MD5_verified_original",
                                 original_rows=nrows, invalid_source_rows=invalid,
                                 **analyze_taxon(animals))
                except Exception as e:
                    entry["error"] = f"{type(e).__name__}: {e}"
                finally:
                    if private_path is not None:
                        private_path.unlink(missing_ok=True)
                cohorts.append(entry)
                print("SOLAR_AZIMUTH_SOURCE " + json.dumps(entry, sort_keys=True), flush=True)
        elif stage == "utah":
            p = json.loads(UTAH_CONTRACT.read_text(encoding="utf-8"))["source"]
            for taxon in p["catalog_taxa"]:
                cohorts.append({"taxon": taxon, "source": "Utah_UDWR", "doi": p["doi"],
                                "source_status": "hold"})
            private_path = verified_original(p, out, zipped=True)
            grouped, counts, others = extract_time_only_original_source(private_path, p["catalog_taxa"])
            for entry in cohorts:
                taxon = entry["taxon"]
                observations = {animal: list(records.values())
                                for animal, records in grouped[taxon].items()}
                entry.update(source_status="provider_MD5_verified_original",
                             original_rows=counts[taxon]["rows"],
                             unclassified_taxon_rows_source_total=others,
                             **analyze_taxon(observations))
                print("SOLAR_AZIMUTH_SOURCE " + json.dumps(entry, sort_keys=True), flush=True)
                grouped[taxon].clear()
        elif stage == "wyoming":
            p = json.loads(WYOMING_CONTRACT.read_text(encoding="utf-8"))["source"]
            for taxon in p["published_species"]:
                cohorts.append({"taxon": taxon, "source": "Wyoming_2019_2020", "doi": p["doi"],
                                "source_status": "hold"})
            private_path = verified_original(p, out, zipped=False)
            grouped, counts, others = streaming_time_selected_csv(private_path, p["published_species"])
            for entry in cohorts:
                taxon = entry["taxon"]
                observations = {animal: list(records.values())
                                for animal, records in grouped[taxon].items()}
                entry.update(source_status="provider_MD5_verified_original",
                             original_rows=counts[taxon]["source_rows"],
                             unclassified_taxon_rows_source_total=others,
                             **analyze_taxon(observations))
                print("SOLAR_AZIMUTH_SOURCE " + json.dumps(entry, sort_keys=True), flush=True)
                grouped[taxon].clear()
        else:
            raise ValueError("Unknown source stage")
    except Exception as e:
        for entry in cohorts:
            if entry["source_status"] == "hold":
                entry["error"] = f"{type(e).__name__}: {e}"
        print("SOLAR_AZIMUTH_SOURCE_HOLD " + str(e), flush=True)
    finally:
        if private_path is not None:
            private_path.unlink(missing_ok=True)
    return {
        "version": SCHEMA, "stage": stage,
        "pilot_is_post_prior_outcome_exploratory": True,
        "source_taxon_entries": cohorts,
        "supported_entries": sum(x.get("status") == "descriptive_source_estimated"
                                 for x in cohorts),
        "clock_adjusted_identifiable_entries": sum(
            (x.get("results") or {}).get("clock_adjusted_excess_cos", {}).get("n_individuals", 0) >= 5
            for x in cohorts),
        "no_cross_source_metaanalysis_yet": True
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["frame", "pilot", "utah", "wyoming"])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    contract = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if contract["version"] != SCHEMA or contract["frame"]["complete_public_package_count"] != 437:
        raise ValueError("Frozen protocol/version or complete-frame gate differs")
    if args.stage == "frame":
        out = offline_frame(args.out)
    else:
        out = each_source(args.stage, args.out)
        (args.out / SOURCE_REPORT).write_text(
            json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("SOLAR_AZIMUTH_MACRO_SUMMARY " + json.dumps(out, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
