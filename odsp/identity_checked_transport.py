"""An executable, synthetic-only BOP source→forecast→identity→gain chain.

The general ODSP source/forecast and identity modules remain separate. This
opt-in integration layer composes them *before* group gain calibration and
replays the joined provenance on both subsequent outcome access operations.

The biological identity crosswalk comes from the caller: no software can
prove it authentic, even if canonical strings are distinct. Crucially, this
adapter CANNOT be used to admit real Dryad/BOP data; it is an executable
integration test of existing method components only, not a new empirical
endpoint or a substitute for a prospectively frozen independent dataset.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

from .common_input_transport import (
    CommonInputTransport,
    calibrate_common_input_transport,
    validate_common_input_transport,
)
from .fixed_group_gain_protocol import FrozenGainCalibration, FrozenGainValidation
from .group_identity_gate import (
    GroupIdentityRecord, IdentityAdmissionGate,
    audit_frozen_group_identity_support,
)

_FIELDS = frozenset(("group_id", "entity_key", "stratum", "source", "study_cluster"))
_ROLES = ("training", "calibration", "validation")
_DECLARED_SOURCES = (
    ("training", "BOP"),
    ("calibration", "DRYAD"),
    ("validation", "DRYAD"),
)
_ALLOWED_EVIDENCE = "known_truth_synthetic_only"
_ALLOWED_CROSSWALK = "synthetic_known_truth"
_PASS = "COUNT_GATE_PASSED_EXCHANGEABILITY_NOT_PROVED"


def _record_bytes(
    groups_by_role: tuple[tuple[str, tuple[GroupIdentityRecord, ...]], ...],
    plan_sha256: str,
) -> bytes:
    return json.dumps(
        {
            "schema": 1,
            "frozen_plan_sha256": plan_sha256,
            "roles": [
                {
                    "role": role,
                    "records": [
                        {
                            "group_id": row.group_id,
                            "entity_key": row.entity_key,
                            "stratum": row.stratum,
                            "source": row.source,
                            "study_cluster": row.study_cluster,
                        }
                        for row in records
                    ],
                }
                for role, records in groups_by_role
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _capture(
    items: Sequence[Mapping[str, object]],
) -> tuple[GroupIdentityRecord, ...]:
    """Snapshot caller metadata AFTER the generic identity gate validates it."""
    result = []
    for row in items:
        if not isinstance(row, Mapping) or set(row) != _FIELDS:
            raise ValueError("identity metadata has forbidden fields")
        fields = [row[k] for k in (
            "group_id", "entity_key", "stratum", "source", "study_cluster"
        )]
        if any(
            not isinstance(x, str) or not x or x != x.strip()
            for x in fields
        ):
            raise ValueError("identity metadata must be nonempty strings")
        result.append(GroupIdentityRecord(*fields))
    return tuple(sorted(result, key=lambda x: x.group_id))


def _map(records: tuple[GroupIdentityRecord, ...]) -> list[dict[str, str]]:
    return [
        {
            "group_id": x.group_id,
            "entity_key": x.entity_key,
            "stratum": x.stratum,
            "source": x.source,
            "study_cluster": x.study_cluster,
        }
        for x in records
    ]


def _assert_training_source_strata_match(
    transport: CommonInputTransport,
    training_metadata: tuple[GroupIdentityRecord, ...],
) -> None:
    """The generic group plan lists training IDs, but not training strata.

    Reconcile those strata against the *actual fitted training source*,
    not an unsupported metadata assertion. This prevents fabricated
    training support for a target species that the predictor never fit.
    """
    source: dict[str, str] = {}
    for row in transport.forecast.training_rows:
        current = source.get(row.group_id)
        if current is not None and current != row.stratum:
            raise ValueError("training source group stratum changed within group")
        source[row.group_id] = row.stratum
    declared = {row.group_id: row.stratum for row in training_metadata}
    if source != declared:
        raise ValueError(
            "training identity metadata species/stratum differs from fitted training source"
        )


@dataclass(frozen=True)
class FrozenIdentityCheckedTransport:
    """Synthetic-only joined source, executable forecast, animal crosswalk.

    Holds the private identity records for fail-closed pre-outcome replay.
    Raw identity records are NEVER returned in as_public_dict().
    """

    transport: CommonInputTransport
    admission: IdentityAdmissionGate
    group_records_by_role: tuple[
        tuple[str, tuple[GroupIdentityRecord, ...]], ...
    ]
    source_fingerprint_sha256: str
    evidence_role: str

    def assert_replayed(self) -> None:
        """Repeat BOTH fitted-source and identity count/role/stratum checks."""
        if (
            self.evidence_role != _ALLOWED_EVIDENCE
            or not isinstance(self.transport, CommonInputTransport)
            or self.transport.protocol != "synthetic_known_truth_only"
            or self.transport.training_source != "BOP"
            or self.transport.target_source != "DRYAD"
        ):
            raise ValueError("real external BOP or Dryad sample is NOT_ADMITTED")
        self.transport.assert_replayed()
        if tuple(role for role, _ in self.group_records_by_role) != _ROLES:
            raise ValueError("frozen canonical animal metadata role roster changed")
        if any(
            not isinstance(rows, tuple)
            or any(not isinstance(row, GroupIdentityRecord) for row in rows)
            for _, rows in self.group_records_by_role
        ):
            raise ValueError("canonical animal records no longer immutable snapshots")
        plan = self.transport.forecast.plan
        source_hash = hashlib.sha256(
            _record_bytes(self.group_records_by_role, plan.digest)
        ).hexdigest()
        if source_hash != self.source_fingerprint_sha256:
            raise ValueError("canonical animal role identity snapshot changed")
        training = self.group_records_by_role[0][1]
        _assert_training_source_strata_match(self.transport, training)
        record_roles = dict(self.group_records_by_role)
        recomputed = audit_frozen_group_identity_support(
            plan,
            training_metadata=_map(record_roles["training"]),
            calibration_metadata=_map(record_roles["calibration"]),
            validation_metadata=_map(record_roles["validation"]),
            model_artifact=self.transport.forecast.model_artifact,
            reference_artifact=self.transport.forecast.reference_artifact,
            expected_source_by_role=dict(_DECLARED_SOURCES),
            group_identity_attestation=_ALLOWED_CROSSWALK,
        )
        if recomputed != self.admission or recomputed.status != _PASS:
            raise ValueError("previously admitted canonical animal group-count gate changed")

    def as_public_dict(self) -> dict[str, object]:
        self.assert_replayed()
        return {
            **self.admission.as_public_dict(),
            "integration_route": "source_model_to_forecast_to_identity_to_calibration_to_validation",
            "identity_evidence_role": self.evidence_role,
            "training_source_species_reconciled": True,
            "training_model_and_holdout_forecasts_replayed": True,
            "private_canonical_identity_records_exported": False,
            "real_BOP_or_Dryad_empirical_assessment": False,
            "historical_BOP_terminal_changed": False,
        }


def freeze_identity_checked_transport(
    transport: CommonInputTransport,
    *,
    training_metadata: Sequence[Mapping[str, object]],
    calibration_metadata: Sequence[Mapping[str, object]],
    validation_metadata: Sequence[Mapping[str, object]],
    evidence_role: str,
) -> FrozenIdentityCheckedTransport:
    """Attach canonical animal metadata BEFORE any target outcomes are read.

    A passing count is NOT proof of individual independence, biological
    sample authenticity, exchangeability or positive gain.
    """
    if evidence_role != _ALLOWED_EVIDENCE:
        raise ValueError("real external BOP or Dryad sample is NOT_ADMITTED")
    if not isinstance(transport, CommonInputTransport):
        raise ValueError("must supply managed executable CommonInputTransport")
    transport.assert_replayed()
    if transport.protocol != "synthetic_known_truth_only":
        raise ValueError("real external BOP or Dryad sample is NOT_ADMITTED")
    if transport.training_source != "BOP" or transport.target_source != "DRYAD":
        raise ValueError("unexpected training or target source role")
    captures = tuple(zip(_ROLES, (
        _capture(training_metadata),
        _capture(calibration_metadata),
        _capture(validation_metadata),
    )))
    _assert_training_source_strata_match(transport, captures[0][1])
    result = audit_frozen_group_identity_support(
        transport.forecast.plan,
        training_metadata=_map(captures[0][1]),
        calibration_metadata=_map(captures[1][1]),
        validation_metadata=_map(captures[2][1]),
        model_artifact=transport.forecast.model_artifact,
        reference_artifact=transport.forecast.reference_artifact,
        expected_source_by_role=dict(_DECLARED_SOURCES),
        group_identity_attestation=_ALLOWED_CROSSWALK,
    )
    if result.status != _PASS:
        raise ValueError(
            "identity/rank count gate HOLD: cannot open target outcome role"
        )
    obj = FrozenIdentityCheckedTransport(
        transport=transport,
        admission=result,
        group_records_by_role=captures,
        source_fingerprint_sha256=hashlib.sha256(
            _record_bytes(captures, transport.forecast.plan.digest)
        ).hexdigest(),
        evidence_role=evidence_role,
    )
    obj.assert_replayed()
    return obj


def calibrate_identity_checked_transport(
    admission: FrozenIdentityCheckedTransport,
    calibration_states_by_native_row: Mapping[str, str],
) -> FrozenGainCalibration:
    """Revalidate identity and source-to-forecast chain before calibration labels."""
    if not isinstance(admission, FrozenIdentityCheckedTransport):
        raise ValueError("frozen identity-checked transport required for calibration")
    admission.assert_replayed()
    return calibrate_common_input_transport(
        admission.transport, calibration_states_by_native_row
    )


def validate_identity_checked_transport(
    admission: FrozenIdentityCheckedTransport,
    calibration: FrozenGainCalibration,
    validation_states_by_native_row: Mapping[str, str],
) -> FrozenGainValidation:
    """Revalidate identity and model/calibration digests before test labels."""
    if not isinstance(admission, FrozenIdentityCheckedTransport):
        raise ValueError("frozen identity-checked transport required for validation")
    admission.assert_replayed()
    outcome = validate_common_input_transport(
        admission.transport, calibration, validation_states_by_native_row
    )
    declared = {row.stratum: row for row in admission.admission.strata}
    for row in outcome.strata:
        gate = declared.get(row.stratum)
        if (
            gate is None
            or row.calibration_group_count != gate.calibration_animals
            or row.validation_group_count != gate.untouched_validation_animals
            or row.finite_rank != gate.one_sided_lower_rank
            or row.vacuous
        ):
            raise ValueError("validated individual count/rank departed from frozen admission")
    if outcome.validation_group_count != admission.admission.untouched_validation_group_count:
        raise ValueError("validation units differ from admitted untouched animal groups")
    return outcome
