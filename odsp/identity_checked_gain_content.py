"""Synthetic-only canonical-animal/source-replayed exact-content integration.

This bridge composes existing frozen managed BOP->Dryad known-truth transport,
the canonical animal identity gate, and the separate #303 exact binomial
population-content procedure in that order. It is NOT a real Dryad admission,
a historical BOP RF replay, or a software proof of IID biological sampling.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from .fixed_group_gain_protocol import (
    FrozenGainValidation, _calibration_digest,
)
from .group_gain_content import (
    FrozenGroupGainContentPlan, GroupGainContentAssessment,
    _binomial_lower_tail, assess_group_gain_content,
    freeze_group_gain_content_plan,
)
from .identity_checked_transport import (
    FrozenIdentityCheckedTransport, validate_identity_checked_transport,
)


@dataclass(frozen=True)
class FrozenIdentityCheckedGainContent:
    """Pre-outcome binding of a synthetic source/identity chain to one content test."""

    identity_checked: FrozenIdentityCheckedTransport
    content_plan: FrozenGroupGainContentPlan
    identity_fingerprint_sha256: str

    def assert_replayed(self) -> None:
        if not isinstance(self.identity_checked, FrozenIdentityCheckedTransport):
            raise ValueError("identity-checked managed transport required")
        # This always precedes reading any outcome values.
        self.identity_checked.assert_replayed()
        if (
            self.identity_fingerprint_sha256
            != self.identity_checked.source_fingerprint_sha256
        ):
            raise ValueError("content binding identity fingerprint changed")
        plan = self.identity_checked.transport.forecast.plan
        policy = self.content_plan
        if not isinstance(policy, FrozenGroupGainContentPlan):
            raise ValueError("frozen content policy required")
        cal_strata = {row.stratum for row in plan.calibration_rows}
        val_strata = {row.stratum for row in plan.validation_rows}
        if cal_strata != {policy.stratum} or val_strata != {policy.stratum}:
            raise ValueError(
                "content integration requires exactly one target calibration/validation stratum"
            )
        expected = freeze_group_gain_content_plan(
            plan, stratum=policy.stratum,
            sampling_assumption=policy.sampling_assumption,
            model_artifact=self.identity_checked.transport.forecast.model_artifact,
            reference_artifact=self.identity_checked.transport.forecast.reference_artifact,
            minimum_positive_fraction=policy.minimum_positive_fraction,
            confidence_level=policy.confidence_level,
            gain_threshold=policy.gain_threshold,
        )
        if expected != policy:
            raise ValueError("bound content policy or forecast roster changed")
        matching = [
            s for s in self.identity_checked.admission.strata
            if s.stratum == policy.stratum
        ]
        if (
            len(matching) != 1
            or matching[0].calibration_animals != policy.calibration_group_count
            or matching[0].untouched_validation_animals != policy.validation_group_count
        ):
            raise ValueError("canonical animal counts differ from content policy")

    def as_public_dict(self) -> dict[str, object]:
        self.assert_replayed()
        return {
            **self.content_plan.as_public_dict(),
            "integration": "synthetic_source_to_artifact_to_forecast_to_identity_to_exact_content",
            "identity_crosswalk_replayed": True,
            "managed_model_and_forecasts_replayed": True,
            "biological_iid_sampling_proven_by_software": False,
            "original_BOP_RF_replayed": False,
            "real_Dryad_external_candidate_admitted": False,
            "original_BOP_empirical_terminal": "empirical_state_prediction_mixed",
            "private_animal_identity_exported": False,
        }


@dataclass(frozen=True)
class IdentityCheckedGainContentAssessment:
    """Bind a content test to exactly the admitted synthetic source and policy."""

    binding: FrozenIdentityCheckedGainContent
    content: GroupGainContentAssessment

    def assert_replayed(self) -> None:
        self.binding.assert_replayed()
        if (
            not isinstance(self.content, GroupGainContentAssessment)
            or self.content.content_plan != self.binding.content_plan
        ):
            raise ValueError("content assessment is not for this frozen binding")
        cal = self.content.calibration
        plan = self.binding.identity_checked.transport.forecast.plan
        if cal.plan_sha256 != plan.digest or cal.calibration_sha256 != _calibration_digest(
            plan.digest, cal.gains
        ):
            raise ValueError("content calibration scores or digest changed")
        expected_groups = {row.group_id for row in plan.calibration_rows}
        if (
            len(cal.gains) != len(expected_groups)
            or {g.group_id for g in cal.gains} != expected_groups
            or any(
                g.stratum != self.binding.content_plan.stratum
                or not math.isfinite(g.weighted_mean_gain)
                for g in cal.gains
            )
        ):
            raise ValueError("content calibration groups differ from admitted roster")
        failures = sum(
            g.weighted_mean_gain <= self.binding.content_plan.gain_threshold
            for g in cal.gains
        )
        expected_tail = _binomial_lower_tail(
            len(cal.gains), failures,
            self.binding.content_plan.minimum_positive_fraction,
        )
        if (
            failures != self.content.nonpositive_group_count
            or expected_tail != self.content.exact_p_value
        ):
            raise ValueError("exact content decision disagrees with frozen group scores")

    def as_public_dict(self) -> dict[str, object]:
        self.assert_replayed()
        return {
            **self.content.as_public_dict(),
            "integration": "synthetic_canonical_identity_and_managed_forecast_replayed",
            "real_cross_source_animal_gain_result": False,
            "identity_and_iid_sampling_verified_by_software": False,
        }


def freeze_identity_checked_gain_content(
    identity_checked: FrozenIdentityCheckedTransport,
    *,
    stratum: str,
    sampling_assumption: str,
    minimum_positive_fraction: object = "0.9",
    confidence_level: object = "0.95",
    gain_threshold: object = 0,
) -> FrozenIdentityCheckedGainContent:
    """Freeze content policy after identity/source admission and before any labels."""
    if not isinstance(identity_checked, FrozenIdentityCheckedTransport):
        raise ValueError("identity-checked managed transport required")
    identity_checked.assert_replayed()
    model = identity_checked.transport.forecast
    policy = freeze_group_gain_content_plan(
        model.plan,
        stratum=stratum,
        sampling_assumption=sampling_assumption,
        model_artifact=model.model_artifact,
        reference_artifact=model.reference_artifact,
        minimum_positive_fraction=minimum_positive_fraction,
        confidence_level=confidence_level,
        gain_threshold=gain_threshold,
    )
    binding = FrozenIdentityCheckedGainContent(
        identity_checked=identity_checked,
        content_plan=policy,
        identity_fingerprint_sha256=identity_checked.source_fingerprint_sha256,
    )
    binding.assert_replayed()
    return binding


def assess_identity_checked_gain_content(
    binding: FrozenIdentityCheckedGainContent,
    calibration_states_by_native_row: Mapping[str, str],
) -> IdentityCheckedGainContentAssessment:
    """Recheck all upstream gates; never read held-out or wrong-role label values."""
    if not isinstance(binding, FrozenIdentityCheckedGainContent):
        raise ValueError("frozen identity/content binding required")
    binding.assert_replayed()
    if not binding.content_plan.count_allows_support:
        raise ValueError("insufficient independent calibration groups for content claim")
    if not isinstance(calibration_states_by_native_row, Mapping):
        raise ValueError("calibration outcomes must be a mapping")
    model = binding.identity_checked.transport.forecast
    raw_ids = []
    for row in model.plan.calibration_rows:
        prefix, delimiter, native_id = row.row_id.partition(":")
        if prefix != "DRYAD" or delimiter != ":" or not native_id:
            raise ValueError("calibration rows lack the frozen DRYAD native ID namespace")
        raw_ids.append(native_id)
    if len(set(raw_ids)) != len(raw_ids) or set(calibration_states_by_native_row) != set(raw_ids):
        raise ValueError("native calibration row IDs must match exactly before label access")
    # Only the already admitted calibration role is accessed, exactly once each.
    frozen_values = {
        "DRYAD:" + native_id: calibration_states_by_native_row[native_id]
        for native_id in raw_ids
    }
    content = assess_group_gain_content(
        binding.content_plan, model.plan, frozen_values,
        model_artifact=model.model_artifact,
        reference_artifact=model.reference_artifact,
    )
    result = IdentityCheckedGainContentAssessment(binding, content)
    result.assert_replayed()
    return result


def validate_identity_checked_gain_content(
    binding: FrozenIdentityCheckedGainContent,
    assessment: IdentityCheckedGainContentAssessment,
    validation_states_by_native_row: Mapping[str, str],
) -> FrozenGainValidation:
    """Validate unchanged calibration on reserved synthetic test animals only."""
    if not isinstance(binding, FrozenIdentityCheckedGainContent):
        raise ValueError("frozen identity/content binding required")
    binding.assert_replayed()
    if not isinstance(assessment, IdentityCheckedGainContentAssessment) or assessment.binding != binding:
        raise ValueError("content assessment belongs to another identity binding")
    assessment.assert_replayed()
    return validate_identity_checked_transport(
        binding.identity_checked,
        assessment.content.calibration,
        validation_states_by_native_row,
    )
