"""ODSP original-GPS solar-azimuth macroecology: geometry and auditable summaries.

The direction of a GPS displacement is NOT body orientation, experienced sunlight,
thermoregulation or a causal response to the sun. No original tracks are exported.
NOAA fractional-year solar-position approximation; event times must be UTC.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import calendar
import math
import random
from statistics import mean

EARTH_RADIUS_KM = 6371.0088
MIN_ELEVATION_DEG = 10.0
MIN_STEP_KM = 0.1
MIN_HOURS, MAX_HOURS = 0.5, 2.0
MAX_SPEED_KMPH = 60.0
MIN_YEAR_STEPS, MIN_YEAR_DAYS = 30, 5
MIN_BLOCK_STEPS, MIN_BLOCK_DAYS = 8, 3
MIN_BLOCK_AZIMUTH_SPAN_DEG = 5.0

@dataclass(frozen=True)
class Sun:
    azimuth: float  # 0 north, 90 east, clockwise degrees
    elevation: float  # geometric, not measured shading/refraction
    solar_hour: float
    solar_date: object

@dataclass(frozen=True)
class Step:
    bearing: float
    sun_azimuth: float
    solar_date: object
    solar_hour: float
    sun_elevation: float


def _utc_naive(t: datetime) -> datetime:
    if t.tzinfo is not None:
        return t.astimezone(timezone.utc).replace(tzinfo=None)
    return t  # caller must attest that naive event timestamps mean UTC


def sun_position(utc: datetime, lat: float, lon: float) -> Sun:
    """NOAA approximate solar position; UTC timestamp, WGS84 lat/lon.

    Site coordinates are used ephemerally. Do not export animal positions.
    Geometry is approximate, especially near poles or the zenith.
    """
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Invalid WGS84 coordinate")
    utc = _utc_naive(utc)
    days = 366 if calendar.isleap(utc.year) else 365
    hour = utc.hour + utc.minute / 60 + (utc.second + utc.microsecond / 1e6) / 3600
    gamma = 2 * math.pi / days * (utc.timetuple().tm_yday - 1 + (hour - 12) / 24)
    eot = 229.18 * (
        0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma)
    )
    dec = (
        0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma)
    )
    apparent_time = utc + timedelta(minutes=4 * lon + eot)
    solar_hour = (apparent_time.hour * 3600 + apparent_time.minute * 60
                  + apparent_time.second + apparent_time.microsecond / 1e6) / 3600
    ha = math.radians(15 * (solar_hour - 12))
    phi = math.radians(lat)
    sin_el = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(ha)
    el = math.degrees(math.asin(max(-1.0, min(1.0, sin_el))))
    az = (math.degrees(math.atan2(
        math.sin(ha),
        math.cos(ha) * math.sin(phi) - math.tan(dec) * math.cos(phi)
    )) + 180.0) % 360.0
    return Sun(az, el, solar_hour, apparent_time.date())


def bearing_degrees(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians((lon2 - lon1 + 180) % 360 - 180)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    if abs(x) + abs(y) < 1e-14:
        raise ValueError("Undefined zero-displacement bearing")
    return math.degrees(math.atan2(y, x)) % 360


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians((lon2 - lon1 + 180) % 360 - 180)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(max(0, min(1, h))))


def directional_step(first, second) -> Step | None:
    """Source tuples are (UTC time, latitude, longitude); no interpolation."""
    t1, a, b = first
    t2, c, d = second
    t1, t2 = _utc_naive(t1), _utc_naive(t2)
    hours = (t2 - t1).total_seconds() / 3600
    if not MIN_HOURS <= hours <= MAX_HOURS:
        return None
    km = distance_km(a, b, c, d)
    if km < MIN_STEP_KM or km / hours > MAX_SPEED_KMPH:
        return None
    midpoint = t1 + (t2 - t1) / 2
    midlat = (a + c) / 2
    # Circular mean longitude handles ordinary ±180-degree crossings.
    midlon = ((b + ((d - b + 180) % 360 - 180) / 2 + 180) % 360) - 180
    left = sun_position(t1, a, b)
    right = sun_position(t2, c, d)
    sun = sun_position(midpoint, midlat, midlon)
    if min(left.elevation, right.elevation, sun.elevation) < MIN_ELEVATION_DEG:
        return None
    if left.solar_date != right.solar_date or left.solar_date != sun.solar_date:
        return None
    return Step(bearing_degrees(a, b, c, d), sun.azimuth, sun.solar_date,
                sun.solar_hour, sun.elevation)


def cosine_alignment(steps: list[Step], harmonic: int = 1) -> tuple[float, float]:
    """Observed sun-relative cosine and its independent-compass-marginal baseline.

    Their difference is a circular covariance, NOT evidence of solar causation.
    """
    angles = [math.radians(harmonic * s.bearing) for s in steps]
    suns = [math.radians(harmonic * s.sun_azimuth) for s in steps]
    actual = mean(math.cos(b - a) for b, a in zip(angles, suns))
    baseline = (mean(math.cos(b) for b in angles) * mean(math.cos(a) for a in suns)
                + mean(math.sin(b) for b in angles) * mean(math.sin(a) for a in suns))
    return actual, baseline


def circular_span_degrees(angles) -> float:
    """Minimal arc containing all angles, robust around 0/360 degrees."""
    a = sorted(float(x) % 360 for x in angles)
    if len(a) < 2:
        return 0.0
    gaps = [a[i + 1] - a[i] for i in range(len(a) - 1)]
    gaps.append(a[0] + 360 - a[-1])
    return 360 - max(gaps)


def summarize_animal(steps: list[Step]) -> dict:
    if len(steps) < MIN_YEAR_STEPS or len({s.solar_date for s in steps}) < MIN_YEAR_DAYS:
        return {"supported": False, "reason": "insufficient_year_directional_steps"}
    raw, raw_base = cosine_alignment(steps)
    axial, axial_base = cosine_alignment(steps, harmonic=2)
    by_clock = defaultdict(list)
    for s in steps:
        # The most stringent estimand only uses changes in sun azimuth remaining
        # WITHIN the same original animal/month/two-hour apparent-solar clock bin.
        key = (s.solar_date.year, s.solar_date.month, int(s.solar_hour // 2))
        by_clock[key].append(s)
    excess, axial_excess = [], []
    n_clock_steps = 0
    for block in by_clock.values():
        if len(block) < MIN_BLOCK_STEPS:
            continue
        if len({s.solar_date for s in block}) < MIN_BLOCK_DAYS:
            continue
        if circular_span_degrees(s.sun_azimuth for s in block) < MIN_BLOCK_AZIMUTH_SPAN_DEG:
            continue
        a, b = cosine_alignment(block)
        aa, bb = cosine_alignment(block, 2)
        excess.append(a - b)
        axial_excess.append(aa - bb)
        n_clock_steps += len(block)
    return {
        "supported": True, "qualified_steps": len(steps),
        "solar_days": len({s.solar_date for s in steps}),
        "raw_toward_sun_mean_cos": raw,
        "raw_axial_mean_cos2": axial,
        "compass_independence_excess_cos": raw - raw_base,
        "compass_independence_excess_cos2": axial - axial_base,
        "clock_adjusted_identifiable": bool(excess),
        "clock_adjusted_strata": len(excess),
        "clock_adjusted_steps": n_clock_steps,
        "clock_adjusted_excess_cos": mean(excess) if excess else None,
        "clock_adjusted_excess_cos2": mean(axial_excess) if axial_excess else None
    }


def _bootstrap(values: list[float], seed: int = 20261025) -> list[float] | None:
    if len(values) < 5:
        return None
    rng = random.Random(seed)
    n = len(values)
    draws = sorted(mean(values[rng.randrange(n)] for _ in range(n)) for _ in range(1000))
    return [draws[24], draws[974]]


def analyze_taxon(animals: dict) -> dict:
    """Equal animal then equal individual-year weighting, never equal GPS-fix weight."""
    valid = defaultdict(list)
    total_adjacent = total_qualified = 0
    for animal, records in animals.items():
        fixes = sorted(records)
        for a, b in zip(fixes, fixes[1:]):
            total_adjacent += 1
            s = directional_step(a, b)
            if s is not None:
                valid[(animal, s.solar_date.year)].append(s)
                total_qualified += 1
    animal_values = defaultdict(list)
    for (animal, year), steps in valid.items():
        r = summarize_animal(steps)
        if r["supported"]:
            animal_values[animal].append(r)
    individual_rows = []
    for years in animal_values.values():
        keys = ("raw_toward_sun_mean_cos", "raw_axial_mean_cos2",
                "compass_independence_excess_cos", "compass_independence_excess_cos2")
        record = {k: mean(y[k] for y in years) for k in keys}
        for k in ("clock_adjusted_excess_cos", "clock_adjusted_excess_cos2"):
            measured = [y[k] for y in years if y[k] is not None]
            record[k] = mean(measured) if measured else None
        individual_rows.append(record)
    means = {}
    for key in ("raw_toward_sun_mean_cos", "raw_axial_mean_cos2",
                "compass_independence_excess_cos", "compass_independence_excess_cos2",
                "clock_adjusted_excess_cos", "clock_adjusted_excess_cos2"):
        values = [r[key] for r in individual_rows if r[key] is not None]
        means[key] = {"n_individuals": len(values),
                      "mean": mean(values) if len(values) >= 5 else None,
                      "bootstrap95": _bootstrap(values)}
    return {
        "source_animals": len(animals), "adjacent_steps": total_adjacent,
        "daylight_directional_qualified_steps": total_qualified,
        "supported_individual_years": sum(len(y) for y in animal_values.values()),
        "supported_individuals": len(individual_rows),
        "results": means,
        "status": ("descriptive_source_estimated" if len(individual_rows) >= 5
                   else "insufficient_independent_animals"),
        "claim_ceiling": "Detected GPS displacement directions; possible solar/clock/migration/habitat confounding. No causal solar orientation or universal macroecological law."
    }
