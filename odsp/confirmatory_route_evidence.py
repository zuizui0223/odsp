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
_PAIRED_LATTICE = "PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json"
_ALL_REFIT_PAIRED_LATTICE = "ODSP_ALL_REFIT_PAIRED_POSITIVE_LATTICE_CONTRACT.json"
_PAIRED_EXTERNAL_LATTICE = (
    "ODSP_UNTOUCHED_EXTERNAL_PAIRED_ALL_REFIT_LATTICE_V4_CONTRACT.json"
)
_TWO_SIDED = "MULTICONTRAST_BOOTSTRAP_T_V2_OPERATING_CHARACTERISTICS_RECEIPT.json"
_TWO_SIDED_INFO = "ODSP_INFORMATION_TRANSFER_BOOTSTRAP_T_V2_CONTRACT.json"


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
