"""Experimental *source-value lineage* preflight for future external rosters.

The existing ODSP v5 freeze can verify that row/group/block/weight metadata
and implementation were frozen before declared outcome access. This NEW
opt-in preflight asks a different question: were the *values* used to
construct the validation roster computed from observations themselves?

A byte hash and freeze timestamp never prove that metadata were generated
independently of outcomes. This auditor traverses a declared dependency DAG
for the fields actually used by roster, group, block, weight and optional
eligibility. Taint from observation-derived roots, outcome-based manual
corrections or undocumented lineage is never silently cleared by freezing
downstream CSV bytes. Passing means only an internally coherent DECLARATION
of independence, not trusted third-party proof.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from collections.abc import Mapping
from typing import Any

ROUTE_VERSION = "validation_roster_field_lineage_v0"
ORIGINS = frozenset(("design_recorded", "derived", "observation_derived", "unknown"))
REQUIRED_ROLES = ("roster_membership", "validation_group", "validation_block", "sample_weight")
OPTIONAL_ROLES = ("eligibility_filter", "physical_unit_id", "fold_assignment")
OUTCOME_CORRECTION = "<outcome-based correction>"


@dataclass(frozen=True)
class FieldLineageAuditV0:
    schema_version: int
    method_version: str
    plan_id: str
    canonical_manifest_sha256: str
    declared_node_count: int
    actually_used_node_count: int
    audited_roles: tuple[str, ...]
    affected_roles: tuple[str, ...]
    outcome_dependent_roles: tuple[str, ...]
    undocumented_roles: tuple[str, ...]
    selection_lineage_status: str
    outcome_paths: tuple[tuple[str, ...], ...]
    undocumented_paths: tuple[tuple[str, ...], ...]
    upstream_field_dependencies_closed: bool
    role_coverage_complete: bool
    declared_source_lineage_independence_supported: bool
    trusted_external_lineage_attestation_verified: bool
    independently_observed_metadata_values_verified: bool
    outcome_bytes_read: bool
    changes_active_odsp_qualified_routes: bool
    retrospectively_reclassifies_old_ecological_results: bool

    def as_dict(self) -> dict[str, object]:
        result=asdict(self)
        for key in ("audited_roles","affected_roles","outcome_dependent_roles",
                    "undocumented_roles"):
            result[key]=list(result[key])
        result["outcome_paths"]=[list(x) for x in self.outcome_paths]
        result["undocumented_paths"]=[list(x) for x in self.undocumented_paths]
        return result


def _identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")
    return value.strip()


def _strict_bool(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be an explicit boolean")
    return value


def audit_validation_roster_field_lineage_v0(
    plan: Mapping[str, object],
) -> FieldLineageAuditV0:
    """Check a source-metadata dependency declaration, NOT data-content truth."""
    if not isinstance(plan, Mapping):
        raise ValueError("lineage plan must be a mapping")
    if plan.get("schema_version") != 1 or plan.get("lineage_method") != ROUTE_VERSION:
        raise ValueError("unrecognized lineage schema/method version")
    plan_id=_identifier(plan.get("plan_id"),"plan_id")
    nodes=plan.get("fields")
    mapping=plan.get("used_by_roles")
    if not isinstance(nodes,list) or not nodes:
        raise ValueError("fields must be a nonempty list")
    if not isinstance(mapping,Mapping):
        raise ValueError("used_by_roles must be a mapping")
    expected=frozenset((*REQUIRED_ROLES,*OPTIONAL_ROLES))
    if set(mapping) - expected:
        raise ValueError("unknown roster role")
    if any(role not in mapping for role in REQUIRED_ROLES):
        raise ValueError("required roster roles must all be declared")

    dag: dict[str,dict[str,object]]={}
    for raw in nodes:
        if not isinstance(raw,Mapping):
            raise ValueError("field node must be an object")
        if set(raw) != {"field","origin","parents","corrected_using_outcomes","documentation"}:
            raise ValueError("field nodes need exact lineage-provenance fields")
        label=_identifier(raw["field"],"field")
        if label in dag:
            raise ValueError(f"duplicate field {label}")
        origin=_identifier(raw["origin"],"origin")
        if origin not in ORIGINS:
            raise ValueError(f"unsupported field origin for {label}")
        parents=raw["parents"]
        if not isinstance(parents,list):
            raise ValueError(f"parents for {label} must be a list")
        ids=tuple(_identifier(p,"parent") for p in parents)
        if len(set(ids))!=len(ids):
            raise ValueError(f"duplicate parent in {label}")
        if origin=="derived" and not ids:
            raise ValueError(f"derived field {label} must name its upstream inputs")
        if origin!="derived" and ids:
            raise ValueError(f"root field {label} cannot silently claim independent parents")
        corrected=_strict_bool(raw["corrected_using_outcomes"],f"{label}.corrected_using_outcomes")
        documentation=_identifier(raw["documentation"],f"{label}.documentation")
        dag[label]={
            "origin":origin,"parents":ids,
            "corrected_using_outcomes":corrected,
            "documentation":documentation,
        }
    for node,value in dag.items():
        if any(p not in dag for p in value["parents"]):
            raise ValueError(f"unresolved parent in lineage for {node}")

    roles: dict[str,str]={}
    for role,name in mapping.items():
        role=str(role)
        field=_identifier(name,f"used_by_roles.{role}")
        if field not in dag:
            raise ValueError(f"roster role {role} refers to a missing field")
        roles[role]=field

    # Check all node cycles, not just ancestor closure of currently selected
    # fields: a broken source lineage is never trusted as a complete DAG.
    visiting=set()
    visited=set()
    def check_cycle(node: str)->None:
        if node in visited:
            return
        if node in visiting:
            raise ValueError(f"cycle in source-value lineage involving {node}")
        visiting.add(node)
        for parent in dag[node]["parents"]:
            check_cycle(parent)
        visiting.remove(node)
        visited.add(node)
    for key in dag:
        check_cycle(key)

    # Collect all reachable ancestor nodes and contamination paths. An
    # unselected outcome column does NOT contaminate a fully independent
    # site roster merely because it appears somewhere in the same source CSV.
    used=set()
    outcomes: list[tuple[str,...]]=[]
    unknowns: list[tuple[str,...]]=[]
    dependent_roles=set()
    undocumented_roles=set()
    for role,field in sorted(roles.items()):
        def walk(node: str,path: tuple[str,...])->None:
            used.add(node)
            item=dag[node]
            if item["corrected_using_outcomes"]:
                outcomes.append((role,*path,OUTCOME_CORRECTION))
                dependent_roles.add(role)
            if item["origin"]=="observation_derived":
                outcomes.append((role,*path))
                dependent_roles.add(role)
            elif item["origin"]=="unknown":
                unknowns.append((role,*path))
                undocumented_roles.add(role)
            for parent in item["parents"]:
                walk(parent,(*path,parent))
        walk(field,(field,))
    if dependent_roles:
        status="HOLD_OUTCOME_DERIVED_SOURCE_METADATA"
    elif undocumented_roles:
        status="HOLD_UNDOCUMENTED_SOURCE_METADATA_LINEAGE"
    else:
        status="DECLARED_INDEPENDENT_LINEAGE_ONLY_NOT_ATTESTED"

    canonical=json.dumps(
        dict(plan),sort_keys=True,separators=(",",":"),
        ensure_ascii=False,allow_nan=False,
    ).encode("utf-8")
    return FieldLineageAuditV0(
        schema_version=1,
        method_version=ROUTE_VERSION,
        plan_id=plan_id,
        canonical_manifest_sha256=hashlib.sha256(canonical).hexdigest(),
        declared_node_count=len(dag),
        actually_used_node_count=len(used),
        audited_roles=tuple(sorted(roles)),
        affected_roles=tuple(sorted(dependent_roles|undocumented_roles)),
        outcome_dependent_roles=tuple(sorted(dependent_roles)),
        undocumented_roles=tuple(sorted(undocumented_roles)),
        selection_lineage_status=status,
        outcome_paths=tuple(sorted(set(outcomes))),
        undocumented_paths=tuple(sorted(set(unknowns))),
        upstream_field_dependencies_closed=True,
        role_coverage_complete=True,
        declared_source_lineage_independence_supported=not bool(
            dependent_roles|undocumented_roles
        ),
        trusted_external_lineage_attestation_verified=False,
        independently_observed_metadata_values_verified=False,
        outcome_bytes_read=False,
        changes_active_odsp_qualified_routes=False,
        retrospectively_reclassifies_old_ecological_results=False,
    )
