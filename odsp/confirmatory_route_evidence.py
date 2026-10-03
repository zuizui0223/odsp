"""Route-context qualification evidence for confirmatory ODSP methods.

Evidence is keyed by the full routed scientific design plus simultaneous family
size, not by API surface alone.  This matters when one canonical surface supports
multiple prospectively qualified families whose evidence chains differ.
"""
from __future__ import annotations


def route_evidence_key(
    *,
    alternative: str,
    validation_design: str,
    information_structure: str,
    upstream_refits: str,
    external_validation: str,
    contrast_count: int | None = None,
    information_block_count: int | None = None,
) -> str:
    """Build the stable machine key used by the frozen evidence registry."""

    parts = [
        f"alternative={str(alternative).strip()}",
        f"validation_design={str(validation_design).strip()}",
        f"information_structure={str(information_structure).strip()}",
        f"upstream_refits={str(upstream_refits).strip()}",
        f"external_validation={str(external_validation).strip()}",
    ]
    if information_structure == "filtration":
        if isinstance(contrast_count, bool) or not isinstance(contrast_count, int):
            raise ValueError("contrast_count is required for filtration evidence keys")
        parts.append(f"contrast_count={contrast_count}")
    elif information_structure == "complete_lattice":
        if isinstance(information_block_count, bool) or not isinstance(
            information_block_count, int
        ):
            raise ValueError(
                "information_block_count is required for lattice evidence keys"
            )
        edge_count = information_block_count * 2 ** (information_block_count - 1)
        parts.append(f"information_block_count={information_block_count}")
        parts.append(f"edge_count={edge_count}")
    else:
        raise ValueError("unknown information_structure for evidence key")
    return "|".join(parts)


def _key(
    alternative: str,
    validation_design: str,
    information_structure: str,
    upstream_refits: str,
    external_validation: str,
    *,
    contrast_count: int | None = None,
    information_block_count: int | None = None,
) -> str:
    return route_evidence_key(
        alternative=alternative,
        validation_design=validation_design,
        information_structure=information_structure,
        upstream_refits=upstream_refits,
        external_validation=external_validation,
        contrast_count=contrast_count,
        information_block_count=information_block_count,
    )


_ONE_SIDED = "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json"
_C4_ENVELOPE = "INDEPENDENT_C4_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json"
_C12_ENVELOPE = "INDEPENDENT_C12_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json"
_ALL_REFIT = "ODSP_ALL_REFIT_DIRECTIONAL_ROBUSTNESS_CONTRACT.json"
_REFIT_ONE_SIDED = "ODSP_REFIT_ONE_SIDED_POSITIVE_TRANSFER_CONTRACT.json"
_EXTERNAL_V2 = "ODSP_UNTOUCHED_EXTERNAL_FREEZE_SEMANTIC_LOCK_V2.json"
_PAIRED_ONE_SIDED = "PAIRED_ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json"
_PAIRED_EXTERNAL_V3 = "ODSP_PAIRED_REFIT_UNTOUCHED_EXTERNAL_V3_CONTRACT.json"
_INDEPENDENT_LATTICE = "ODSP_INDEPENDENT_DIRECTIONAL_LATTICE_4_12EDGE_CONTRACT.json"
_INDEPENDENT_LATTICE_12 = "INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json"
_ALL_REFIT_INDEPENDENT_LATTICE = (
    "ODSP_ALL_REFIT_INDEPENDENT_DIRECTIONAL_LATTICE_4_12EDGE_CONTRACT.json"
)
_INDEPENDENT_EXTERNAL_LATTICE = (
    "ODSP_UNTOUCHED_EXTERNAL_INDEPENDENT_ALL_REFIT_LATTICE_V5_CONTRACT.json"
)
_PAIRED_LATTICE = "PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json"
_ALL_REFIT_PAIRED_LATTICE = "ODSP_ALL_REFIT_PAIRED_POSITIVE_LATTICE_CONTRACT.json"
_PAIRED_EXTERNAL_LATTICE = (
    "ODSP_UNTOUCHED_EXTERNAL_PAIRED_ALL_REFIT_LATTICE_V4_CONTRACT.json"
)
_TWO_SIDED = "MULTICONTRAST_BOOTSTRAP_T_V2_OPERATING_CHARACTERISTICS_RECEIPT.json"
_TWO_SIDED_INFO = "ODSP_INFORMATION_TRANSFER_BOOTSTRAP_T_V2_CONTRACT.json"

QUALIFICATION_EVIDENCE_REGISTRY_ID = "odsp-confirmatory-route-evidence-v3"

