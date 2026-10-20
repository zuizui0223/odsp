"""Synthetic regressions for post-outcome measurement identifiability audit."""
from prospective.delta2021_device_qc import inspect_rows


def row(a="A",tag="tag-a",stamp="2021-05-01 08:00:00.000",speed="8",gps="150",bar="120",hdop="1.2",sat="8",tf="20",sp="Larus fuscus",outlier="false"):
    return {
        "individual-taxon-canonical-name":sp,
        "individual-local-identifier":a,
        "tag-local-identifier":tag,
        "timestamp":stamp,
        "location-long":"3.72",
        "location-lat":"51.62",
        "ground-speed":speed,
        "height-above-msl":gps,
        "bar:barometric-height":bar,
        "gps:hdop":hdop,
        "gps:satellite-count":sat,
        "gps-time-to-fix":tf,
        "import-marked-outlier":outlier,
    }


def test_tag_identity_one_to_one_is_not_bird_identity_discriminator():
    rows=[row(a="A",tag="t1"),row(a="B",tag="t2",stamp="2021-05-01 09:00:00.000")]
    out=inspect_rows(rows)
    r=out["panels"]["Larus fuscus"]
    assert r["flight"]["distinct_birds"]==2
    assert r["device"]["birds_with_two_tags"]==0
    assert r["device"]["tags_shared_by_birds"]==0
    assert r["device"]["cross_tag_repeated_birds"]==0


def test_cross_tag_gate_requires_two_distinct_days_each_tag():
    rows=[
        row(a="A",tag="t1",stamp="2021-05-01 08:00:00.000"),
        row(a="A",tag="t1",stamp="2021-05-02 08:00:00.000"),
        row(a="A",tag="t2",stamp="2021-05-03 08:00:00.000"),
        row(a="A",tag="t2",stamp="2021-05-04 08:00:00.000"),
    ]
    r=inspect_rows(rows)["panels"]["Larus fuscus"]["device"]
    assert r["birds_with_two_tags"]==1
    assert r["cross_tag_repeated_birds"]==1


def test_constant_barometric_zero_is_not_an_independent_height_channel():
    rows=[row(stamp=f"2021-05-01 08:{5*i:02d}:00.000",bar="0") for i in range(10)]
    q=inspect_rows(rows)["panels"]["Larus fuscus"]["barometer"]
    assert q["paired_valid_gps_bins"]==10
    assert q["finite_paired_bins"]==10
    assert q["nonzero_paired_bins"]==0
    assert q["distinct_values_at_most_1000"]==1
    assert not q["channel_candidate"]


def test_first_fix_precedes_height_quality_and_outlier_excluded():
    rows=[
       row(gps="",bar="100"),
       row(stamp="2021-05-01 08:01:00.000",gps="200",bar="120"),
       row(a="B",stamp="2021-05-01 08:10:00.000",outlier="true"),
    ]
    p=inspect_rows(rows)["panels"]["Larus fuscus"]
    assert p["flight"]["first_5min_bins"]==1
    assert p["flight"]["valid_gps_height_bins"]==0


def test_stationary_availability_separate_from_flying():
    rows=[
      row(stamp=f"2021-05-01 09:{2*i:02d}:00.000",speed="0.1")
      for i in range(20)
    ] + [row(stamp="2021-05-02 08:00:00.000")]
    p=inspect_rows(rows)["panels"]["Larus fuscus"]
    assert p["stationary"]["bird_days_at_least_20_bins"]==0
    assert p["flight"]["first_5min_bins"]==1


def test_no_tag_id_cannot_establish_device_independence():
    p=inspect_rows([row(tag="")])["panels"]["Larus fuscus"]
    assert p["device"]["birds_with_unknown_tag"]==1
    assert not p["device"]["separable_within_year"]


def test_quality_columns_missing_is_reported_not_zero():
    p=inspect_rows([row(hdop="",sat="",tf="")])["panels"]["Larus fuscus"]
    assert p["gps_quality"]["gps:hdop"]["finite_fraction"]==0
    assert p["gps_quality"]["gps:satellite-count"]["p50"] is None
