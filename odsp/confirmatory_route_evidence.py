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
_TRAINING_PROCESS_V5 = "ODSP_TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_CONTRACT.json"
_TRAINING_PROCESS_V5_BASE = "TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_QUALIFICATION_RECEIPT.json"
_TRAINING_PROCESS_V5_SUPPORT_CONTRACT = "ODSP_TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_CONTRACT.json"
_TRAINING_PROCESS_V5_SUPPORT = "TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_RECEIPT.json"
_TRAINING_PROCESS_V5_PROMOTION = "ODSP_TRAINING_PROCESS_V5_PRIMARY_PROMOTION_GATE.json"
_TRAINING_PROCESS_V5_PROMOTION_V2 = "ODSP_TRAINING_PROCESS_V5_PRIMARY_PROMOTION_GATE_V2.json"
_TRAINING_PROCESS_MANAGED = "ODSP_TRAINING_PROCESS_MANAGED_GENERATION_CONTRACT.json"
_TRAINING_PROCESS_FRAME = "ODSP_TRAINING_PROCESS_VALIDATION_FRAME_PROVENANCE_CONTRACT.json"
_TRAINING_PROCESS_V5_IDENTITY_CONTRACT = "ODSP_TRAINING_PROCESS_V5_QUALIFICATION_IDENTITY_CONTRACT.json"
_TRAINING_PROCESS_V5_IDENTITY = "TRAINING_PROCESS_V5_QUALIFICATION_IDENTITY_RECEIPT.json"
_TRAINING_PROCESS_V5_EXTERNAL_FREEZE = "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT.json"
_TRAINING_PROCESS_V5_EXTERNAL_FREEZE_V2 = "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT_V2.json"
_TRAINING_PROCESS_V5_EXTERNAL_FREEZE_V3 = "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT_V3.json"
_TRAINING_PROCESS_V5_MANAGED_EXTERNAL_SCORING = "ODSP_TRAINING_PROCESS_V5_MANAGED_EXTERNAL_SCORING_CONTRACT.json"
_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION = "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE.json"
_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_V2 = "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE_V2.json"
_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_V3 = "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE_V3.json"
_TRAINING_PROCESS_V5_EXTERNAL_IDENTITY_CONTRACT_V2 = "ODSP_TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_CONTRACT_V2.json"
_TRAINING_PROCESS_V5_EXTERNAL_FOCUSED_V2 = "TRAINING_PROCESS_V5_EXTERNAL_FOCUSED_ENDPOINT_RECEIPT_V2.json"
_TRAINING_PROCESS_V5_EXTERNAL_IDENTITY_V2 = "TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_RECEIPT_V2.json"
_TRAINING_PROCESS_V5_EXTERNAL_ROUTE_PROMOTION_FINAL = "ODSP_TRAINING_PROCESS_V5_EXTERNAL_ROUTE_PROMOTION_CONTRACT.json"
_TRAINING_PROCESS_V5_EXTERNAL_HASH_RECEIPT = "TRAINING_PROCESS_V5_EXTERNAL_EVIDENCE_HASH_RECEIPT.json"
_TRAINING_PROCESS_V5_EXTERNAL_REGISTRATION_CORRECTION = "ODSP_TRAINING_PROCESS_V5_EXTERNAL_REGISTRATION_CORRECTION_CONTRACT.json"

