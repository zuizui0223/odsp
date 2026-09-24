"""Portable N2 -> N3 handoff for population-level information-transfer value.

This payload is deliberately not a state artifact and not a survey-priority map.
It carries the expected and uncertainty-bounded value of adding information
levels so N3/EOG can combine that evidence with downstream reachability/world
structure. Spatial survey-action ownership remains with N4/ACSP.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from numbers import Real
import re
from typing import Mapping, Sequence


SCHEMA_ID = "n2-to-n3-transfer-value-payload-v1"
PROGRAM_ID = "niche-to-survey-four-chapter-v1"
PRODUCER_REPOSITORY = "zuizui0223/odsp"
TARGET_CHAPTER = "N3"
TARGET_SYSTEM = "EOG"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_STATUS = {"positive", "uncertain", "nonpositive"}


@dataclass(frozen=True)
class TransferValueStep:
    lower_level: str
    upper_level: str
    expected_gain: float
    mean_interval_lower: float
    mean_interval_upper: float
    mean_status: str
    conservative_mean_value: float
    positive_group_fraction: float
    positive_fraction_lower: float
    positive_fraction_lower_method: str
    prediction_lower: float | None
    prediction_upper: float | None
    prediction_method: str | None
    empirical_p10: float
    empirical_p50: float
    empirical_p90: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TransferValueHandoff:
    schema_id: str
    program_id: str
    producer_chapter: str
    producer_repository: str
    target_chapter: str
    target_system: str
    evidence_id: str
    group_semantics: str
    population_cluster_semantics: str | None
    estimand: str
    gain_tolerance: float
    score_kind: str
    score_name: str
    score_unit: str
    total_value: TransferValueStep
    steps: tuple[TransferValueStep, ...]
    source_population_fingerprint: str
    source_receipt: str | None
    source_contract: str | None
    fingerprint: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "program_id": self.program_id,
            "producer": {
                "chapter": self.producer_chapter,
                "repository": self.producer_repository,
            },
            "target": {
                "chapter": self.target_chapter,
                "system": self.target_system,
                "role": "information_transfer_value_for_downstream_reachability",
            },
            "evidence_id": self.evidence_id,
            "semantics": {
                "group": self.group_semantics,
                "population_cluster": self.population_cluster_semantics,
                "estimand": self.estimand,
                "gain_tolerance": self.gain_tolerance,
                "score": {
                    "kind": self.score_kind,
                    "name": self.score_name,
                    "unit": self.score_unit,
                    "orientation": "higher_is_better",
                },
            },
            "total_value": self.total_value.as_dict(),
            "steps": [step.as_dict() for step in self.steps],
            "boundary": {
                "is_state_artifact": False,
                "authorizes_state_promotion": False,
                "authorizes_spatial_patch_ranking": False,
                "authorizes_survey_site_selection": False,
                "authorizes_n4_action": False,
                "n4_survey_action_owner": "ACSP",
                "interpretation": (
                    "values quantify held-out predictive value of additional "
                    "information across groups; N3 may combine them with reachability "
                    "or world structure, but this payload alone cannot rank places"
                ),
            },
            "provenance": {
                "source_population_fingerprint": self.source_population_fingerprint,
                "source_receipt": self.source_receipt,
                "source_contract": self.source_contract,
            },
            "fingerprint": self.fingerprint,
        }


def _clean_text(value: object, *, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _optional_text(value: object, *, name: str) -> str | None:
    if value is None:
        return None
    return _clean_text(value, name=name)


def _finite_number(value: object, *, name: str) -> float:
    if not isinstance(value, Real) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _optional_finite_number(value: object, *, name: str) -> float | None:
    if value is None:
        return None
    return _finite_number(value, name=name)


def _canonical_fingerprint(payload: Mapping[str, object]) -> str:
    data = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def population_result_fingerprint(population_result: Mapping[str, object]) -> str:
    """Return a canonical SHA-256 fingerprint of one serialized population result."""

    if not isinstance(population_result, Mapping):
        raise ValueError("population_result must be an object")
    return _canonical_fingerprint(dict(population_result))


def _parse_step(value: Mapping[str, object], *, name: str) -> TransferValueStep:
    lower = _clean_text(value.get("lower_level"), name=f"{name}.lower_level")
    upper = _clean_text(value.get("upper_level"), name=f"{name}.upper_level")
    if lower == upper:
        raise ValueError(f"{name} lower_level and upper_level must differ")

    expected = _finite_number(value.get("mean_gain"), name=f"{name}.mean_gain")
    interval_lower = _finite_number(
        value.get("mean_gain_lower"), name=f"{name}.mean_gain_lower"
    )
    interval_upper = _finite_number(
        value.get("mean_gain_upper"), name=f"{name}.mean_gain_upper"
    )
    if interval_lower > interval_upper:
        raise ValueError(f"{name} mean interval is reversed")

    status = _clean_text(value.get("mean_gain_status"), name=f"{name}.mean_gain_status")
    if status not in _ALLOWED_STATUS:
        raise ValueError(f"{name} has unsupported mean_gain_status: {status!r}")
    if status == "positive" and not interval_lower > 0.0:
        raise ValueError(f"{name} positive status requires lower interval bound > 0")
    if status == "nonpositive" and not interval_upper <= 0.0:
        raise ValueError(f"{name} nonpositive status requires upper interval bound <= 0")
    if status == "uncertain" and not interval_lower <= 0.0 < interval_upper:
        raise ValueError(f"{name} uncertain status requires interval crossing zero")

    fraction = _finite_number(
        value.get("positive_group_fraction"),
        name=f"{name}.positive_group_fraction",
    )
    fraction_lower = _finite_number(
        value.get("positive_fraction_lower"),
        name=f"{name}.positive_fraction_lower",
    )
    if not 0.0 <= fraction_lower <= fraction <= 1.0:
        raise ValueError(f"{name} positive fractions must satisfy 0 <= lower <= fraction <= 1")

    method = _clean_text(
        value.get("positive_fraction_lower_method"),
        name=f"{name}.positive_fraction_lower_method",
    )

    prediction_lower = _optional_finite_number(
        value.get("prediction_lower"), name=f"{name}.prediction_lower"
    )
    prediction_upper = _optional_finite_number(
        value.get("prediction_upper"), name=f"{name}.prediction_upper"
    )
    prediction_method = _optional_text(
        value.get("prediction_method"), name=f"{name}.prediction_method"
    )
    if (prediction_lower is None) != (prediction_upper is None):
        raise ValueError(f"{name} prediction interval must provide both bounds or neither")
    if prediction_lower is not None and prediction_upper is not None and prediction_lower > prediction_upper:
        raise ValueError(f"{name} prediction interval is reversed")
    if prediction_lower is None and prediction_method is not None:
        raise ValueError(f"{name} prediction_method requires a prediction interval")

    p10 = _finite_number(value.get("empirical_p10"), name=f"{name}.empirical_p10")
    p50 = _finite_number(value.get("empirical_p50"), name=f"{name}.empirical_p50")
    p90 = _finite_number(value.get("empirical_p90"), name=f"{name}.empirical_p90")
    if not p10 <= p50 <= p90:
        raise ValueError(f"{name} empirical quantiles must be ordered")

    return TransferValueStep(
        lower_level=lower,
        upper_level=upper,
        expected_gain=expected,
        mean_interval_lower=interval_lower,
        mean_interval_upper=interval_upper,
        mean_status=status,
        conservative_mean_value=max(0.0, interval_lower),
        positive_group_fraction=fraction,
        positive_fraction_lower=fraction_lower,
        positive_fraction_lower_method=method,
        prediction_lower=prediction_lower,
        prediction_upper=prediction_upper,
        prediction_method=prediction_method,
        empirical_p10=p10,
        empirical_p50=p50,
        empirical_p90=p90,
    )



def _parse_handoff_step(
    value: Mapping[str, object],
    *,
    name: str,
) -> TransferValueStep:
    lower = _clean_text(value.get("lower_level"), name=f"{name}.lower_level")
    upper = _clean_text(value.get("upper_level"), name=f"{name}.upper_level")
    if lower == upper:
        raise ValueError(f"{name} lower_level and upper_level must differ")

    expected = _finite_number(
        value.get("expected_gain"), name=f"{name}.expected_gain"
    )
    interval_lower = _finite_number(
        value.get("mean_interval_lower"), name=f"{name}.mean_interval_lower"
    )
    interval_upper = _finite_number(
        value.get("mean_interval_upper"), name=f"{name}.mean_interval_upper"
    )
    if interval_lower > interval_upper:
        raise ValueError(f"{name} mean interval is reversed")

    status = _clean_text(value.get("mean_status"), name=f"{name}.mean_status")
    if status not in _ALLOWED_STATUS:
        raise ValueError(f"{name} has unsupported mean_status: {status!r}")
    if status == "positive" and not interval_lower > 0.0:
        raise ValueError(f"{name} positive status requires lower interval bound > 0")
    if status == "nonpositive" and not interval_upper <= 0.0:
        raise ValueError(f"{name} nonpositive status requires upper interval bound <= 0")
    if status == "uncertain" and not interval_lower <= 0.0 < interval_upper:
        raise ValueError(f"{name} uncertain status requires interval crossing zero")

    conservative = _finite_number(
        value.get("conservative_mean_value"),
        name=f"{name}.conservative_mean_value",
    )
    expected_conservative = max(0.0, interval_lower)
    if not math.isclose(conservative, expected_conservative, rel_tol=0.0, abs_tol=1e-15):
        raise ValueError(
            f"{name} conservative_mean_value must equal max(0, mean_interval_lower)"
        )

    fraction = _finite_number(
        value.get("positive_group_fraction"),
        name=f"{name}.positive_group_fraction",
    )
    fraction_lower = _finite_number(
        value.get("positive_fraction_lower"),
        name=f"{name}.positive_fraction_lower",
    )
    if not 0.0 <= fraction_lower <= fraction <= 1.0:
        raise ValueError(
            f"{name} positive fractions must satisfy 0 <= lower <= fraction <= 1"
        )
    method = _clean_text(
        value.get("positive_fraction_lower_method"),
        name=f"{name}.positive_fraction_lower_method",
    )

    prediction_lower = _optional_finite_number(
        value.get("prediction_lower"), name=f"{name}.prediction_lower"
    )
    prediction_upper = _optional_finite_number(
        value.get("prediction_upper"), name=f"{name}.prediction_upper"
    )
    prediction_method = _optional_text(
        value.get("prediction_method"), name=f"{name}.prediction_method"
    )
    if (prediction_lower is None) != (prediction_upper is None):
        raise ValueError(
            f"{name} prediction interval must provide both bounds or neither"
        )
    if (
        prediction_lower is not None
        and prediction_upper is not None
        and prediction_lower > prediction_upper
    ):
        raise ValueError(f"{name} prediction interval is reversed")
    if prediction_lower is None and prediction_method is not None:
        raise ValueError(f"{name} prediction_method requires a prediction interval")

    p10 = _finite_number(value.get("empirical_p10"), name=f"{name}.empirical_p10")
    p50 = _finite_number(value.get("empirical_p50"), name=f"{name}.empirical_p50")
    p90 = _finite_number(value.get("empirical_p90"), name=f"{name}.empirical_p90")
    if not p10 <= p50 <= p90:
        raise ValueError(f"{name} empirical quantiles must be ordered")

    return TransferValueStep(
        lower_level=lower,
        upper_level=upper,
        expected_gain=expected,
        mean_interval_lower=interval_lower,
        mean_interval_upper=interval_upper,
        mean_status=status,
        conservative_mean_value=conservative,
        positive_group_fraction=fraction,
        positive_fraction_lower=fraction_lower,
        positive_fraction_lower_method=method,
        prediction_lower=prediction_lower,
        prediction_upper=prediction_upper,
        prediction_method=prediction_method,
        empirical_p10=p10,
        empirical_p50=p50,
        empirical_p90=p90,
    )


def _validate_chain(total: TransferValueStep, steps: Sequence[TransferValueStep]) -> None:
    if not steps:
        raise ValueError("population_result must contain at least one adjacent step")
    if steps[0].lower_level != total.lower_level:
        raise ValueError("first step must start at total lower_level")
    if steps[-1].upper_level != total.upper_level:
        raise ValueError("last step must end at total upper_level")
    for previous, current in zip(steps, steps[1:]):
        if previous.upper_level != current.lower_level:
            raise ValueError("population_result steps must form a contiguous information chain")


def build_population_transfer_value_handoff(
    *,
    evidence_id: str,
    population_result: Mapping[str, object],
    group_semantics: str,
    population_cluster_semantics: str | None = None,
    score_kind: str,
    score_name: str,
    score_unit: str,
    source_receipt: str | None = None,
    source_contract: str | None = None,
) -> TransferValueHandoff:
    """Convert one ODSP population result into a bounded N2 -> N3 value payload."""

    evidence_id = _clean_text(evidence_id, name="evidence_id")
    group_semantics = _clean_text(group_semantics, name="group_semantics")
    population_cluster_semantics = _optional_text(
        population_cluster_semantics, name="population_cluster_semantics"
    )
    score_kind = _clean_text(score_kind, name="score_kind")
    if score_kind not in {"log", "other_proper"}:
        raise ValueError("score_kind must be log or other_proper")
    score_name = _clean_text(score_name, name="score_name")
    score_unit = _clean_text(score_unit, name="score_unit")
    source_receipt = _optional_text(source_receipt, name="source_receipt")
    source_contract = _optional_text(source_contract, name="source_contract")

    estimand = _clean_text(population_result.get("estimand"), name="population_result.estimand")
    if estimand != "equal_weight_mean_gain_across_groups":
        raise ValueError("transfer-value payload v1 requires equal_weight_mean_gain_across_groups")
    if population_result.get("familywise_confirmatory_claim") is not False:
        raise ValueError("transfer-value payload v1 requires familywise_confirmatory_claim=false")
    gain_tolerance = _finite_number(
        population_result.get("gain_tolerance"),
        name="population_result.gain_tolerance",
    )
    if gain_tolerance < 0.0:
        raise ValueError("population_result.gain_tolerance must be non-negative")

    total_raw = population_result.get("total_gain")
    steps_raw = population_result.get("steps")
    if not isinstance(total_raw, Mapping):
        raise ValueError("population_result.total_gain must be an object")
    if not isinstance(steps_raw, list) or not steps_raw:
        raise ValueError("population_result.steps must be a non-empty list")
    if not all(isinstance(value, Mapping) for value in steps_raw):
        raise ValueError("every population_result step must be an object")

    total = _parse_step(total_raw, name="population_result.total_gain")
    steps = tuple(
        _parse_step(value, name=f"population_result.steps[{index}]")
        for index, value in enumerate(steps_raw)
    )
    _validate_chain(total, steps)

    source_fingerprint = population_result_fingerprint(population_result)
    core = {
        "schema_id": SCHEMA_ID,
        "program_id": PROGRAM_ID,
        "producer": {"chapter": "N2", "repository": PRODUCER_REPOSITORY},
        "target": {
            "chapter": TARGET_CHAPTER,
            "system": TARGET_SYSTEM,
            "role": "information_transfer_value_for_downstream_reachability",
        },
        "evidence_id": evidence_id,
        "semantics": {
            "group": group_semantics,
            "population_cluster": population_cluster_semantics,
            "estimand": estimand,
            "gain_tolerance": gain_tolerance,
            "score": {
                "kind": score_kind,
                "name": score_name,
                "unit": score_unit,
                "orientation": "higher_is_better",
            },
        },
        "total_value": total.as_dict(),
        "steps": [step.as_dict() for step in steps],
        "boundary": {
            "is_state_artifact": False,
            "authorizes_state_promotion": False,
            "authorizes_spatial_patch_ranking": False,
            "authorizes_survey_site_selection": False,
            "authorizes_n4_action": False,
            "n4_survey_action_owner": "ACSP",
            "interpretation": (
                "values quantify held-out predictive value of additional information "
                "across groups; N3 may combine them with reachability or world structure, "
                "but this payload alone cannot rank places"
            ),
        },
        "provenance": {
            "source_population_fingerprint": source_fingerprint,
            "source_receipt": source_receipt,
            "source_contract": source_contract,
        },
    }
    fingerprint = _canonical_fingerprint(core)
    return TransferValueHandoff(
        schema_id=SCHEMA_ID,
        program_id=PROGRAM_ID,
        producer_chapter="N2",
        producer_repository=PRODUCER_REPOSITORY,
        target_chapter=TARGET_CHAPTER,
        target_system=TARGET_SYSTEM,
        evidence_id=evidence_id,
        group_semantics=group_semantics,
        population_cluster_semantics=population_cluster_semantics,
        estimand=estimand,
        gain_tolerance=gain_tolerance,
        score_kind=score_kind,
        score_name=score_name,
        score_unit=score_unit,
        total_value=total,
        steps=steps,
        source_population_fingerprint=source_fingerprint,
        source_receipt=source_receipt,
        source_contract=source_contract,
        fingerprint=fingerprint,
    )


def validate_population_transfer_value_handoff(payload: Mapping[str, object]) -> str:
    """Validate a serialized transfer-value payload; return its fingerprint."""

    if payload.get("schema_id") != SCHEMA_ID:
        raise ValueError("unsupported transfer-value payload schema_id")
    if payload.get("program_id") != PROGRAM_ID:
        raise ValueError("unexpected program_id")

    producer = payload.get("producer")
    target = payload.get("target")
    semantics = payload.get("semantics")
    boundary = payload.get("boundary")
    provenance = payload.get("provenance")
    if not all(isinstance(value, Mapping) for value in (producer, target, semantics, boundary, provenance)):
        raise ValueError("producer, target, semantics, boundary and provenance must be objects")

    assert isinstance(producer, Mapping)
    assert isinstance(target, Mapping)
    assert isinstance(semantics, Mapping)
    assert isinstance(boundary, Mapping)
    assert isinstance(provenance, Mapping)
    if producer.get("chapter") != "N2" or producer.get("repository") != PRODUCER_REPOSITORY:
        raise ValueError("unexpected payload producer")
    if target.get("chapter") != TARGET_CHAPTER or target.get("system") != TARGET_SYSTEM:
        raise ValueError("unexpected transfer-value target")
    if target.get("role") != "information_transfer_value_for_downstream_reachability":
        raise ValueError("unexpected transfer-value target role")

    for key in (
        "is_state_artifact",
        "authorizes_state_promotion",
        "authorizes_spatial_patch_ranking",
        "authorizes_survey_site_selection",
        "authorizes_n4_action",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"boundary.{key} must be false")
    if boundary.get("n4_survey_action_owner") != "ACSP":
        raise ValueError("N4 survey-action ownership must remain ACSP")

    total_raw = payload.get("total_value")
    steps_raw = payload.get("steps")
    if not isinstance(total_raw, Mapping):
        raise ValueError("total_value must be an object")
    if not isinstance(steps_raw, list) or not steps_raw or not all(
        isinstance(value, Mapping) for value in steps_raw
    ):
        raise ValueError("steps must be a non-empty list of objects")
    total = _parse_handoff_step(total_raw, name="total_value")
    steps = tuple(
        _parse_handoff_step(value, name=f"steps[{index}]")
        for index, value in enumerate(steps_raw)
    )
    _validate_chain(total, steps)

    group_semantics = _clean_text(semantics.get("group"), name="semantics.group")
    cluster_semantics = _optional_text(
        semantics.get("population_cluster"), name="semantics.population_cluster"
    )
    estimand = _clean_text(semantics.get("estimand"), name="semantics.estimand")
    if estimand != "equal_weight_mean_gain_across_groups":
        raise ValueError("unsupported transfer-value estimand")
    gain_tolerance = _finite_number(
        semantics.get("gain_tolerance"), name="semantics.gain_tolerance"
    )
    if gain_tolerance < 0.0:
        raise ValueError("semantics.gain_tolerance must be non-negative")
    score = semantics.get("score")
    if not isinstance(score, Mapping):
        raise ValueError("semantics.score must be an object")
    score_kind = _clean_text(score.get("kind"), name="semantics.score.kind")
    if score_kind not in {"log", "other_proper"}:
        raise ValueError("semantics.score.kind must be log or other_proper")
    score_name = _clean_text(score.get("name"), name="semantics.score.name")
    score_unit = _clean_text(score.get("unit"), name="semantics.score.unit")
    if score.get("orientation") != "higher_is_better":
        raise ValueError("semantics.score.orientation must be higher_is_better")

    source_population_fingerprint = provenance.get("source_population_fingerprint")
    if not isinstance(source_population_fingerprint, str) or not _SHA256_RE.fullmatch(source_population_fingerprint):
        raise ValueError("source_population_fingerprint must be a canonical SHA-256")
    source_receipt = _optional_text(provenance.get("source_receipt"), name="provenance.source_receipt")
    source_contract = _optional_text(provenance.get("source_contract"), name="provenance.source_contract")

    core = {
        "schema_id": SCHEMA_ID,
        "program_id": PROGRAM_ID,
        "producer": {"chapter": "N2", "repository": PRODUCER_REPOSITORY},
        "target": {
            "chapter": TARGET_CHAPTER,
            "system": TARGET_SYSTEM,
            "role": "information_transfer_value_for_downstream_reachability",
        },
        "evidence_id": _clean_text(payload.get("evidence_id"), name="evidence_id"),
        "semantics": {
            "group": group_semantics,
            "population_cluster": cluster_semantics,
            "estimand": estimand,
            "gain_tolerance": gain_tolerance,
            "score": {
                "kind": score_kind,
                "name": score_name,
                "unit": score_unit,
                "orientation": "higher_is_better",
            },
        },
        "total_value": total.as_dict(),
        "steps": [step.as_dict() for step in steps],
        "boundary": {
            "is_state_artifact": False,
            "authorizes_state_promotion": False,
            "authorizes_spatial_patch_ranking": False,
            "authorizes_survey_site_selection": False,
            "authorizes_n4_action": False,
            "n4_survey_action_owner": "ACSP",
            "interpretation": (
                "values quantify held-out predictive value of additional information "
                "across groups; N3 may combine them with reachability or world structure, "
                "but this payload alone cannot rank places"
            ),
        },
        "provenance": {
            "source_population_fingerprint": source_population_fingerprint,
            "source_receipt": source_receipt,
            "source_contract": source_contract,
        },
    }
    expected = _canonical_fingerprint(core)
    fingerprint = payload.get("fingerprint")
    if not isinstance(fingerprint, str) or not _SHA256_RE.fullmatch(fingerprint):
        raise ValueError("payload fingerprint must be a canonical SHA-256")
    if fingerprint != expected:
        raise ValueError("transfer-value payload fingerprint mismatch")
    return fingerprint