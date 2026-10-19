"""Synthetic tests: GPS altitudes must never be read by structural preflight."""
import csv
import gzip
from pathlib import Path

from prospective.screen_gull_event_support import audit_one_year


def write_gps(path: Path, rows: list[dict]) -> None:
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        fieldnames = [
            "timestamp", "individual-local-identifier", "location-long",
            "location-lat", "ground-speed", "height-above-msl",
            "manually-marked-outlier",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def test_repeat_days_coarse_horizontal_support(tmp_path: Path) -> None:
    path = tmp_path / "LBBG_SCHIERMONNIKOOG-gps-2017.csv.gz"
    rows = []
    for animal in ("bird1", "bird2"):
        for day in ("2017-05-12", "2017-05-13"):
            for bin_i in range(60):
                hr = 7 + bin_i // 12
                mm = 5 * (bin_i % 12)
                rows.append({
                    "timestamp": f"{day} {hr:02d}:{mm:02d}:00.000",
                    "individual-local-identifier": animal,
                    "location-long": "6.25",
                    "location-lat": "53.49",
                    "ground-speed": "8",
                    "height-above-msl": "DO_NOT_READ_ALTITUDE",
                    "manually-marked-outlier": "false",
                })
    write_gps(path, rows)
    r = audit_one_year(path, "lbbg", 2017)
    assert r["counts"]["all_rows"] == 240
    assert r["individuals_with_flight_proxy"] == 2
    assert r["individuals_with_2_scorable_days_50_bins"] == 2
    assert r["scorable_heldout_days"] == 4
    assert r["support_cells_5km"] == 1


def test_roost_and_outlier_do_not_create_fake_sessions(tmp_path: Path) -> None:
    path = tmp_path / "MEDGULL_ANTWERPEN-gps-2021.csv.gz"
    rows = [
        {
            "timestamp": f"2021-05-12 07:{5*i:02d}:00.000",
            "individual-local-identifier": "bird1",
            "location-long": "4.4",
            "location-lat": "51.2",
            "ground-speed": speed,
            "height-above-msl": "DO_NOT_READ_ALTITUDE",
            "manually-marked-outlier": outlier,
        }
        for i, (speed, outlier) in enumerate(
            [("0", "false"), ("8", "true"), ("10", "false")]
        )
    ]
    write_gps(path, rows)
    r = audit_one_year(path, "medgull", 2021)
    assert r["counts"]["source_marked_outliers"] == 1
    assert r["counts"]["not_flight_speed_proxy"] == 1
    assert r["flight_proxy_5min_unique_bins"] == 1
    assert r["individuals_with_2_scorable_days_50_bins"] == 0
