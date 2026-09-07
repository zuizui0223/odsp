"""Known-truth benchmark for Forecast Assessment v4 row provenance."""
from __future__ import annotations

import numpy as np

from .forecast_assessment_v2 import assess_state_forecast_v2
from .forecast_assessment_v3 import assess_state_forecast_v3
from .forecast_assessment_v3_benchmark import _base_design, _common_kwargs, _scheme_kwargs
from .forecast_assessment_v4 import assess_state_forecast_v4


def _permuted_scheme_inputs(scheme_kwargs, base_ids):
    schemes = scheme_kwargs["refit_schemes"]
    n = next(iter(schemes.values())).shape[1]
    orders = {
        "bootstrap": np.arange(n),
        "fold": np.roll(np.arange(n), 41),
        "seed": np.random.default_rng(44671).permutation(n),
    }
    permuted_schemes = {
        name: matrix[:, orders[name]] for name, matrix in schemes.items()
    }
    row_ids = {
        name: tuple(np.asarray(base_ids, dtype=object)[orders[name]]) for name in schemes
    }
    return permuted_schemes, row_ids


def run_forecast_assessment_v4_benchmark(*, seed: int = 20260907) -> dict[str, object]:
    if seed != 20260907:
        raise ValueError("the frozen v4 benchmark uses seed 20260907")

    gain, groups, blocks, covered, bootstrap, _fold, _seed, fragile, ids = _base_design()
    n = gain.size
    conditional = gain.copy()
    marginal = np.zeros(n)
    base_ids = tuple(f"validation-{i:05d}" for i in range(n))

    base_kwargs = _common_kwargs()
    base_kwargs["region_size"] = np.full(n, 4.0, dtype=float)
    v2_formal_kwargs = dict(base_kwargs)
    v2_formal_kwargs.update(
        run_simultaneous_group_certification=True,
        simultaneous_draws=1200,
        refit_row_gain=bootstrap,
        refit_ids=ids["bootstrap"],
        reference_refit_id=ids["bootstrap"][0],
        refit_nested_draws=1200,
        minimum_refits=8,
    )
    robust_scheme_kwargs = _scheme_kwargs(ids)
    sensitive_scheme_kwargs = _scheme_kwargs(ids, sensitive=True)

    direct_strong = assess_state_forecast_v3(
        "strong", conditional, marginal, covered, groups, blocks,
        **v2_formal_kwargs, **robust_scheme_kwargs,
    )
    exact = assess_state_forecast_v4(
        "strong", conditional, marginal, covered, groups, blocks,
        **v2_formal_kwargs,
        refit_schemes=robust_scheme_kwargs["refit_schemes"],
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme={
            name: base_ids for name in robust_scheme_kwargs["refit_schemes"]
        },
        refit_ids_by_scheme=robust_scheme_kwargs["refit_ids_by_scheme"],
        reference_refit_ids_by_scheme=robust_scheme_kwargs["reference_refit_ids_by_scheme"],
        scheme_nested_draws=robust_scheme_kwargs["scheme_nested_draws"],
        scheme_seed=robust_scheme_kwargs["scheme_seed"],
        scheme_minimum_refits=robust_scheme_kwargs["scheme_minimum_refits"],
    )

    permuted_schemes, permuted_ids = _permuted_scheme_inputs(robust_scheme_kwargs, base_ids)
    permuted = assess_state_forecast_v4(
        "strong", conditional, marginal, covered, groups, blocks,
        **v2_formal_kwargs,
        refit_schemes=permuted_schemes,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=permuted_ids,
        refit_ids_by_scheme=robust_scheme_kwargs["refit_ids_by_scheme"],
        reference_refit_ids_by_scheme=robust_scheme_kwargs["reference_refit_ids_by_scheme"],
        scheme_nested_draws=robust_scheme_kwargs["scheme_nested_draws"],
        scheme_seed=robust_scheme_kwargs["scheme_seed"],
        scheme_minimum_refits=robust_scheme_kwargs["scheme_minimum_refits"],
    )

    direct_sensitive = assess_state_forecast_v3(
        "scheme-sensitive", conditional, marginal, covered, groups, blocks,
        **v2_formal_kwargs, **sensitive_scheme_kwargs,
    )
    sensitive = assess_state_forecast_v4(
        "scheme-sensitive", conditional, marginal, covered, groups, blocks,
        **v2_formal_kwargs,
        refit_schemes=sensitive_scheme_kwargs["refit_schemes"],
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme={
            name: base_ids for name in sensitive_scheme_kwargs["refit_schemes"]
        },
        refit_ids_by_scheme=sensitive_scheme_kwargs["refit_ids_by_scheme"],
        reference_refit_ids_by_scheme=sensitive_scheme_kwargs["reference_refit_ids_by_scheme"],
        scheme_nested_draws=sensitive_scheme_kwargs["scheme_nested_draws"],
        scheme_seed=sensitive_scheme_kwargs["scheme_seed"],
        scheme_minimum_refits=sensitive_scheme_kwargs["scheme_minimum_refits"],
    )

    mismatch_ids = {name: base_ids for name in robust_scheme_kwargs["refit_schemes"]}
    bad_seed_ids = list(base_ids)
    bad_seed_ids[-1] = "validation-extra"
    mismatch_ids["seed"] = tuple(bad_seed_ids)
    mismatch = assess_state_forecast_v4(
        "row-mismatch", conditional, marginal, covered, groups, blocks,
        **v2_formal_kwargs,
        refit_schemes=robust_scheme_kwargs["refit_schemes"],
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=mismatch_ids,
        refit_ids_by_scheme=robust_scheme_kwargs["refit_ids_by_scheme"],
        reference_refit_ids_by_scheme=robust_scheme_kwargs["reference_refit_ids_by_scheme"],
        scheme_nested_draws=robust_scheme_kwargs["scheme_nested_draws"],
        scheme_seed=robust_scheme_kwargs["scheme_seed"],
        scheme_minimum_refits=robust_scheme_kwargs["scheme_minimum_refits"],
    )
    direct_mismatch_v2 = assess_state_forecast_v2(
        "row-mismatch", conditional, marginal, covered, groups, blocks, **v2_formal_kwargs
    )

    v2_fragile_kwargs = dict(base_kwargs)
    v2_fragile_kwargs.update(
        refit_row_gain=fragile,
        refit_ids=ids["bootstrap"],
        reference_refit_id=ids["bootstrap"][0],
        refit_nested_draws=1200,
        minimum_refits=8,
    )
    prior_failed = assess_state_forecast_v4(
        "prior-failed-row-mismatch", conditional, marginal, covered, groups, blocks,
        **v2_fragile_kwargs,
        refit_schemes=robust_scheme_kwargs["refit_schemes"],
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=mismatch_ids,
        refit_ids_by_scheme=robust_scheme_kwargs["refit_ids_by_scheme"],
        reference_refit_ids_by_scheme=robust_scheme_kwargs["reference_refit_ids_by_scheme"],
        scheme_nested_draws=robust_scheme_kwargs["scheme_nested_draws"],
        scheme_seed=robust_scheme_kwargs["scheme_seed"],
        scheme_minimum_refits=robust_scheme_kwargs["scheme_minimum_refits"],
    )

    direct_omitted = assess_state_forecast_v3(
        "omitted", conditional, marginal, covered, groups, blocks, **v2_formal_kwargs
    )
    omitted = assess_state_forecast_v4(
        "omitted", conditional, marginal, covered, groups, blocks, **v2_formal_kwargs
    )

    train_x = np.column_stack([np.linspace(-1, 1, 60), np.sin(np.linspace(-2, 2, 60))])
    query_x = np.asarray([[0.0, 0.0], [0.5, 0.2], [3.0, 0.0]])
    direct_strict = assess_state_forecast_v3(
        "strict", conditional, marginal, covered, groups, blocks,
        **v2_formal_kwargs, **robust_scheme_kwargs,
        novelty_train_X=train_x, novelty_query_X=query_x,
    )
    strict = assess_state_forecast_v4(
        "strict", conditional, marginal, covered, groups, blocks,
        **v2_formal_kwargs,
        novelty_train_X=train_x, novelty_query_X=query_x,
        refit_schemes=permuted_schemes,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=permuted_ids,
        refit_ids_by_scheme=robust_scheme_kwargs["refit_ids_by_scheme"],
        reference_refit_ids_by_scheme=robust_scheme_kwargs["reference_refit_ids_by_scheme"],
        scheme_nested_draws=robust_scheme_kwargs["scheme_nested_draws"],
        scheme_seed=robust_scheme_kwargs["scheme_seed"],
        scheme_minimum_refits=robust_scheme_kwargs["scheme_minimum_refits"],
    )

    relabeled_base = tuple(f"case-{i:05d}" for i in range(n))
    relabeled_scheme_ids = {}
    for name, ids_for_scheme in permuted_ids.items():
        order = [base_ids.index(row_id) for row_id in ids_for_scheme]
        relabeled_scheme_ids[name] = tuple(relabeled_base[idx] for idx in order)
    relabeled = assess_state_forecast_v4(
        "strong", conditional, marginal, covered, groups, blocks,
        **v2_formal_kwargs,
        refit_schemes=permuted_schemes,
        validation_row_ids=relabeled_base,
        validation_row_ids_by_scheme=relabeled_scheme_ids,
        refit_ids_by_scheme=robust_scheme_kwargs["refit_ids_by_scheme"],
        reference_refit_ids_by_scheme=robust_scheme_kwargs["reference_refit_ids_by_scheme"],
        scheme_nested_draws=robust_scheme_kwargs["scheme_nested_draws"],
        scheme_seed=robust_scheme_kwargs["scheme_seed"],
        scheme_minimum_refits=robust_scheme_kwargs["scheme_minimum_refits"],
    )

    checks = {
        "exact_alignment_reproduces_direct_v3_dictionary_exactly": exact.v3_assessment is not None and exact.v3_assessment.as_dict() == direct_strong.as_dict(),
        "independently_permuted_schemes_reproduce_direct_v3_dictionary_exactly": permuted.v3_assessment is not None and permuted.v3_assessment.as_dict() == direct_strong.as_dict(),
        "successful_alignment_preserves_v3_certification_and_operational_status": exact.v4_certification.certification_status == direct_strong.v3_certification.certification_status and exact.v4_certification.operational_status == direct_strong.v3_certification.operational_status,
        "scheme_sensitive_alignment_preserves_v3_not_certified_result": sensitive.v3_assessment is not None and sensitive.v3_assessment.as_dict() == direct_sensitive.as_dict() and sensitive.v4_certification.certification_status == "not_certified",
        "row_mismatch_withholds_scheme_aware_v3_assessment": mismatch.v3_assessment is None and mismatch.v4_certification.v3_assessment_status == "withheld_row_mismatch",
        "row_mismatch_preserves_v2_assessment_exactly": mismatch.base_v2_assessment.as_dict() == direct_mismatch_v2.as_dict(),
        "row_mismatch_on_otherwise_certifiable_case_is_v4_unavailable": direct_mismatch_v2.extended_certification.certification_status == "certified" and mismatch.v4_certification.certification_status == "unavailable" and "heldout_row_mismatch" in mismatch.v4_certification.extended_blocking_reasons,
        "row_mismatch_does_not_rescue_prior_v2_not_certified": prior_failed.base_v2_assessment.extended_certification.certification_status == "not_certified" and prior_failed.v4_certification.certification_status == "not_certified" and "heldout_row_mismatch" in prior_failed.v4_certification.extended_blocking_reasons,
        "omitted_scheme_layer_preserves_direct_v3_result": omitted.v3_assessment is not None and omitted.v3_assessment.as_dict() == direct_omitted.as_dict() and omitted.v4_certification.row_provenance_status == "not_required",
        "strict_extrapolation_remains_warning_after_successful_alignment": strict.v3_assessment is not None and strict.v3_assessment.as_dict() == direct_strict.as_dict() and strict.v4_certification.certification_status == "certified" and strict.v4_certification.operational_status == "admitted_with_warnings" and "strict_extrapolation" in strict.v4_certification.warning_reasons,
        "consistent_row_id_relabeling_preserves_v4_result_except_alignment_labels": relabeled.v3_assessment is not None and permuted.v3_assessment is not None and relabeled.v3_assessment.as_dict() == permuted.v3_assessment.as_dict() and relabeled.v4_certification.as_dict() == permuted.v4_certification.as_dict(),
        "aggregate_confidence_score_emitted": all(not row.aggregate_confidence_score_emitted for row in (exact, permuted, sensitive, mismatch, prior_failed, omitted, strict, relabeled)),
    }

    return {
        "seed": seed,
        "row_count": n,
        "exact": exact.as_dict(),
        "permuted": permuted.as_dict(),
        "scheme_sensitive": sensitive.as_dict(),
        "row_mismatch": mismatch.as_dict(),
        "prior_failed_row_mismatch": prior_failed.as_dict(),
        "omitted_scheme": omitted.as_dict(),
        "strict_extrapolation": strict.as_dict(),
        "relabeled": relabeled.as_dict(),
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
