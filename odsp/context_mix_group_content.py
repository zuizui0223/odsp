"""Mixture-robust group content for the synthetic identity-checked BOP bridge.

Reweight only the two mean-solar-clock contexts, not records within each
context. Positive robust gain is equivalent to both context means being
strictly positive in the SAME animal. Not detection-bias identification.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
import json
import math

from .group_gain_content import _binomial_lower_tail, _upper_float
from .identity_checked_transport import FrozenIdentityCheckedTransport


ROBUST_IID = "iid_context_mix_robust_group_indicators_within_prespecified_stratum"
CONTENT = Fraction(9, 10)
ALPHA = Fraction(1, 20)


@dataclass(frozen=True)
class ContextMixGain:
    """Exact accumulation of the given binary log deltas and binary weights."""
    context0: Fraction
    context1: Fraction
    observed: Fraction

    @property
    def balanced(self) -> Fraction:
        return (self.context0 + self.context1) / 2

    @property
    def worst(self) -> Fraction:
        return min(self.context0, self.context1)

    @property
    def best(self) -> Fraction:
        return max(self.context0, self.context1)


def _summarize_context_masses(rows) -> ContextMixGain:
    sums = [Fraction(0), Fraction(0)]
    weights = [Fraction(0), Fraction(0)]
    for context, log_delta, weight in rows:
        if type(context) is not int or context not in (0, 1):
            raise ValueError("context must be exact integer 0 or 1")
        if not math.isfinite(log_delta) or not math.isfinite(weight) or weight <= 0:
            raise ValueError("finite log deltas and positive finite weights required")
        w = Fraction.from_float(float(weight))
        weights[context] += w
        sums[context] += w * Fraction.from_float(float(log_delta))
    if not all(weights):
        raise ValueError("both contexts must have observed support")
    return ContextMixGain(
        sums[0] / weights[0], sums[1] / weights[1],
        sum(sums) / sum(weights),
    )


def _role_counts(rows, features, stratum, minimum_rows):
    by_id = {r.row_id: r for r in features}
    if len(by_id) != len(features) or set(by_id) != {r.row_id for r in rows}:
        raise ValueError("feature roster differs from frozen forecast role")
    count = Counter()
    groups = set()
    for row in rows:
        feature = by_id[row.row_id]
        if (
            row.stratum != stratum or feature.stratum != stratum
            or feature.group_id != row.group_id or feature.weight != row.weight
            or type(feature.context) is not int or feature.context not in (0, 1)
        ):
            raise ValueError("one exact target stratum and matching context features required")
        groups.add(row.group_id)
        count[row.group_id, feature.context] += 1
    complete = sum(
        all(count[g, c] >= minimum_rows for c in (0, 1)) for g in groups
    )
    return len(groups), complete


@dataclass(frozen=True)
class FrozenContextMixContentPlan:
    identity_checked: FrozenIdentityCheckedTransport
    stratum: str
    minimum_rows_per_context: int
    sampling_assumption: str
    calibration_groups: int
    calibration_complete_groups: int
    validation_groups: int
    validation_complete_groups: int
    digest: str

    def _canonical(self):
        return {
            "schema_version": 1,
            "forecast_plan_sha256": self.identity_checked.transport.forecast.plan.digest,
            "private_identity_sha256": self.identity_checked.source_fingerprint_sha256,
            "stratum": self.stratum,
            "minimum_rows_per_context": self.minimum_rows_per_context,
            "sampling_assumption": self.sampling_assumption,
            "calibration_groups": self.calibration_groups,
            "calibration_complete_groups": self.calibration_complete_groups,
            "validation_groups": self.validation_groups,
            "validation_complete_groups": self.validation_complete_groups,
            "content_fraction": str(CONTENT),
            "alpha": str(ALPHA),
            "gain_threshold": 0,
            "context": "binary_mean_solar_clock_06_18",
            "mixture": "all_context1_weights_in_closed_unit_interval",
        }

    @property
    def structural_status(self):
        if not self.calibration_groups or not self.validation_groups:
            return "HOLD_EMPTY_TARGET_ROLE"
        if (
            self.calibration_complete_groups != self.calibration_groups
            or self.validation_complete_groups != self.validation_groups
        ):
            return "HOLD_INCOMPLETE_CONTEXT_SUPPORT"
        if CONTENT ** self.calibration_groups > ALPHA:
            return "HOLD_INSUFFICIENT_GROUPS_FOR_CONTENT"
        return "COUNT_AND_CONTEXT_FEASIBLE_ONLY"

    def assert_replayed(self):
        rebuilt = freeze_context_mix_content(
            self.identity_checked, stratum=self.stratum,
            minimum_rows_per_context=self.minimum_rows_per_context,
            sampling_assumption=self.sampling_assumption,
        )
        if rebuilt != self:
            raise ValueError("context mixture policy or frozen support changed")

    def _summary(self):
        return {
            "schema_version": 1,
            "stage": "synthetic_context_mix_robust_group_content",
            "status": self.structural_status,
            "stratum": self.stratum,
            "context": "binary_mean_solar_clock_06_18_not_astronomical_daylight",
            "minimum_rows_per_context": self.minimum_rows_per_context,
            "calibration_groups": self.calibration_groups,
            "calibration_complete_groups": self.calibration_complete_groups,
            "reserved_validation_groups": self.validation_groups,
            "reserved_validation_complete_groups": self.validation_complete_groups,
            "minimum_robust_positive_fraction": str(CONTENT),
            "one_sided_alpha": str(ALPHA),
            "sampling_assumption": self.sampling_assumption,
            "iid_or_biological_independence_verified_by_software": False,
            "within_context_selection_bias_corrected": False,
            "real_dryad_admitted": False,
            "original_bop_terminal_changed": False,
        }

    def as_public_dict(self):
        self.assert_replayed()
        return {
            **self._summary(),
            "calibration_labels_accessed_by_preflight": False,
            "validation_labels_accessed": False,
        }


def freeze_context_mix_content(
    identity_checked: FrozenIdentityCheckedTransport, *, stratum: str,
    minimum_rows_per_context: int,
    sampling_assumption: str,
) -> FrozenContextMixContentPlan:
    """Freeze one context-mix test before any target outcomes."""
    if not isinstance(identity_checked, FrozenIdentityCheckedTransport):
        raise ValueError("synthetic identity-checked managed transport required")
    identity_checked.assert_replayed()
    if sampling_assumption != ROBUST_IID:
        raise ValueError("explicit IID robust group indicator assumption required")
    if not isinstance(stratum, str) or not stratum or stratum != stratum.strip():
        raise ValueError("one explicit target stratum required")
    if type(minimum_rows_per_context) is not int or minimum_rows_per_context < 1:
        raise ValueError("minimum rows per context must be a positive integer")
    model = identity_checked.transport.forecast
    if (
        {r.stratum for r in model.plan.calibration_rows} != {stratum}
        or {r.stratum for r in model.plan.validation_rows} != {stratum}
    ):
        raise ValueError("requires exactly one target calibration/validation stratum")
    cal, cal_ok = _role_counts(
        model.plan.calibration_rows, model.calibration_features,
        stratum, minimum_rows_per_context,
    )
    val, val_ok = _role_counts(
        model.plan.validation_rows, model.validation_features,
        stratum, minimum_rows_per_context,
    )
    admitted = [s for s in identity_checked.admission.strata if s.stratum == stratum]
    if len(admitted) != 1 or (
        admitted[0].calibration_animals != cal
        or admitted[0].untouched_validation_animals != val
    ):
        raise ValueError("context support group counts differ from identity admission")
    result = FrozenContextMixContentPlan(
        identity_checked, stratum, minimum_rows_per_context, sampling_assumption,
        cal, cal_ok, val, val_ok, "",
    )
    digest = hashlib.sha256(json.dumps(
        result._canonical(), sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")).hexdigest()
    return replace(result, digest=digest)


def assess_context_mix_content(
    plan: FrozenContextMixContentPlan,
    calibration_states_by_native_row: Mapping[str, str],
) -> dict[str, object]:
    """Calibration-only aggregate sensitivity and one exact robust-content test.

    The natural and balanced positive counts are descriptive, not separately
    tested population-content claims. No reserved validation labels accepted.
    """
    if not isinstance(plan, FrozenContextMixContentPlan):
        raise ValueError("frozen context mixture content plan required")
    plan.assert_replayed()
    if plan.structural_status != "COUNT_AND_CONTEXT_FEASIBLE_ONLY":
        raise ValueError(plan.structural_status)
    if not isinstance(calibration_states_by_native_row, Mapping):
        raise ValueError("calibration outcomes must be a mapping")
    model = plan.identity_checked.transport.forecast
    features = {r.row_id: r for r in model.calibration_features}
    rows = model.plan.calibration_rows
    ids = []
    for row in rows:
        prefix, separator, native = row.row_id.partition(":")
        if prefix != "DRYAD" or separator != ":" or not native:
            raise ValueError("invalid frozen native row namespace")
        ids.append(native)
    if len(set(ids)) != len(ids) or set(calibration_states_by_native_row) != set(ids):
        raise ValueError("exact frozen native calibration row IDs required before label access")
    values = {key: calibration_states_by_native_row[key] for key in ids}
    index = {label: i for i, label in enumerate(model.plan.classes)}
    by_group = {}
    for row, native in zip(rows, ids):
        label = values[native]
        if not isinstance(label, str) or label not in index:
            raise ValueError("observed state absent from frozen classes")
        i = index[label]
        gain = math.log(row.conditional[i]) - math.log(row.reference[i])
        by_group.setdefault(row.group_id, []).append(
            (features[row.row_id].context, gain, row.weight)
        )
    scores = tuple(_summarize_context_masses(rows) for rows in by_group.values())
    n = len(scores)
    if n != plan.calibration_groups:
        raise ValueError("scored group count differs from frozen roster")
    robust = sum(g.worst > 0 for g in scores)
    p = _binomial_lower_tail(n, n - robust, CONTENT)
    return {
        **plan._summary(),
        "status": "SUPPORTED_IF_ROBUST_IID_HOLDS" if p <= ALPHA else "NOT_SUPPORTED",
        "observed_positive_groups": sum(g.observed > 0 for g in scores),
        "equal_context_positive_groups": sum(g.balanced > 0 for g in scores),
        "context0_positive_groups": sum(g.context0 > 0 for g in scores),
        "context1_positive_groups": sum(g.context1 > 0 for g in scores),
        "all_mixtures_positive_groups": robust,
        "mixture_sensitive_groups": sum(g.worst <= 0 < g.best for g in scores),
        "equal_animal_mean_observed_gain": float(sum(g.observed for g in scores) / n),
        "equal_animal_mean_balanced_gain": float(sum(g.balanced for g in scores) / n),
        "equal_animal_mean_worst_mixture_gain": float(sum(g.worst for g in scores) / n),
        "robust_content_p_value_upper_bound": _upper_float(p),
        "robust_content_supported_if_iid": p <= ALPHA,
        "decision_uses_exact_binary_delta_accumulation_and_exact_binomial_tail": True,
        "raw_and_balanced_counts_are_descriptive_only": True,
        "calibration_labels_accessed": True,
        "validation_labels_accessed": False,
        "rank_bound_or_unseen_context_gain_claimed": False,
    }
