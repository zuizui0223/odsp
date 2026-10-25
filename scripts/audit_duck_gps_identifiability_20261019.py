#!/usr/bin/env python3
"""Post-outcome audit, not a new speed-effect test or a relaxation of v0.

Preserve the 2025 source MD5 and byte-exact original 2026-10-18 GPS result.
Identify the observational bottleneck; bound matching capacity without reading
speed magnitudes into the matching rule; report duplicates and median-zero
support. No animal IDs, coordinates, dates, or individual effects exported.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

BASELINE_SHA256 = '557c21c6446556f16c24ccf496b0b2c7ea8e22c259830a9e9a764faec10e5e8b'
BASELINE_COMMIT = '18923d090861a604e02386c8640da9c62d8acf25'
STAGES = ('day_night_sampling', 'photoperiod_overlap', 'fix_count_balance',
          'greedy_pairing', 'included_v0')


def maximum_matching(graph: dict) -> dict:
    """Maximum cardinality, augmenting paths; no biological outcome scores."""
    right_to_left = {}
    def augment(left, seen):
        for right in graph[left]:
            if right in seen:
                continue
            seen.add(right)
            if right not in right_to_left or augment(right_to_left[right], seen):
                right_to_left[right] = left
                return True
        return False
    for left in graph:
        augment(left, set())
    return {left: right for right, left in right_to_left.items()}


def diagnose(n_f: int, n_r: int, astro: int, balanced: int, greedy: int) -> str:
    if min(n_f, n_r) < 5:
        return 'day_night_sampling'
    if astro < 5:
        return 'photoperiod_overlap'
    if balanced < 5:
        return 'fix_count_balance'
    if greedy < 5:
        return 'greedy_pairing'
    return 'included_v0'


def zero_summary(rows: list) -> dict:
    return {
        'zone_medians_zero': sum(statistics.median(x) == 0 for x in rows if x),
        'zone_medians_total': sum(bool(x) for x in rows),
        'sensor_samples_zero': sum(v == 0 for x in rows for v in x),
        'sensor_samples_total': sum(len(x) for x in rows),
    }


def run(path: Path) -> dict:
    from scripts import run_2025_seven_duck_gps_solar_matched_speed_v0 as old
    from scripts import audit_2025_seven_duck_gps_daylength_source_v0 as source
    baseline = old.run(path)
    baseline_bytes = (json.dumps(baseline, sort_keys=True, indent=2)+'\n').encode()
    if hashlib.sha256(baseline_bytes).hexdigest() != BASELINE_SHA256:
        raise ValueError('The unchanged original GPS result was not reproduced.')

    groups = defaultdict(lambda: defaultdict(lambda: {'day': [], 'night': []}))
    positions = defaultdict(list)
    prelim = defaultdict(lambda: defaultdict(lambda: {'dates': set(), 'n': 0}))
    stamps = defaultdict(list)
    original_individuals = defaultdict(set)
    duplicate_source = Counter()
    all_timestamps = set()
    n_rows = 0
    with path.open(newline='', encoding='utf-8-sig') as h:
        for row in csv.DictReader(h):
            n_rows += 1
            study = row['study.name'].strip()
            ident = row['individual.id'].strip()
            taxon = row['individual.taxon.canonical.name'].strip()
            original_individuals[taxon].add((study, ident))
            t = source.parse_original_time(row['timestamp'])
            stamp = (study, ident, t)
            if stamp in all_timestamps:
                duplicate_source[taxon] += 1
            all_timestamps.add(stamp)
            lat, lon = float(row['location.lat']), float(row['location.long'])
            speed = float(row['ground.speed'])
            support = source.date_support(study, ident, taxon, t, lat, lon)
            if support is None or not math.isfinite(speed) or speed < 0:
                continue
            key, branch = support
            prelim[key][branch]['dates'].add(t.date())
            prelim[key][branch]['n'] += 1
            if speed > old.MAX_GROUND_SPEED_MPS:
                continue
            zone = 'day' if old.is_daylight_at_GPS_UTC(t, lat, lon) else 'night'
            groups[key][(branch, t.date())][zone].append(math.log1p(speed))
            stamps[(key, branch, t.date(), zone)].append(t)
            positions[key].append(lat)

    prelim_keys = set()
    prelim_animals = defaultdict(set)
    for key, branches in prelim.items():
        if all(len(branches[b]['dates']) >= 7 and branches[b]['n'] >= 15
               for b in ('rising', 'falling')):
            prelim_keys.add(key)
            prelim_animals[key[2]].add(key[:2])
    if n_rows != 294683 or sum(map(len, prelim_animals.values())) != 36:
        raise ValueError('Original source-only 36-bird cohort failed to replay.')

    reached = defaultdict(dict)
    final_animals = defaultdict(set)
    maximum_capacity_animals = defaultdict(set)
    studies = defaultdict(set)
    zero_stats = defaultdict(Counter)
    missing_opportunity = defaultdict(Counter)
    by_species = defaultdict(Counter)
    groups_improvable = 0
    extra_pair_capacity = 0
    max_pairs_total = greedy_pairs_total = 0
    for key, days in groups.items():
        study, ident, taxon, year, latcell, loncell = key
        lat = statistics.median(positions[key])
        f_dates, r_dates = {}, {}
        for (b, day), values in days.items():
            if not old._daily_valid_sampling(values):
                continue
            length = old.modeled_photoperiod_minutes(day, lat)
            if length is not None:
                (f_dates if b == 'falling' else r_dates)[day] = length
        astro_graph = {f: [] for f in sorted(f_dates)}
        balanced_graph = {f: [] for f in sorted(f_dates)}
        for f in astro_graph:
            for r in sorted(r_dates):
                if abs(f_dates[f]-r_dates[r]) <= 5.0:
                    astro_graph[f].append(r)
                    if old.balanced_pair(days[('falling', f)], days[('rising', r)]):
                        balanced_graph[f].append(r)
        ma = len(maximum_matching(astro_graph))
        mb = len(maximum_matching(balanced_graph))
        pairs, _ = old.one_to_one_source_datepairs(days, lat)
        ng = len(pairs)
        if mb < ng:
            raise AssertionError('Maximum matching smaller than original greedy.')
        if mb > ng:
            groups_improvable += 1
        extra_pair_capacity += mb-ng
        max_pairs_total += mb
        greedy_pairs_total += ng
        stage = diagnose(len(f_dates), len(r_dates), ma, mb, ng)
        if key in prelim_keys:
            previous = reached[taxon].get((study, ident), 0)
            reached[taxon][(study, ident)] = max(previous, STAGES.index(stage))
        for branch in ('rising', 'falling'):
            missing_opportunity[taxon][branch + '_all_dates'] += sum(b == branch for b, d in days)
            missing_opportunity[taxon][branch + '_both_solar_zone_dates'] += sum(
                b == branch and old._daily_valid_sampling(v) for (b, d), v in days.items())
        if mb >= 5:
            maximum_capacity_animals[taxon].add((study, ident))
        if ng < 5:
            continue
        final_animals[taxon].add((study, ident))
        studies[study].add((study, ident))
        by_species[taxon]['groups'] += 1
        by_species[taxon]['paired_dates'] += ng
        for f, r, mismatch in pairs:
            for branch, day in [('falling', f), ('rising', r)]:
                for zone in ('day', 'night'):
                    v = days[(branch, day)][zone]
                    zero_stats[taxon].update(zero_summary([v]))
                    ts = stamps[(key, branch, day, zone)]
                    zero_stats[taxon]['repeated_timestamps_in_used_zone_rows'] += len(ts)-len(set(ts))

    species = []
    for taxon in sorted(original_individuals):
        pre = prelim_animals[taxon]
        final = final_animals[taxon]
        loss = Counter(STAGES[reached[taxon].get(animal, 0)] for animal in pre)
        expected = next(r for r in baseline['all_original_seven_taxa_species_results']
                        if r['published_source_taxon'] == taxon)
        if len(final) != expected['n_distinct_independent_individuals']:
            raise AssertionError('Original per-species final sample not reproduced.')
        if by_species[taxon]['paired_dates'] != expected['matched_balanced_daylength_datepairs']:
            raise AssertionError('Original species date-pair count not reproduced.')
        species.append({
            'taxon': taxon,
            'original_marked_individuals': len(original_individuals[taxon]),
            'preliminary_individuals': len(pre),
            'v0_final_individuals': len(final),
            'v0_final_outside_preliminary_cohort': len(final-pre),
            'preliminary_loss_by_farthest_reached_stage': {s: loss[s] for s in STAGES},
            'maximum_matching_could_qualify_individuals_same_rules': len(maximum_capacity_animals[taxon]),
            'original_matched_pairs': by_species[taxon]['paired_dates'],
            'matched_v0_sensor_zero_and_duplicate_diagnostics': dict(zero_stats[taxon]),
            'source_duplicate_timestamps_all_rows': duplicate_source[taxon],
            'source_group_date_sampling': dict(missing_opportunity[taxon]),
        })
    return {
        'status': 'POST_OUTCOME_GPS_IDENTIFIABILITY_AUDIT_NOT_NEW_EFFECT_TEST',
        'audit_date': '2026-10-19',
        'source_md5': source.PINNED_MD5,
        'baseline_result_sha256_replayed': BASELINE_SHA256,
        'baseline_commit': BASELINE_COMMIT,
        'source_rows': n_rows,
        'original_marked_individuals': sum(map(len, original_individuals.values())),
        'preliminary_individuals': sum(map(len, prelim_animals.values())),
        'v0_final_individuals': sum(map(len, final_animals.values())),
        'per_species': species,
        'publication_study_names_of_v0_final_individuals': [
            {'public_study_name': s, 'distinct_individuals': len(v)} for s, v in sorted(studies.items())],
        'matching_capacity_without_changing_any_rule': {
            'original_greedy_pairs_all_groups_including_low_support': greedy_pairs_total,
            'maximum_cardinality_pairs_all_groups': max_pairs_total,
            'groups_with_greedy_capacity_loss': groups_improvable,
            'extra_pairs_mathematically_possible': extra_pair_capacity,
            'no_alternative_pair_speed_effects_computed': True},
        'interpretation_limits': [
            'An audit of sample opportunity, not a speed association selected for significance.',
            'Source study names describe recruitment/publication groups, not independent ecosystems.',
            'Sensor zero does not prove inactivity; a zero median may hide occasional large movements.',
            'Maximum matching bounds available sample size, not causal identification or a new result.',
            'No existing threshold, source outcome, matched pair or manuscript claim changed automatically.',
            'No animal identifiers, exact positions or timestamps exported.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
