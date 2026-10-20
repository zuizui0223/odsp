from prospective.gull_support_diagnostic_v1 import stage_counts, summarise


def test_single_bird_cannot_supply_other_individual_reference():
    counts = {('A','2022-05-01',(1,1)):60, ('A','2022-05-02',(1,1)):60}
    assert stage_counts(counts, 'legacy_bug')['eligible_birds'] == 1
    assert stage_counts(counts, 'correct_other_ids')['eligible_birds'] == 0


def test_two_birds_repeated_dates_remain_eligible():
    counts = {(a,d,(1,1)):60 for a in ('A','B') for d in ('2022-05-01','2022-05-02')}
    for s in ('correct_other_ids','exclude_same_date','long_donor_days_only'):
        assert stage_counts(counts,s)['eligible_birds'] == 2


def test_short_donor_day_discard_is_a_separate_restriction():
    counts = {(a,d,cell):n for a in ('A','B') for d,cell,n in (
        ('2022-05-01',(1,1),60), ('2022-05-02',(2,2),60),
        ('2022-05-03',(1,1),10), ('2022-05-04',(2,2),10))}
    assert stage_counts(counts,'exclude_same_date')['eligible_birds'] == 2
    assert stage_counts(counts,'long_donor_days_only')['eligible_birds'] == 0


def test_adding_restrictions_never_increases_eligibility():
    counts = {(a,d,(1,1)):60 for a in ('A','B') for d in ('2022-05-01','2022-05-02')}
    out = summarise(counts)
    assert out['raw_day']['eligible_birds'] >= out['long_donor_days_only']['eligible_birds']


def test_only_same_date_other_bird_cannot_be_other_date_reference():
    counts = {('A','2022-05-01',(1,1)):60, ('A','2022-05-02',(2,2)):60,
              ('A','2022-05-03',(1,1)):10, ('A','2022-05-04',(2,2)):10,
              ('B','2022-05-01',(1,1)):10, ('B','2022-05-02',(2,2)):10}
    assert stage_counts(counts,'correct_other_ids')['eligible_birds'] == 1
    assert stage_counts(counts,'exclude_same_date')['eligible_birds'] == 0