# Exact UTF-8 file-content digests for every artifact admitted to a confirmatory
# qualification chain. Source CI verifies these constants against repository bytes.
QUALIFICATION_EVIDENCE_SHA256_BY_ARTIFACT: dict[str, str] = {
    "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json": "a80a92f82487a3eba8298de9bf15cee189a3b417503ae727e981a5f11ac0ccef",
    "INDEPENDENT_C4_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json": "17d64fede53a1dcb12c3a81bb325fdd80b626ac06a48c180c158316b9bea7007",
    "INDEPENDENT_C12_ONE_SIDED_SUPPORT_ENVELOPE_RECEIPT.json": "cde0b86d8c2e11ce94b111a6b42663814e257efcc4aa0e2cdddbb70c88041838",
    "ODSP_ALL_REFIT_DIRECTIONAL_ROBUSTNESS_CONTRACT.json": "5b69958df43d4b4b7ac14851401218f5ad8086e032fd75bad1cbb46456d508bf",
    "ODSP_REFIT_ONE_SIDED_POSITIVE_TRANSFER_CONTRACT.json": "c29b95b9b83329005b0dd49a1fe911e2f5fbebe5a7319f41875a396a31015cb3",
    "ODSP_UNTOUCHED_EXTERNAL_FREEZE_SEMANTIC_LOCK_V2.json": "cc4e66bf1b8fe3448493517f4f2119a1ba4af9ea053c026673b48abbb185faf5",
    "PAIRED_ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json": "54f45559b9fcc6db6a42058cd6a76dd7fef6b48810258003eb019cbc0dfd0098",
    "ODSP_PAIRED_REFIT_UNTOUCHED_EXTERNAL_V3_CONTRACT.json": "bc4f35f15d2b91fcddc028635dad683d14843fa25904625626a9ebad90eac9e4",
    "ODSP_INDEPENDENT_DIRECTIONAL_LATTICE_4_12EDGE_CONTRACT.json": "f41e37d0303737b2f4ae99f77fb17415ffebcaef18f8cd77b23bbf3e1731614e",
    "INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json": "552ff692b2dbb31a61765720393804595723c0ffa66be8262295260148e8fa6e",
    "ODSP_ALL_REFIT_INDEPENDENT_DIRECTIONAL_LATTICE_4_12EDGE_CONTRACT.json": "2938e2e881ed3e8f54f960cd797a940a9962f1aedcadb306d9bcfaf5acbbc371",
    "ODSP_UNTOUCHED_EXTERNAL_INDEPENDENT_ALL_REFIT_LATTICE_V5_CONTRACT.json": "828343e42bdff6b00d127c530d7b0efccf652ba450b591445d18960d8deacfc6",
    "PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json": "664dcb27526464e9f3f70cb09de6c6d7df525009c8c41280d74967d85610a960",
    "ODSP_ALL_REFIT_PAIRED_POSITIVE_LATTICE_CONTRACT.json": "7979268574dc3f13e0619e02b34017cfd8af67414045b3f094d51e3e73cdcd76",
    "ODSP_UNTOUCHED_EXTERNAL_PAIRED_ALL_REFIT_LATTICE_V4_CONTRACT.json": "a6e09c958f7e51e9f77124711b1ed5f67c63a579b45f34d266a6da237cd04430",
    "MULTICONTRAST_BOOTSTRAP_T_V2_OPERATING_CHARACTERISTICS_RECEIPT.json": "40c00b38316df9a0109ec6aca1c7fe6c2b7548a1b2ee01a85df80fded91f1a2e",
    "ODSP_INFORMATION_TRANSFER_BOOTSTRAP_T_V2_CONTRACT.json": "ecf523b936b5264633e9f7f7d070b48fa75a8ba23168a856dcad1a11c49f265b",
}


CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY: dict[str, tuple[str, ...]] = {}


def _register(
    key: str,
    *evidence: str,
) -> None:
    if key in CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY:
        raise RuntimeError(f"duplicate confirmatory evidence route key: {key}")
    CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY[key] = tuple(evidence)


# Independent directional filtration.
for count in (2, 4):
    base = (_ONE_SIDED,) if count == 2 else (_ONE_SIDED, _C4_ENVELOPE)
    _register(
        _key(
            "greater",
            "independent_groups",
            "filtration",
            "none",
            "none",
            contrast_count=count,
        ),
        *base,
    )
    _register(
        _key(
            "greater",
            "independent_groups",
            "filtration",
            "fixed_set",
            "none",
            contrast_count=count,
        ),
        *base,
        _ALL_REFIT,
    )
    _register(
        _key(
            "greater",
            "independent_groups",
            "filtration",
            "fixed_set",
            "untouched_frozen",
            contrast_count=count,
        ),
        *base,
        _REFIT_ONE_SIDED,
        _EXTERNAL_V2,
    )

# Paired directional filtration.
_register(
    _key(
        "greater",
        "paired_shared_blocks",
        "filtration",
        "none",
        "none",
        contrast_count=2,
    ),
    _PAIRED_ONE_SIDED,
)
_register(
    _key(
        "greater",
        "paired_shared_blocks",
        "filtration",
        "fixed_set",
        "none",
        contrast_count=2,
    ),
    _PAIRED_ONE_SIDED,
    _ALL_REFIT,
)
_register(
    _key(
        "greater",
        "paired_shared_blocks",
        "filtration",
        "fixed_set",
        "untouched_frozen",
        contrast_count=2,
    ),
    _PAIRED_ONE_SIDED,
    _ALL_REFIT,
    _PAIRED_EXTERNAL_V3,
)

