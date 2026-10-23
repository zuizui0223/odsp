#!/usr/bin/env python3
"""Post-hoc two-part SENSOR description, not a behavioral hurdle model.

Keep the original nine individuals, 186 pairs, all seven labels and median
endpoint unchanged. Zero/positive refer to reported GPS speed, not a validated
stop/move state. Equal dates, then equal groups and individuals; no p-values.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

BASELINE_SHA = '557c21c6446556f16c24ccf496b0b2c7ea8e22c259830a9e9a764faec10e5e8b'
PHASES = ('FN', 'FD', 'RN', 'RD')
METRICS = ('delta_p', 'delta_M', 'delta_C', 'occurrence_term', 'positive_magnitude_term')


def date_equal_mixture(blocks: list[list[float]]) -> dict:
    """Blocks contain log1p speed. Every original date has equal weight."""
    if not blocks or any(not b for b in blocks):
        raise ValueError('Empty sampling block is not a zero observation.')
    if any(not math.isfinite(v) or v < 0 for b in blocks for v in b):
        raise ValueError('Nonfinite/negative log1p speed.')
    p = st.mean(sum(v > 0 for v in b)/len(b) for b in blocks)
    M = st.mean(st.mean(b) for b in blocks)
    C = M/p if p > 0 else None
    return {'p': p, 'M': M, 'C': C}


def seasonal_contrast(parts: dict) -> dict:
    def dd(field):
        values = [parts[k][field] for k in PHASES]
        return None if any(v is None for v in values) else values[0]-values[1]-values[2]+values[3]
    result = {'delta_p': dd('p'), 'delta_M': dd('M'), 'delta_C': dd('C'),
              'occurrence_term': None, 'positive_magnitude_term': None, 'identity_error': None}
    if result['delta_C'] is not None:
        occurrence = magnitude = 0.0
        for zone, sign in [('N', 1), ('D', -1)]:
            f, r = parts['F'+zone], parts['R'+zone]
            occurrence += sign*.5*(f['C']+r['C'])*(f['p']-r['p'])
            magnitude += sign*.5*(f['p']+r['p'])*(f['C']-r['C'])
        err = abs(occurrence+magnitude-result['delta_M'])
        if err > 1e-12:
            raise AssertionError('Mixture identity failed.')
        result.update(occurrence_term=occurrence, positive_magnitude_term=magnitude, identity_error=err)
    return result


def describe(values: list) -> dict:
    usable = [x for x in values if x is not None]
    loo = [st.mean(usable[:i]+usable[i+1:]) for i in range(len(usable))] if len(usable) > 1 else []
    return {'n_defined_individuals': len(usable), 'n_undefined_individuals': len(values)-len(usable),
            'mean': st.mean(usable) if usable else None, 'median': st.median(usable) if usable else None,
            'positive': sum(x > 0 for x in usable), 'negative': sum(x < 0 for x in usable),
            'zero': sum(x == 0 for x in usable),
            'leave_one_individual_out_mean_range_not_CI': [min(loo), max(loo)] if loo else None}


def strict_group_mean(rows, field):
    vals = [r[field] for r in rows]
    return None if any(v is None for v in vals) else st.mean(vals)


def run(path: Path) -> dict:
    from scripts import run_2025_seven_duck_gps_solar_matched_speed_v0 as old
    from scripts import audit_2025_seven_duck_gps_daylength_source_v0 as source
    baseline = old.run(path)
    digest = hashlib.sha256((json.dumps(baseline, sort_keys=True, indent=2)+'\n').encode()).hexdigest()
    if digest != BASELINE_SHA:
        raise ValueError('Frozen original median-speed result failed byte-exact replay.')
    groups = defaultdict(lambda: defaultdict(lambda: {'day': [], 'night': []}))
    positions = defaultdict(list)
    timestamps = defaultdict(list)
    with path.open(newline='', encoding='utf-8-sig') as h:
        for row in csv.DictReader(h):
            study, ident, taxon = [row[k].strip() for k in
                                  ('study.name', 'individual.id', 'individual.taxon.canonical.name')]
            if not all((study, ident, taxon)):
                continue
            try:
                t = source.parse_original_time(row['timestamp'])
                lat, lon, speed = [float(row[k]) for k in ('location.lat', 'location.long', 'ground.speed')]
                if not all(math.isfinite(v) for v in (lat, lon, speed)) or not (-90<=lat<=90 and -180<=lon<=180 and 0<=speed<=60):
                    continue
            except (ValueError, TypeError):
                continue
            support = source.date_support(study, ident, taxon, t, lat, lon)
            if support is None:
                continue
            key, branch = support
            zone = 'day' if old.is_daylight_at_GPS_UTC(t, lat, lon) else 'night'
            groups[key][(branch, t.date())][zone].append(math.log1p(speed))
            positions[key].append(lat)
            timestamps[(key, branch, t.date(), zone)].append(t)

    by_taxon = defaultdict(lambda: defaultdict(list))
    counts = defaultdict(Counter)
    raw_counts = defaultdict(lambda: defaultdict(Counter))
    total_pairs = total_blocks = total_readings = total_duplicates = 0
    for key, days in groups.items():
        pairs, _ = old.one_to_one_source_datepairs(days, st.median(positions[key]))
        if len(pairs) < old.MIN_MATCHED_DATES_PER_GROUP:
            continue
        taxon, animal = key[2], key[:2]
        blocks = {k: [] for k in PHASES}
        old_deltas = []
        for f, r, mismatch in pairs:
            old_deltas.append(old.night_minus_day_median_log1p(days[('falling', f)])-
                              old.night_minus_day_median_log1p(days[('rising', r)]))
            for b, d, short in [('falling', f, 'F'), ('rising', r, 'R')]:
                for z, zs in [('night', 'N'), ('day', 'D')]:
                    phase = short+zs
                    values = days[(b, d)][z]
                    blocks[phase].append(values)
                    ts = timestamps[(key, b, d, z)]
                    dup = len(ts)-len(set(ts))
                    raw_counts[taxon][phase].update(readings=len(values), positive=sum(v>0 for v in values),
                                                   repeated_timestamps=dup)
                    total_duplicates += dup
                    total_blocks += 1
                    total_readings += len(values)
        total_pairs += len(pairs)
        counts[taxon]['pairs'] += len(pairs)
        counts[taxon]['groups'] += 1
        parts = {phase: date_equal_mixture(blocks[phase]) for phase in PHASES}
        result = seasonal_contrast(parts)
        result['parts'] = parts
        result['original_median_effect'] = st.mean(old_deltas)
        by_taxon[taxon][animal].append(result)

    species = []
    for before in baseline['all_original_seven_taxa_species_results']:
        taxon = before['published_source_taxon']
        records = []
        for rows in by_taxon[taxon].values():
            record = {field: strict_group_mean(rows, field) for field in METRICS}
            record['old'] = st.mean(r['original_median_effect'] for r in rows)
            record['parts'] = {phase: {field: strict_group_mean([r['parts'][phase] for r in rows], field)
                                       for field in ('p','M','C')} for phase in PHASES}
            records.append(record)
        if len(records) != before['n_distinct_independent_individuals'] or counts[taxon]['pairs'] != before['matched_balanced_daylength_datepairs']:
            raise ValueError('Original species cohort or matched date count changed.')
        if records and abs(st.mean(r['old'] for r in records)-before['individual_effect_mean']) > 1e-12:
            raise ValueError('Original median endpoint changed.')
        species.append({'taxon': taxon, 'n_individuals': len(records), 'original_pairs': counts[taxon]['pairs'],
                        'original_median_effect_unchanged': before['individual_effect_mean'],
                        'headline_support_n_ge_5': len(records)>=5,
                        'phase_profiles': {phase: {field: describe([r['parts'][phase][field] for r in records])
                                                   for field in ('p','M','C')} for phase in PHASES},
                        'contrasts': {field: describe([r[field] for r in records]) for field in METRICS},
                        'raw_selected_reading_counts_NOT_weights': {p: dict(raw_counts[taxon][p]) for p in PHASES}})
    if (sum(r['n_individuals'] for r in species), total_pairs, total_blocks, total_readings, total_duplicates) != (9,186,744,7850,2):
        raise ValueError('Original accepted sensor sample no longer matches audit.')
    return {'status': 'POST_HOC_TWO_PART_REPORTED_SPEED_NOT_ACTIVITY',
            'baseline_result_sha256_replayed': digest, 'source_md5': source.PINNED_MD5,
            'individuals': 9, 'matched_pairs': total_pairs, 'blocks': total_blocks, 'sensor_readings': total_readings,
            'duplicate_timestamp_extra_rows_retained': total_duplicates, 'species': species,
            'threshold_search_performed': False, 'behavioral_state_calibrated': False,
            'old_outputs_replaced': False, 'raw_locations_or_animal_ids_exported': False,
            'interpretation': 'Positive reporting fraction and size conditional on positive report; not bouts, inactivity, activity budgets or independent replication.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = run(a.input)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'species': [{'taxon': r['taxon'], 'n': r['n_individuals'],
                      'contrasts': r['contrasts']} for r in result['species']]}, sort_keys=True))

if __name__ == '__main__':
    main()
