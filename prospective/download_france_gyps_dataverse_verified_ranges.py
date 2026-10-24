#!/usr/bin/env python3
"""Resumable-by-segment HTTP byte-range downloader for immutable Dataverse ZIP.

The official Dataverse API returned HTTP 206 with Accept-Ranges: bytes in
source run 39722441215. Use only that original published URL and verify
every segment's Content-Range and total source MD5 before source analysis.
This is a transport repair, NOT a biological eligibility modification.
"""
from __future__ import annotations
import argparse,hashlib,os,time,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

URL="https://data.indores.fr/api/access/datafile/5114"
TOTAL=1093170227
MD5="b18cc8004d311d19ff24060f655178bf"
CHUNK=64*1024*1024


def planned_ranges(total=TOTAL,chunk=CHUNK):
    if total<=0 or chunk<=0:raise ValueError("Bad source size/chunk")
    out=[]
    for i,start in enumerate(range(0,total,chunk)):
        end=min(total-1,start+chunk-1)
        out.append((i,start,end))
    assert out[0][1]==0 and out[-1][2]==total-1
    return out


def read_chunk(partdir,spec,attempts=4):
    idx,start,end=spec
    expected=end-start+1
    part=partdir/f"{idx:04d}.part"
    if part.exists() and part.stat().st_size==expected:
        return idx,expected,True
    for n in range(attempts):
        part.unlink(missing_ok=True)
        request=urllib.request.Request(URL,headers={
            "Range":f"bytes={start}-{end}",
            "Accept":"application/octet-stream",
            "User-Agent":"ODSP-original-public-archive-range-hash-verified/1.0"
        })
        try:
            with urllib.request.urlopen(request,timeout=210) as response:
                if response.status!=206:
                    raise ValueError("Official source ignored exact byte range")
                actual_range=response.headers.get("Content-Range","")
                if actual_range!=f"bytes {start}-{end}/{TOTAL}":
                    raise ValueError("Unexpected source segment Content-Range "+actual_range)
                written=0
                with part.open("wb") as fp:
                    for block in iter(lambda:response.read(1<<20),b""):
                        written+=len(block);fp.write(block)
            if written!=expected:raise IOError(f"Short range {idx}: {written} vs {expected}")
            return idx,written,False
        except (OSError,urllib.error.URLError,ValueError) as e:
            part.unlink(missing_ok=True)
            if n==attempts-1:raise
            time.sleep(3*(n+1))
    raise RuntimeError("Unreachable")


def assemble(parts,target,ranges):
    md5=hashlib.md5()
    total=0
    with target.open("wb") as dst:
        for i,start,end in ranges:
            part=parts/f"{i:04d}.part"
            expected=end-start+1
            if part.stat().st_size!=expected:
                raise ValueError("Source segment bytes changed")
            with part.open("rb") as src:
                for block in iter(lambda:src.read(1<<20),b""):
                    dst.write(block);md5.update(block);total+=len(block)
    if total!=TOTAL or md5.hexdigest()!=MD5:
        target.unlink(missing_ok=True)
        raise ValueError("Combined public source differs from published byte count/MD5")
    return total,md5.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--parallel",type=int,default=3)
    args=p.parse_args()
    if not(1<=args.parallel<=4):raise ValueError("Use 1-4 parallel range fetches")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    parts=args.out.parent/(args.out.name+".ranges")
    parts.mkdir(parents=True,exist_ok=True)
    ranges=planned_ranges()
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures=[executor.submit(read_chunk,parts,item) for item in ranges]
        for f in as_completed(futures):
            idx,n,cached=f.result()
            print(f"Dataverse Range {idx+1}/{len(ranges)}: {n} bytes, cached={cached}",flush=True)
    total,md5=assemble(parts,args.out,ranges)
    for i,_,_ in ranges:(parts/f"{i:04d}.part").unlink()
    parts.rmdir()
    print(f"Verified original public source: bytes={total}, md5={md5}",flush=True)


if __name__=="__main__":
    main()