# Independent directional complete lattice.
_register(
    _key(
        "greater",
        "independent_groups",
        "complete_lattice",
        "none",
        "none",
        information_block_count=2,
    ),
    _ONE_SIDED,
    _C4_ENVELOPE,
    _INDEPENDENT_LATTICE,
)
_register(
    _key(
        "greater",
        "independent_groups",
        "complete_lattice",
        "none",
        "none",
        information_block_count=3,
    ),
    _INDEPENDENT_LATTICE_12,
    _INDEPENDENT_LATTICE,
)
_register(
    _key(
        "greater",
        "independent_groups",
        "complete_lattice",
        "fixed_set",
        "none",
        information_block_count=2,
    ),
    _ONE_SIDED,
    _C4_ENVELOPE,
    _INDEPENDENT_LATTICE,
    _ALL_REFIT_INDEPENDENT_LATTICE,
)
_register(
    _key(
        "greater",
        "independent_groups",
        "complete_lattice",
        "fixed_set",
        "none",
        information_block_count=3,
    ),
    _INDEPENDENT_LATTICE_12,
    _INDEPENDENT_LATTICE,
    _ALL_REFIT_INDEPENDENT_LATTICE,
)
_register(
    _key(
        "greater",
        "independent_groups",
        "complete_lattice",
        "fixed_set",
        "untouched_frozen",
        information_block_count=2,
    ),
    _ONE_SIDED,
    _C4_ENVELOPE,
    _INDEPENDENT_LATTICE,
    _ALL_REFIT_INDEPENDENT_LATTICE,
    _INDEPENDENT_EXTERNAL_LATTICE,
)
_register(
    _key(
        "greater",
        "independent_groups",
        "complete_lattice",
        "fixed_set",
        "untouched_frozen",
        information_block_count=3,
    ),
    _INDEPENDENT_LATTICE_12,
    _C12_ENVELOPE,
    _INDEPENDENT_LATTICE,
    _ALL_REFIT_INDEPENDENT_LATTICE,
    _INDEPENDENT_EXTERNAL_LATTICE,
)

# Paired directional complete lattice.
for blocks in (2, 3):
    _register(
        _key(
            "greater",
            "paired_shared_blocks",
            "complete_lattice",
            "none",
            "none",
            information_block_count=blocks,
        ),
        _PAIRED_LATTICE,
    )
    _register(
        _key(
            "greater",
            "paired_shared_blocks",
            "complete_lattice",
            "fixed_set",
            "none",
            information_block_count=blocks,
        ),
        _PAIRED_LATTICE,
        _ALL_REFIT_PAIRED_LATTICE,
    )
    _register(
        _key(
            "greater",
            "paired_shared_blocks",
            "complete_lattice",
            "fixed_set",
            "untouched_frozen",
            information_block_count=blocks,
        ),
        _PAIRED_LATTICE,
        _ALL_REFIT_PAIRED_LATTICE,
        _PAIRED_EXTERNAL_LATTICE,
    )

# Independent bidirectional v2.
for count in (2, 4):
    _register(
        _key(
            "two_sided",
            "independent_groups",
            "filtration",
            "none",
            "none",
            contrast_count=count,
        ),
        _TWO_SIDED,
    )
_register(
    _key(
        "two_sided",
        "independent_groups",
        "complete_lattice",
        "none",
        "none",
        information_block_count=2,
    ),
    _TWO_SIDED,
    _TWO_SIDED_INFO,
)


def qualification_evidence_for_route_key(key: str) -> tuple[str, ...]:
    """Return the frozen evidence chain for one fully specified route key."""

    value = str(key).strip()
    if not value:
        return ()
    return CONFIRMATORY_EVIDENCE_BY_ROUTE_KEY.get(value, ())


def qualification_evidence_artifacts_for_route_key(
    key: str,
) -> tuple[dict[str, str], ...]:
    """Return the ordered artifact+SHA256 snapshot for one route key.

    The statistical qualification is not recomputed here. This function binds
    the already-registered evidence chain to exact repository artifact content.
    Missing or malformed digest registrations fail closed.
    """

    evidence = qualification_evidence_for_route_key(key)
    if not evidence:
        return ()
    snapshot: list[dict[str, str]] = []
    for artifact in evidence:
        digest = QUALIFICATION_EVIDENCE_SHA256_BY_ARTIFACT.get(artifact)
        if digest is None:
            raise ValueError(
                f"qualification evidence artifact has no registered SHA256: {artifact}"
            )
        if len(digest) != 64 or digest.lower() != digest:
            raise ValueError(
                f"qualification evidence artifact has invalid SHA256: {artifact}"
            )
        try:
            int(digest, 16)
        except ValueError as exc:
            raise ValueError(
                f"qualification evidence artifact has invalid SHA256: {artifact}"
            ) from exc
        snapshot.append({"artifact": artifact, "sha256": digest})
    return tuple(snapshot)
