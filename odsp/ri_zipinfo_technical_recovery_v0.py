"""ZIP central-directory-only structural gate for pinned Rhode Island v3.

This is an AFTER-FIRST-FAILURE technical recovery governed by
ODSP_RI_SOLAR_V0_ZIPINFO_TECHNICAL_RECOVERY_CONTRACT.json, frozen before
this code and BEFORE any source CSV member was opened in the new route.
It does NOT touch species, timestamps, model predictions or evaluation
criteria. Input is an already-downloaded MD5-pinned ZIP byte stream.

Inspect ONLY ZIP CENTRAL DIRECTORY metadata: member names, byte sizes,
encryption flags and path safety. No ZIP member decompression or CSV
parsing occurs in this module.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import io
from pathlib import PurePosixPath
import stat
import zipfile

SOURCE_MD5 = "c66943e6c2a9aab0abce2a1eba8ce02e"
REQUIRED_CSV_BASENAMES = frozenset((
    "RI_CameraSurvey_Deployments.csv",
    "RI_CameraSurvey_Detections.csv",
))
MAX_ARCHIVE = 75_000_000
MAX_MEMBERS = 80
MAX_TOTAL_EXPANDED = 600_000_000
MAX_MEMBER_EXPANDED = 500_000_000
MAX_EXPANSION_RATIO = 60.0


@dataclass(frozen=True)
class RIZipStructureReceipt:
    schema_version: int
    contract_id: str
    archive_md5_verified: bool
    compressed_archive_bytes: int
    member_count: int
    directory_entry_count: int
    expected_csv_member_count: int
    ancillary_non_csv_entry_count: int
    total_declared_expanded_bytes: int
    largest_declared_member_bytes: int
    declared_expansion_ratio: float
    expected_named_members_present_exactly_once: bool
    content_or_detection_values_read: bool
    csv_member_contents_decompressed: bool
    source_schema_or_estimand_modified: bool
    recovery_eligibility: str

    def as_dict(self) -> dict[str,object]:
        return asdict(self)


def inspect_ri_pinned_zip_central_directory(raw: bytes) -> RIZipStructureReceipt:
    """Reject unexpected ZIP structures before extracting any CSV member.

    Raises ValueError for invalid metadata rather than returning an
    apparently eligible result. ZIP metadata do NOT verify the content
    semantics, which must remain subject to original frozen schema checks.
    """
    if not isinstance(raw,bytes) or not 0<len(raw)<=MAX_ARCHIVE:
        raise ValueError("ZIP compressed byte count outside frozen bounds")
    if hashlib.md5(raw).hexdigest()!=SOURCE_MD5:
        raise ValueError("pinned Rhode Island source MD5 mismatch")
    try:
        archive=zipfile.ZipFile(io.BytesIO(raw))
    except (zipfile.BadZipFile, ValueError) as exc:
        raise ValueError("invalid pinned source ZIP structure") from exc
    with archive:
        infos=archive.infolist()
        if not 0<len(infos)<=MAX_MEMBERS:
            raise ValueError("ZIP member count exceeds prospectively frozen recovery ceiling")
        observed_paths=set()
        csv_found=[]
        directories=0
        ancillary=0
        total=0
        largest=0
        for item in infos:
            name=item.filename.replace("\\","/")
            path=PurePosixPath(name)
            if (
                not name or name.startswith(("/", "\\"))
                or ":" in name.split("/")[0]
                or any(component in ("..", ".") for component in name.split("/"))
            ):
                raise ValueError("ZIP path is not a safe relative path")
            normalized=str(path)
            if normalized in observed_paths:
                raise ValueError("duplicate ZIP archive member name")
            observed_paths.add(normalized)
            if item.flag_bits & 1:
                raise ValueError("encrypted ZIP member forbidden")
            if stat.S_IFMT(item.external_attr >> 16)==stat.S_IFLNK:
                raise ValueError("ZIP symbolic-link member forbidden")
            if item.is_dir():
                directories+=1
                continue
            if item.file_size<0 or item.file_size>MAX_MEMBER_EXPANDED:
                raise ValueError("ZIP member expanded bytes outside frozen recovery ceiling")
            total+=item.file_size
            largest=max(largest,item.file_size)
            base=path.name
            if base.lower().endswith(".csv"):
                if base not in REQUIRED_CSV_BASENAMES:
                    raise ValueError("unexpected extra CSV member in source ZIP")
                csv_found.append(base)
            else:
                ancillary+=1
        if total>MAX_TOTAL_EXPANDED:
            raise ValueError("ZIP total declared expanded bytes outside frozen recovery ceiling")
        ratio=total/len(raw)
        if ratio>MAX_EXPANSION_RATIO:
            raise ValueError("ZIP expansion ratio outside frozen recovery ceiling")
        if len(csv_found)!=2 or set(csv_found)!=REQUIRED_CSV_BASENAMES:
            raise ValueError("exactly two pinned RI CSV members are required")
        return RIZipStructureReceipt(
            schema_version=1,
            contract_id="odsp-ri-solar-clock-v0-zipinfo-only-recovery-v1",
            archive_md5_verified=True,
            compressed_archive_bytes=len(raw),
            member_count=len(infos),
            directory_entry_count=directories,
            expected_csv_member_count=len(csv_found),
            ancillary_non_csv_entry_count=ancillary,
            total_declared_expanded_bytes=total,
            largest_declared_member_bytes=largest,
            declared_expansion_ratio=ratio,
            expected_named_members_present_exactly_once=True,
            content_or_detection_values_read=False,
            csv_member_contents_decompressed=False,
            source_schema_or_estimand_modified=False,
            recovery_eligibility="TECHNICAL_ZIP_RECOVERY_ELIGIBLE",
        )
