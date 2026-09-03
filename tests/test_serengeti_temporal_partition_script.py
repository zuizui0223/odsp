from datetime import date

from scripts import run_n2_serengeti_temporal_partition as lane


def test_effort_intervals_merge_without_double_count(tmp_path):
    path = tmp_path / "search_effort.csv"
    path.write_text(
        "Site ID,Start date,End date\n"
        "A,2011-01-01,2011-01-10\n"
        "A,2011-01-08,2011-01-15\n"
        "B,2011-02-01,2011-02-02\n",
        encoding="utf-8",
    )
    active_days, audit = lane._load_effort(path)
    assert active_days == {"A": 15, "B": 2}
    assert audit["camera_days"] == 17


def test_event_filter_preserves_source_time_and_deduplicates_30_minutes(tmp_path):
    effort = tmp_path / "search_effort.csv"
    effort.write_text(
        "Site ID,Start date,End date\nA,2011-01-01,2011-01-31\n",
        encoding="utf-8",
    )
    active_days, _ = lane._load_effort(effort)

    consensus = tmp_path / "consensus_data.csv"
    consensus.write_text(
        "DateTime,SiteID,Species,NumVotes,NumClassifications\n"
        "2011-01-01 01:00:00,A,zebra,10,10\n"
        "2011-01-01 01:10:00,A,zebra,10,10\n"
        "2011-01-01 01:30:00,A,zebra,10,10\n"
        "2011-01-01 05:00:00,A,human,10,10\n"
        "2011-01-01 09:00:00,A,gazelle,5,10\n",
        encoding="utf-8",
    )
    events, audit = lane._load_events(consensus, active_days)
    assert [event[2].hour for event in events] == [1, 1]
    assert events[0][2].minute == 0
    assert events[1][2].minute == 30
    assert audit["removed_same_species_site_within_30min"] == 1
    assert audit["excluded_group_categories"] == 1
    assert audit["excluded_uncertain"] == 1


def test_species_admission_is_distribution_blind(monkeypatch):
    monkeypatch.setattr(lane, "MIN_EVENTS", 3)
    monkeypatch.setattr(lane, "MIN_SITES", 3)
    monkeypatch.setattr(lane, "MIN_EVENTS_EACH_FOLD", 1)

    # Find three synthetic site names spanning all deterministic folds.
    sites_by_fold = {}
    index = 0
    while len(sites_by_fold) < 3:
        site = f"S{index}"
        sites_by_fold.setdefault(lane._site_fold(site), site)
        index += 1
    sites = [sites_by_fold[fold] for fold in range(3)]

    events = [
        (site, "species_a", lane.datetime(2011, 1, 1, 12, 0, 0))
        for site in sites
    ]
    admitted, audit = lane._admit_species(events)
    assert admitted == ["species_a"]
    assert audit["species_a"]["events_by_fold"] == [1, 1, 1]


def test_date_parser_accepts_source_iso_dates():
    assert lane._parse_date("2011-07-09") == date(2011, 7, 9)