QUALIFICATION_EVIDENCE_REGISTRY_ID = "odsp-confirmatory-route-evidence-v6"

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
    "ODSP_TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_CONTRACT.json": "f82180186bbc333244b80625c67394cd6117c0c75d028caf580e5e9a6cc689af",
    "TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_QUALIFICATION_RECEIPT.json": "f813acc7b9c57bc0b621bc823ee7bd1d45fe68af05a4d645729cb903c8da41ea",
    "ODSP_TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_CONTRACT.json": "67cbb1da0f76a82cb879ef555f58adc20348656b1713db449aa96cdb7b452394",
    "TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_RECEIPT.json": "5880800bd80bf691b6cbfb880b27af29218fe5d260595658d4c878872f15031d",
    "ODSP_TRAINING_PROCESS_V5_PRIMARY_PROMOTION_GATE.json": "05bebc8627c83e94cc6d1d54657083987b4fe5ba01876faf6c57aa7138fdd57e",
    "ODSP_TRAINING_PROCESS_V5_PRIMARY_PROMOTION_GATE_V2.json": "92d25f7ab3979ebbf1f98eab3df142c820750bbd67a38f7ea001eb0b9a017dbc",
    "ODSP_TRAINING_PROCESS_MANAGED_GENERATION_CONTRACT.json": "dd63556b8be22d3dee405b8071238d64db22b4d0382b739d37eb29e617f9afbb",
    "ODSP_TRAINING_PROCESS_VALIDATION_FRAME_PROVENANCE_CONTRACT.json": "a0ec68a9cb2a83399f8b861ac217eaf0c02c23a8458cbc36c74da42210e48999",
    "ODSP_TRAINING_PROCESS_V5_QUALIFICATION_IDENTITY_CONTRACT.json": "86e185703e40d8ca33ecf81a7376587bfe85e1ab5b295cd8e32499f34f740227",
    "TRAINING_PROCESS_V5_QUALIFICATION_IDENTITY_RECEIPT.json": "c6cbe36f2581b0c1b5ec2fe9e4670a887b07f7a491a567cd9fd4f3c304a12278",
    "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT.json": "453390e9fc342bab2db9e37b8673111f5037f5231a3ed5f0c0027cd5a00755cb",
    "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT_V2.json": "375f8f6df3cf47a2a5a354ab8efdd80a20851bbc61fe114173fd26d848e95312",
    "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT_V3.json": "7e82730f7258901ffc10be22d267ae1b9270a19ed5593d44f78b25646e8b715b",
    "ODSP_TRAINING_PROCESS_V5_MANAGED_EXTERNAL_SCORING_CONTRACT.json": "1a50629b5b48ac3eb01403319ce7ec43e941052cda209812c82df5184adb839e",
    "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE.json": "52dbab209bbb471d1f3756be31e616b9004252092e368614b89d2caa8326eccf",
    "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE_V2.json": "3edc33bc9451b693afb777ddbd07f31677b390db777985eb25e93bba65b650a5",
    "ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE_V3.json": "2e953a99fe8bd39fffcf277bdce8273c2e67914ffe4d43237f2d40b011fbefa8",
    "ODSP_TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_CONTRACT_V2.json": "379464ec4c50db02a3a2fc63b0db6e772222836036d2f13c1f15cde3be46b4e2",
    "TRAINING_PROCESS_V5_EXTERNAL_FOCUSED_ENDPOINT_RECEIPT_V2.json": "e6e436a33dcb8549b9068938e41e0c6a1e68d0ae36e20614fd782cac88e9778d",
    "TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_RECEIPT_V2.json": "e19fe9ae630bf5430f9fda997a37f0933e51e010b73653d32cf15ee971ba7ed3",
    "ODSP_TRAINING_PROCESS_V5_EXTERNAL_ROUTE_PROMOTION_CONTRACT.json": "380e1772f7b84736a7f12411da8f913c47407223bb508ff88158f2b75c2b8022",
    "TRAINING_PROCESS_V5_EXTERNAL_EVIDENCE_HASH_RECEIPT.json": "2e62d874b0934978dab85e87c1a1cb7f0f1912786a445dd04f4116727e2300ee",
    "ODSP_TRAINING_PROCESS_V5_EXTERNAL_REGISTRATION_CORRECTION_CONTRACT.json": "7f804c4b391ab13388daf879ee13b9aa332afff4155f8c22d892bf2e9517dfd0",
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

# Qualified predeclared training-process directional filtration.
_register(
    _key(
        "greater",
        "independent_groups",
        "filtration",
        "predeclared_training_process",
        "none",
        contrast_count=2,
    ),
    _TRAINING_PROCESS_V5,
    _TRAINING_PROCESS_V5_BASE,
    _TRAINING_PROCESS_V5_SUPPORT_CONTRACT,
    _TRAINING_PROCESS_V5_SUPPORT,
    _TRAINING_PROCESS_V5_PROMOTION,
    _TRAINING_PROCESS_V5_PROMOTION_V2,
    _TRAINING_PROCESS_MANAGED,
    _TRAINING_PROCESS_FRAME,
    _TRAINING_PROCESS_V5_IDENTITY_CONTRACT,
    _TRAINING_PROCESS_V5_IDENTITY,
)


_register(
    _key(
        "greater",
        "independent_groups",
        "filtration",
        "predeclared_training_process",
        "untouched_frozen",
        contrast_count=2,
    ),
    _TRAINING_PROCESS_V5,
    _TRAINING_PROCESS_V5_BASE,
    _TRAINING_PROCESS_V5_SUPPORT_CONTRACT,
    _TRAINING_PROCESS_V5_SUPPORT,
    _TRAINING_PROCESS_V5_PROMOTION,
    _TRAINING_PROCESS_V5_PROMOTION_V2,
    _TRAINING_PROCESS_MANAGED,
    _TRAINING_PROCESS_FRAME,
    _TRAINING_PROCESS_V5_IDENTITY_CONTRACT,
    _TRAINING_PROCESS_V5_IDENTITY,
    _TRAINING_PROCESS_V5_EXTERNAL_FREEZE,
    _TRAINING_PROCESS_V5_EXTERNAL_FREEZE_V2,
    _TRAINING_PROCESS_V5_EXTERNAL_FREEZE_V3,
    _TRAINING_PROCESS_V5_MANAGED_EXTERNAL_SCORING,
    _TRAINING_PROCESS_V5_EXTERNAL_PROMOTION,
    _TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_V2,
    _TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_V3,
    _TRAINING_PROCESS_V5_EXTERNAL_IDENTITY_CONTRACT_V2,
    _TRAINING_PROCESS_V5_EXTERNAL_FOCUSED_V2,
    _TRAINING_PROCESS_V5_EXTERNAL_IDENTITY_V2,
    _TRAINING_PROCESS_V5_EXTERNAL_ROUTE_PROMOTION_FINAL,
    _TRAINING_PROCESS_V5_EXTERNAL_HASH_RECEIPT,
    _TRAINING_PROCESS_V5_EXTERNAL_REGISTRATION_CORRECTION,
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
