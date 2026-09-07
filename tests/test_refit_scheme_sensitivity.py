import numpy as np
import pytest

from odsp.refit_scheme_sensitivity import audit_refit_scheme_sensitivity


def _fixture(refits=8, groups_n=2, blocks_n=8, rows_per_block=2):
    groups=tuple(f"g{g}" for g in range(groups_n) for _ in range(blocks_n*rows_per_block))
    blocks=tuple(f"b{b}" for _ in range(groups_n) for b in range(blocks_n) for _ in range(rows_per_block))
    n=len(groups)
    base=np.full((refits,n),0.30)
    schemes={"a":base.copy(),"b":base.copy()+0.02}
    return schemes,groups,blocks


def test_stable_positive_schemes_are_admissible():
    schemes,groups,blocks=_fixture()
    result=audit_refit_scheme_sensitivity(
        schemes,groups,blocks=blocks,nested_draws=500,minimum_refits=8,minimum_blocks_per_group=8,
    )
    assert result.sensitivity_category=="scheme_robust_generalizing"
    assert result.scheme_robust_admissible
    assert result.scheme_names==("a","b")


def test_unavailable_scheme_blocks_global_claim():
    schemes,groups,blocks=_fixture()
    schemes["b"]=schemes["b"][:4]
    result=audit_refit_scheme_sensitivity(
        schemes,groups,blocks=blocks,nested_draws=500,minimum_refits=8,minimum_blocks_per_group=8,
    )
    assert result.sensitivity_category=="unavailable"
    assert result.unavailable_scheme_count==1
    assert not result.scheme_robust_admissible


def test_rejects_unknown_scheme_metadata():
    schemes,groups,blocks=_fixture()
    with pytest.raises(ValueError,match="unknown scheme"):
        audit_refit_scheme_sensitivity(
            schemes,groups,blocks=blocks,refit_ids_by_scheme={"missing":["x"]*8},nested_draws=500,
        )
