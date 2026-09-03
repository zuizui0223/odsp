"""Fail-closed validation for the frozen Snapshot Serengeti terminal result.

The authoritative workflow was frozen before the grouped/cross-fitted audit APIs
were added. Its numeric estimand is unchanged. This module accepts the workflow's
terminal JSON, re-checks the frozen source/rules and reconstructs the temporal
decision with explicit site-fold IDs and zero gain tolerance.

A validated terminal summary is not itself an N3 state artifact. Even a
``temporal_partition_generalizing`` result remains in N2 until an independently
specified, integrity-pinned axis-resolved state artifact exists.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from numbers import Real
from typing import Mapping

from .temporal_partition import TemporalPartitionDecision

LANE_ID = "n2_serengeti_temporal_partition_v1"
WORKFLOW_RUN_ID = 33726030526
WORKFLOW_HEAD_SHA = "d17a204527b5426d29535ef6303bc759fe52adcc"
CONSENSUS_MD5 = "5ed2d32fd09127c178cf9dca8ccfd623"
EFFORT_MD5 = "27cb42f3feaa0642b17cbde24ba15fbd"
SITE_FOLD_IDS = ("site-fold-0", "site-fold-1", "site-fold-2")
ALPHA = 0.05
GAIN_TOLERANCE = 0.0
N_PERMUTATIONS = 199
PSEUDOCOUNT = 0.5

_ALLOWED_TERMINAL_CATEGORIES = {
    "empirical_temporal_partition_unavailable",
    "temporal_partition_not_detected",
    "temporal_partition_generalizing",
    "temporal_partition_present_mixed_transfer",
    "temporal_partition_present_not_generalizing",
}


@dataclass(frozen=True)
class SerengetiTerminalReceipt:
    """Canonical audit receipt derived from one frozen workflow result."""

    schema_id: str
    lane_id: str
    workflow_run_id: int
    workflow_head_sha: str
    terminal_category: str
    outcome_opened: bool
    result_fingerprint_sha256: str
    admitted_species_count: int
    temporal_information_nats: float | None
    effective_temporal_states: float | None
    partition_information_nats: float | None
    permutation_p_value: float | None
    transfer_category: str | None
    heldout_group_ids: tuple[str, ...]
    heldout_gains: tuple[float, ...]
    axis_resolved_state_allowed_for_empirical_n3: bool
    n3_reason_code: str

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["heldout_group_ids"] = list(self.heldout_group_ids)
        payload["heldout_gains"] = list(self.heldout_gains)
        return payload


def _mapping(value: object, *, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _list(value: object, *, name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _number(value: object, *, name: str, nonnegative: bool = False) -> float:
    if not isinstance(value, Real) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    if nonnegative and number < 0:
        raise ValueError(f"{name} must be non-negative")
    return number


def _positive_int(value: object, *, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _same(left: float, right: float, *, atol: float = 1e-12) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=atol)


def _fingerprint(payload: Mapping[str, object]) -> str:
    data = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _validate_frozen_identity(result: Mapping[str, object]) -> tuple[list[object], str]:
    if result.get("lane_id") != LANE_ID:
        raise ValueError("unexpected Serengeti lane_id")

    source = _mapping(result.get("source"), name="source")
    if source.get("consensus_md5") != CONSENSUS_MD5:
        raise ValueError("consensus source checksum does not match frozen contract")
    if source.get("effort_md5") != EFFORT_MD5:
        raise ValueError("effort source checksum does not match frozen contract")
    if source.get("timezone") != "UTC+03:00_source_local_clock_no_dst":
        raise ValueError("source timezone semantics do not match frozen contract")

    rules = _mapping(result.get("frozen_rules"), name="frozen_rules")
    expected = {
        "certainty_min": 0.8,
        "independence_minutes": 30,
        "time_bins_hours": [[0, 4], [4, 8], [8, 12], [12, 16], [16, 20], [20, 24]],
        "site_fold": "sha256_siteid_mod_3",
        "min_events": 500,
        "min_sites": 20,
        "min_events_each_fold": 50,
        "permutations": N_PERMUTATIONS,
        "permutation_seed": 20260903,
        "alpha": ALPHA,
        "model_species_time_pseudocount": PSEUDOCOUNT,
    }
    for key, value in expected.items():
        if rules.get(key) != value:
            raise ValueError(f"frozen rule drift for {key}")

    admitted = _list(result.get("admitted_species"), name="admitted_species")
    if any(not isinstance(value, str) or not value.strip() for value in admitted):
        raise ValueError("admitted_species must contain non-empty strings")

    terminal = _text(result.get("terminal_category"), name="terminal_category")
    if terminal not in _ALLOWED_TERMINAL_CATEGORIES:
        raise ValueError(f"unsupported terminal_category: {terminal!r}")
    return admitted, terminal


def validate_serengeti_terminal_result(
    result: Mapping[str, object],
) -> SerengetiTerminalReceipt:
    """Validate one authoritative frozen workflow result and return an audit receipt."""

    if not isinstance(result, Mapping):
        raise ValueError("result must be an object")
    admitted, terminal = _validate_frozen_identity(result)
    fingerprint = _fingerprint(result)
    opened = result.get("outcome_opened")
    if not isinstance(opened, bool):
        raise ValueError("outcome_opened must be boolean")

    if terminal == "empirical_temporal_partition_unavailable":
        if opened:
            raise ValueError("unavailable Serengeti result cannot mark outcome_opened=true")
        _text(result.get("unavailable_reason"), name="unavailable_reason")
        if result.get("decision") is not None:
            raise ValueError("unavailable Serengeti result must not carry a decision")
        return SerengetiTerminalReceipt(
            schema_id="n2-serengeti-terminal-receipt-v1",
            lane_id=LANE_ID,
            workflow_run_id=WORKFLOW_RUN_ID,
            workflow_head_sha=WORKFLOW_HEAD_SHA,
            terminal_category=terminal,
            outcome_opened=False,
            result_fingerprint_sha256=fingerprint,
            admitted_species_count=len(admitted),
            temporal_information_nats=None,
            effective_temporal_states=None,
            partition_information_nats=None,
            permutation_p_value=None,
            transfer_category=None,
            heldout_group_ids=(),
            heldout_gains=(),
            axis_resolved_state_allowed_for_empirical_n3=False,
            n3_reason_code="temporal_lane_unavailable",
        )

    if not opened:
        raise ValueError("estimable Serengeti terminal result must mark outcome_opened=true")
    if len(admitted) < 2:
        raise ValueError("estimable Serengeti result requires at least two admitted species")

    shape = _list(
        result.get("support_shape_site_species_time"),
        name="support_shape_site_species_time",
    )
    if (
        len(shape) != 3
        or any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in shape)
        or shape[1] != len(admitted)
        or shape[2] != 6
    ):
        raise ValueError("support shape is inconsistent with the frozen site-species-time design")
    admitted_site_count = _positive_int(
        result.get("admitted_site_count"), name="admitted_site_count"
    )
    if admitted_site_count != shape[0]:
        raise ValueError("admitted_site_count disagrees with the support site dimension")
    _positive_int(result.get("admitted_event_count"), name="admitted_event_count")

    profile = _mapping(result.get("temporal_profile"), name="temporal_profile")
    if _list(profile.get("context_axes"), name="temporal_profile.context_axes") != [0]:
        raise ValueError("temporal profile context axes must equal the frozen site axis [0]")
    identity_axis = profile.get("identity_axis")
    time_axis = profile.get("time_axis")
    if not isinstance(identity_axis, int) or isinstance(identity_axis, bool) or identity_axis != 1:
        raise ValueError("temporal profile identity_axis must equal frozen species axis 1")
    if not isinstance(time_axis, int) or isinstance(time_axis, bool) or time_axis != 2:
        raise ValueError("temporal profile time_axis must equal frozen time axis 2")

    temporal_information = _number(
        profile.get("temporal_information_given_context_nats"),
        name="temporal information",
        nonnegative=True,
    )
    effective_temporal_states = _number(
        profile.get("effective_temporal_states_given_context"),
        name="effective temporal states",
        nonnegative=True,
    )
    if not _same(effective_temporal_states, math.exp(temporal_information), atol=1e-10):
        raise ValueError("effective temporal states do not equal exp(H(T|Site))")
    identity_information = _number(
        profile.get("identity_information_given_context_nats"),
        name="identity information",
        nonnegative=True,
    )
    joint_information = _number(
        profile.get("joint_identity_time_information_given_context_nats"),
        name="joint identity-time information",
        nonnegative=True,
    )
    partition_information = _number(
        profile.get("identity_time_partition_information_nats"),
        name="temporal partition information",
        nonnegative=True,
    )
    recomputed_partition = max(
        0.0,
        identity_information + temporal_information - joint_information,
    )
    if not _same(partition_information, recomputed_partition, atol=1e-10):
        raise ValueError("temporal partition information fails the frozen information identity")

    null_summary = _mapping(result.get("permutation_null"), name="permutation_null")
    null_draws = _positive_int(null_summary.get("draws"), name="permutation_null.draws")
    if null_draws != N_PERMUTATIONS:
        raise ValueError("permutation draw count does not match frozen contract")
    for metric in ("mean_nats", "q50_nats", "q95_nats", "max_nats"):
        _number(null_summary.get(metric), name=f"permutation_null.{metric}", nonnegative=True)

    gains_raw = _list(result.get("heldout_site_fold_gains"), name="heldout_site_fold_gains")
    if len(gains_raw) != len(SITE_FOLD_IDS):
        raise ValueError("Serengeti terminal result must carry exactly three site-fold gains")
    gains = tuple(_number(value, name="heldout site-fold gain") for value in gains_raw)

    decision_raw = _mapping(result.get("decision"), name="decision")
    decision_gains_raw = _list(decision_raw.get("heldout_gains"), name="decision.heldout_gains")
    decision_gains = tuple(_number(value, name="decision heldout gain") for value in decision_gains_raw)
    if len(decision_gains) != len(gains) or any(
        not _same(left, right) for left, right in zip(decision_gains, gains)
    ):
        raise ValueError("decision heldout gains disagree with top-level site-fold gains")

    gain_tolerance = decision_raw.get("gain_tolerance", GAIN_TOLERANCE)
    gain_tolerance = _number(
        gain_tolerance,
        name="decision gain_tolerance",
        nonnegative=True,
    )
    if not _same(gain_tolerance, GAIN_TOLERANCE):
        raise ValueError("Serengeti gain tolerance drifted from the frozen zero boundary")

    group_ids_raw = decision_raw.get("heldout_group_ids")
    if group_ids_raw is None:
        group_ids = SITE_FOLD_IDS
    else:
        group_ids_list = _list(group_ids_raw, name="decision.heldout_group_ids")
        group_ids = tuple(_text(value, name="heldout_group_id") for value in group_ids_list)
        if group_ids != SITE_FOLD_IDS:
            raise ValueError("heldout group IDs do not match frozen Serengeti site folds")

    decision = TemporalPartitionDecision(
        observed_partition_information_nats=_number(
            decision_raw.get("observed_partition_information_nats"),
            name="decision observed partition information",
            nonnegative=True,
        ),
        null_draw_count=_positive_int(
            decision_raw.get("null_draw_count"),
            name="decision null_draw_count",
        ),
        permutation_p_value=_number(
            decision_raw.get("permutation_p_value"),
            name="decision permutation_p_value",
            nonnegative=True,
        ),
        alpha=_number(decision_raw.get("alpha"), name="decision alpha", nonnegative=True),
        heldout_gains=gains,
        transfer_category=_text(
            decision_raw.get("transfer_category"),
            name="decision transfer_category",
        ),
        terminal_category=_text(
            decision_raw.get("terminal_category"),
            name="decision terminal_category",
        ),
        gain_tolerance=gain_tolerance,
        heldout_group_ids=group_ids,
    )
    if decision.null_draw_count != N_PERMUTATIONS:
        raise ValueError("decision null_draw_count does not match frozen contract")
    if not _same(decision.alpha, ALPHA):
        raise ValueError("decision alpha does not match frozen contract")
    if not _same(
        decision.observed_partition_information_nats,
        partition_information,
        atol=1e-10,
    ):
        raise ValueError("decision partition information disagrees with temporal profile")
    if decision.terminal_category != terminal:
        raise ValueError("root terminal_category disagrees with reconstructed decision")

    claim = _mapping(result.get("claim_boundary"), name="claim_boundary")
    for key in (
        "true_activity_niche_partition_identified",
        "interspecific_displacement_causality_identified",
        "solar_time_partition_identified",
        "bat_endpoint_reinterpreted",
    ):
        if claim.get(key) is not False:
            raise ValueError(f"claim boundary {key} must remain false")

    n3_reason = (
        "generalizing_terminal_summary_has_no_integrity_pinned_state_artifact"
        if terminal == "temporal_partition_generalizing"
        else "temporal_terminal_result_does_not_authorize_axis_resolved_n3_state"
    )
    return SerengetiTerminalReceipt(
        schema_id="n2-serengeti-terminal-receipt-v1",
        lane_id=LANE_ID,
        workflow_run_id=WORKFLOW_RUN_ID,
        workflow_head_sha=WORKFLOW_HEAD_SHA,
        terminal_category=terminal,
        outcome_opened=True,
        result_fingerprint_sha256=fingerprint,
        admitted_species_count=len(admitted),
        temporal_information_nats=temporal_information,
        effective_temporal_states=effective_temporal_states,
        partition_information_nats=partition_information,
        permutation_p_value=decision.permutation_p_value,
        transfer_category=decision.transfer_category,
        heldout_group_ids=group_ids,
        heldout_gains=gains,
        axis_resolved_state_allowed_for_empirical_n3=False,
        n3_reason_code=n3_reason,
    )
