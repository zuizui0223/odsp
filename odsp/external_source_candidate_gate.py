"""Publisher-metadata-only external source candidate screen for BOP.

No tracking, individual identity, event labels, or model predictions are read.
Source declarations are untrusted metadata. Even the most favorable result
authorizes SOURCE-ONLY preflight, never empirical admission.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping
from urllib.parse import urlparse


BOP_STRATA = frozenset((
    "Buteo buteo", "Circus aeruginosus",
    "Circus cyaneus", "Circus pygargus",
))
_FIELDS = frozenset((
    "species", "timestamp_utc", "longitude", "altitude_msl",
    "external_temperature",
))
_SCHEMA = frozenset((
    "candidate_id", "source_url", "source_version",
    "publisher_evidence_urls", "species_animal_count_upper_bounds",
    "field_evidence", "longitude_precision", "altitude_state_semantics",
    "cross_source_identity", "source_access",
))
_FIELD_STATES = frozenset(("present", "absent", "unknown"))
_PRECISION = frozenset(("native", "rounded_0p1_degree", "absent", "unknown"))
_HEIGHT = frozenset(("compatible_gps_msl", "different_outcome", "unknown"))
_IDENTITY = frozenset(("external_crosswalk_attested", "known_overlap", "unknown"))
_ACCESS = frozenset(("public_reuse_confirmed", "permission_required", "unknown"))
_ROUTES = frozenset(("historic_rf_direct", "new_reduced_common_input"))
_AIMS = frozenset(("new_animal_rank", "positive_population_content"))


def _hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _safe_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{name} must be a nonempty stripped string")
    return value


def _https_url(value: object) -> str:
    url = _safe_text(value, "publisher URL")
    parts = urlparse(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("publisher evidence requires an HTTPS URL with no credentials")
    return url


@dataclass(frozen=True)
class FrozenCandidateSource:
    candidate_id: str
    source_url: str
    source_version: str
    publisher_evidence_urls: tuple[str, ...]
    species_animal_count_upper_bounds: tuple[tuple[str, int | None], ...]
    field_evidence: tuple[tuple[str, str], ...]
    longitude_precision: str
    altitude_state_semantics: str
    cross_source_identity: str
    source_access: str
    sha256: str

    def canonical(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "candidate_id": self.candidate_id,
            "source_url": self.source_url,
            "source_version": self.source_version,
            "publisher_evidence_urls": list(self.publisher_evidence_urls),
            "species_animal_count_upper_bounds": dict(self.species_animal_count_upper_bounds),
            "field_evidence": dict(self.field_evidence),
            "longitude_precision": self.longitude_precision,
            "altitude_state_semantics": self.altitude_state_semantics,
            "cross_source_identity": self.cross_source_identity,
            "source_access": self.source_access,
            "stage": "publisher_metadata_only_no_animal_data",
        }

    def assert_unchanged(self) -> None:
        if _hash(self.canonical()) != self.sha256:
            raise ValueError("candidate source metadata changed since freeze")


def freeze_candidate_source(metadata: Mapping[str, object]) -> FrozenCandidateSource:
    """Freeze public-level declarations; this does not authenticate their truth."""
    if not isinstance(metadata, Mapping) or set(metadata) != _SCHEMA:
        raise ValueError("candidate metadata schema must exclude outcomes and extra fields")
    candidate = _safe_text(metadata["candidate_id"], "candidate_id")
    url = _https_url(metadata["source_url"])
    version = _safe_text(metadata["source_version"], "source_version")
    evidence = metadata["publisher_evidence_urls"]
    if (
        not isinstance(evidence, (list, tuple)) or not evidence
        or any(not isinstance(v, str) for v in evidence)
    ):
        raise ValueError("explicit publisher evidence URLs are required")
    evidence_urls = tuple(sorted(set(_https_url(v) for v in evidence)))
    counts = metadata["species_animal_count_upper_bounds"]
    if not isinstance(counts, Mapping) or not counts:
        raise ValueError("publisher count bounds must be species-resolved")
    normalized = []
    for name, bound in counts.items():
        species = _safe_text(name, "species")
        if bound is not None and (type(bound) is not int or bound < 0):
            raise ValueError("species animal upper bounds must be nonnegative integers or unknown")
        normalized.append((species, bound))
    fields = metadata["field_evidence"]
    if not isinstance(fields, Mapping) or set(fields) != _FIELDS:
        raise ValueError("required source feature schema must be exact")
    for name, state in fields.items():
        if state not in _FIELD_STATES:
            raise ValueError(f"unsupported feature evidence: {name}")
    for name, value, allowed in (
        ("longitude_precision", metadata["longitude_precision"], _PRECISION),
        ("altitude_state_semantics", metadata["altitude_state_semantics"], _HEIGHT),
        ("cross_source_identity", metadata["cross_source_identity"], _IDENTITY),
        ("source_access", metadata["source_access"], _ACCESS),
    ):
        if not isinstance(value, str) or value not in allowed:
            raise ValueError(f"invalid {name} declaration")
    frozen = FrozenCandidateSource(
        candidate_id=candidate,
        source_url=url,
        source_version=version,
        publisher_evidence_urls=evidence_urls,
        species_animal_count_upper_bounds=tuple(sorted(normalized)),
        field_evidence=tuple(sorted(fields.items())),
        longitude_precision=metadata["longitude_precision"],
        altitude_state_semantics=metadata["altitude_state_semantics"],
        cross_source_identity=metadata["cross_source_identity"],
        source_access=metadata["source_access"],
        sha256="",
    )
    object.__setattr__(frozen, "sha256", _hash(frozen.canonical()))
    return frozen


@dataclass(frozen=True)
class CandidateSourceScreen:
    candidate_id: str
    source_sha256: str
    route: str
    aim: str
    target_stratum: str
    required_animals_upper_bound: int
    known_blockers: tuple[str, ...]
    unresolved_holds: tuple[str, ...]
    status: str

    def as_public_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "candidate_id": self.candidate_id,
            "source_metadata_sha256": self.source_sha256,
            "route": self.route,
            "aim": self.aim,
            "target_stratum": self.target_stratum,
            "minimum_species_animal_count_to_attempt": self.required_animals_upper_bound,
            "known_blockers": list(self.known_blockers),
            "unresolved_holds": list(self.unresolved_holds),
            "status": self.status,
            "only_publisher_metadata_were_considered": True,
            "real_biological_source_admitted": False,
            "source_permissions_verified_by_software": False,
            "source_animal_counts_verified_by_software": False,
            "canonical_animal_nonoverlap_verified_by_software": False,
            "no_tracking_or_outcome_values_accessed": True,
            "historic_bop_terminal_unchanged": "empirical_state_prediction_mixed",
            "original_dryad_status_unchanged": "NOT_ADMITTED",
        }


def screen_candidate_source(
    candidate: FrozenCandidateSource,
    *,
    route: str,
    aim: str,
    target_stratum: str,
) -> CandidateSourceScreen:
    """Gate metadata ONLY; permission to download is never an output of this API."""
    if not isinstance(candidate, FrozenCandidateSource):
        raise ValueError("frozen source declaration required")
    candidate.assert_unchanged()
    if route not in _ROUTES or aim not in _AIMS:
        raise ValueError("route or inferential aim not recognized")
    if target_stratum not in BOP_STRATA:
        raise ValueError("target must be one of the original four BOP strata")
    # 9 calibration + 1 validation for a finite 90%-rank bound; 29 + 1
    # for 90%-positive content with 95% confidence. These are maxima on
    # available individuals, not evidence of actually eligible counts.
    needed = 30 if aim == "positive_population_content" else 10
    hard, hold = [], []
    counts = dict(candidate.species_animal_count_upper_bounds)
    if target_stratum not in counts:
        hard.append("TARGET_SPECIES_NOT_IN_PUBLISHER_ROSTER")
    elif counts[target_stratum] is None:
        hold.append("TARGET_SPECIES_INDEPENDENT_ANIMAL_COUNT_UNKNOWN")
    elif counts[target_stratum] < needed:
        hard.append("PUBLISHER_ANIMAL_COUNT_UPPER_BOUND_BELOW_REQUIRED_ROSTER")
    fields = dict(candidate.field_evidence)
    required = ("species", "timestamp_utc", "longitude", "altitude_msl")
    if route == "historic_rf_direct":
        required += ("external_temperature",)
    for name in required:
        if fields[name] == "absent":
            hard.append("PUBLISHED_REQUIRED_FIELD_ABSENT:" + name)
        elif fields[name] == "unknown":
            hold.append("PUBLISHED_REQUIRED_FIELD_UNVERIFIED:" + name)
    if candidate.longitude_precision == "absent":
        hard.append("PUBLISHED_LONGITUDE_COORDINATES_ABSENT")
    elif candidate.longitude_precision == "unknown":
        hold.append("LONGITUDE_RESOLUTION_UNKNOWN")
    elif route == "historic_rf_direct" and candidate.longitude_precision == "rounded_0p1_degree":
        hard.append("HISTORIC_RF_LONGITUDE_PRECISION_NOT_RETAINED")
    if candidate.altitude_state_semantics == "different_outcome":
        hard.append("ALTITUDE_STATE_DEFINITION_INCOMPATIBLE")
    elif candidate.altitude_state_semantics == "unknown":
        hold.append("ALTITUDE_STATE_DEFINITION_UNVERIFIED")
    if candidate.cross_source_identity == "known_overlap":
        hard.append("TRAINING_TARGET_ANIMAL_IDENTITY_OVERLAP")
    elif candidate.cross_source_identity == "unknown":
        hold.append("INDEPENDENT_CANONICAL_CROSSWALK_UNVERIFIED")
    if candidate.source_access != "public_reuse_confirmed":
        hold.append("SOURCE_ACCESS_OR_REUSE_PERMISSION_UNVERIFIED")
    status = (
        "KNOWN_INCOMPATIBLE" if hard else
        "HOLD_METADATA_OR_PERMISSION" if hold else
        "ELIGIBLE_FOR_SOURCE_ONLY_PREFLIGHT"
    )
    return CandidateSourceScreen(
        candidate_id=candidate.candidate_id, source_sha256=candidate.sha256,
        route=route, aim=aim, target_stratum=target_stratum,
        required_animals_upper_bound=needed,
        known_blockers=tuple(hard), unresolved_holds=tuple(hold),
        status=status,
    )
