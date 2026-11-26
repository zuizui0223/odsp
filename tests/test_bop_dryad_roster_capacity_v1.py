"""Independent small-set enumeration and exact probability checks."""
from fractions import Fraction as F
from itertools import combinations
from math import comb

import pytest

from scripts.audit_bop_dryad_roster_capacity_v1 import (
    audit, novelty_bounds, failure_limit, exact_power, best_fixed_n_power,
    checked_json,
)


def test_pinned_counts_and_status():
    result = audit()
    a, b = result["scenarios"]["v3"], result["scenarios"]["v2026"]
    assert [x["data_1a_novel_lower"] for x in a["taxa"].values()] == [83, 36, 13, 17]
    assert [x["data_1a_novel_lower"] for x in b["taxa"].values()] == [82, 36, 7, 16]
    assert a["joint_novel_lower"] == 176
    assert b["joint_novel_lower"] == 168
    assert a["joint_novel_upper"] == b["joint_novel_upper"] == 217
    assert a["taxa"]["Circus pygargus"]["additional_exclusion_budget_if_lower_at_least_30"] == 53
    assert b["taxa"]["Circus cyaneus"]["additional_exclusion_budget_if_lower_at_least_30"] == 6
    assert not result["real_source_admitted"]
    assert not result["canonical_identity_resolved"]
    assert result["prior_small_sidecar_access_status"] == "HTTP_403_ALL_THREE"


@pytest.mark.parametrize("retained", range(6))
@pytest.mark.parametrize("excluded", [0, 1, 3, 5])
def test_bounds_against_explicit_sets(retained, excluded):
    # A:3, B:2, independently possible overlap subsets up to cap.
    universe = tuple(range(5))
    counts = {"A": 3, "B": 2}
    caps = {"A": excluded, "B": 1}
    observed = []
    for subset in combinations(universe, retained):
        for n in range(6):
            for overlap in combinations(universe, n):
                if sum(x < 3 for x in overlap) > excluded or sum(x >= 3 for x in overlap) > 1:
                    continue
                novel = set(subset) - set(overlap)
                observed.append((sum(x < 3 for x in novel), sum(x >= 3 for x in novel), len(novel)))
    result = novelty_bounds(counts, caps, retained, ("A", "B"))
    for i, s in enumerate(("A", "B")):
        assert result["taxa"][s]["data_1a_novel_lower"] == min(r[i] for r in observed)
        assert result["taxa"][s]["data_1a_novel_upper"] == max(r[i] for r in observed)
    assert result["joint_novel_lower"] == min(r[2] for r in observed)
    assert result["joint_novel_upper"] == max(r[2] for r in observed)


@pytest.mark.parametrize("source,excluded,retained,taxa", [
    ({"A": True}, {"A": 0}, 1, ("A",)),
    ({"A": 1}, {"A": -1}, 1, ("A",)),
    ({"A": 1}, {"A": 0}, 2, ("A",)),
    ({"A": 1}, {"A": 0}, 1, ("A", "A")),
    ({"A": 1}, {}, 1, ("A",)),
    ({"A": 1}, {"A": 0}, 1, ()),
])
def test_invalid_counts_stop(source, excluded, retained, taxa):
    with pytest.raises(ValueError):
        novelty_bounds(source, excluded, retained, taxa)


@pytest.mark.parametrize("n,k", [(0,-1),(9,-1),(28,-1),(29,0),(45,0),(46,1),(76,3),(89,4),(179,11)])
def test_exact_decision_boundary(n,k):
    assert failure_limit(n) == k
    if k >= 0:
        tail = sum(F(comb(n,x)*9**(n-x),10**n) for x in range(k+1))
        assert tail <= F(1,20)
    if k < n:
        next_tail = sum(F(comb(n,x)*9**(n-x),10**n) for x in range(k+2))
        assert next_tail > F(1,20)


def test_power_is_not_monotone_and_fixed_design_ceiling_is_enumerated():
    assert exact_power(29,F(19,20)) == F(19,20)**29
    assert exact_power(30,F(19,20)) < exact_power(29,F(19,20))
    assert exact_power(29,F(9,10)) <= F(1,20)
    assert best_fixed_n_power(28,F(19,20)) is None
    ceiling = best_fixed_n_power(100,F(19,20))
    assert ceiling["best_fixed_calibration_n"] == 89
    assert ceiling["maximum_nonpositive_count"] == 4
    assert ceiling["maximum_power"] == pytest.approx(0.5394286633325065)


def test_original_blob_is_checked_before_json_parse(tmp_path):
    (tmp_path / "x.json").write_text("{}",encoding="utf-8")
    with pytest.raises(ValueError,match="blob mismatch"):
        checked_json(tmp_path,"x.json","0"*40)
