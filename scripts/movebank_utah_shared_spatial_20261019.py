"""Source-locked shared-cell/month species contrasts with spatial-block sensitivity.

First reproduce ALL six already published q differences byte-numerically from
the original public Utah provider-MD5 ZIP, before opening night/day components
and block-level summaries. Publication outputs contain no raw GPS or cell IDs.
"""
import argparse,json,math,random
from collections import defaultdict
from pathlib import Path
from statistics import mean,median
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download,daylength
from scripts.movebank_solar_movement_20261019 import valid_interval
from scripts.movebank_utah_four_taxa_solar_20261019 import (
    extract_time_only_original_source,CONTRACT as UTAH_ORIGINAL
)
from scripts.movebank_utah_diel_photoperiod_20261019 import compare_sites

CONTRACT=HERE/"research/MOVEBANK_UTAH_SHARED_SPATIAL_BLOCK_V0_20261019.json"

def source_cell_month(animals):
    """The exact previous within-animal/calendar-year admitted cell-month roster."""
    cells=defaultdict(lambda:defaultdict(list))
    for animal,original_hour in animals.items():
        ordered=sorted(original_hour.values())
        day=defaultdict(lambda:{"day":[],"night":[],"lat":[],"lon":[]})
        for a,b in zip(ordered,ordered[1:]):
            v=valid_interval(a[0],a[1],a[2],b[0],b[1],b[2])
            if v is None:continue
            local_date,part,speed,hour,lat=v
            item=day[local_date]
            item[part].append(speed)
            item["lat"].append(lat)
            item["lon"].append((a[2]+b[2])/2)
        by_year=defaultdict(list)
        for d,v in day.items():
            if len(v["day"])<3 or len(v["night"])<3:continue
            lat=mean(v["lat"]);lon=mean(v["lon"])
            dn=math.log1p(median(v["day"]))
            nn=math.log1p(median(v["night"]))
            cell=(math.floor(lat),math.floor(lon),d.year,d.month)
            by_year[d.year].append((cell,nn-dn,nn,dn))
        for year,valid_days in by_year.items():
            if len(valid_days)<10:continue
            for cell,q,n,d in valid_days:
                cells[cell][animal].append((q,n,d))
    result={}
    for key,per_animal in cells.items():
        eligible=[
            tuple(mean(v[k] for v in measures) for k in range(3))
            for measures in per_animal.values() if len(measures)>=3
        ]
        if len(eligible)<3:continue
        q,n,d=tuple(mean(x[k] for x in eligible) for k in range(3))
        result[key]=(q,n,d)
    return result

def percentile(values,p):
    a=sorted(values)
    if not a:return None
    rank=(len(a)-1)*p
    lo=math.floor(rank);hi=math.ceil(rank)
    return a[lo]+(rank-lo)*(a[hi]-a[lo])

def cluster_interval(values,seed=20261019,n=2000):
    if len(values)<5:return None
    rng=random.Random(seed)
    samples=[mean(values[rng.randrange(len(values))] for _ in values) for _ in range(n)]
    return [percentile(samples,.025),percentile(samples,.975)]

def summarize_pair(a,b,source_map):
    common=sorted(set(source_map[a])&set(source_map[b]))
    if not common:
        return {"taxa":[a,b],"status":"unsupported","shared_cell_months":0}
    contrast={}
    for key in common:
        # q, night absolute, day absolute. Never export underlying block IDs.
        va=source_map[a][key];vb=source_map[b][key]
        values=tuple(va[i]-vb[i] for i in range(3))
        if abs(values[0]-(values[1]-values[2]))>1e-11:
            raise ValueError("Shared-space diel contrast algebra failed")
        contrast[key]=values
    count=len(common)
    cellmonth=tuple(mean(contrast[key][i] for key in common) for i in range(3))
    by_geogrid=defaultdict(list)
    for (lat,lon,year,month),v in contrast.items():
        by_geogrid[(lat,lon)].append(v)
    equalblocks=[
        tuple(mean(v[i] for v in vals) for i in range(3))
        for vals in by_geogrid.values()
    ]
    blocks=len(equalblocks)
    blockmean=tuple(mean(v[i] for v in equalblocks) for i in range(3))
    loo=None
    if blocks>=2:
        q=[v[0] for v in equalblocks]
        loo_means=[(sum(q)-x)/(len(q)-1) for x in q]
        loo=[min(loo_means),max(loo_means)]
    return {
      "taxa":[a,b],"status":"complete_source_spatial_sensitivity",
      "shared_cell_months":count,"distinct_geographic_1degree_spatial_blocks":blocks,
      "distinct_calendar_years":len({k[2] for k in common}),
      "equal_cellmonth_night_minus_day_log1p_difference_a_minus_b":cellmonth[0],
      "equal_cellmonth_night_log1p_difference_a_minus_b":cellmonth[1],
      "equal_cellmonth_day_log1p_difference_a_minus_b":cellmonth[2],
      "equal_spatial_block_night_minus_day_log1p_difference_a_minus_b":blockmean[0],
      "equal_spatial_block_night_log1p_difference_a_minus_b":blockmean[1],
      "equal_spatial_block_day_log1p_difference_a_minus_b":blockmean[2],
      "spatial_block_cluster_bootstrap_95_interval":cluster_interval([v[0] for v in equalblocks]),
      "leave_one_geographic_spatial_block_range_NOT_CI":loo,
      "limitation":"Grid/month is an observational grouping, not co-observed tagged animals or independent ecosystems; historical wildlife sampling and detection cannot identify physiology or competition."
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    freeze=json.loads(CONTRACT.read_text())
    if freeze["version"]!="utah-shared-gridmonth-spatial-block-ecology-v0":
        raise ValueError("Unregistered outcome-sensitive route")
    orig=json.loads(UTAH_ORIGINAL.read_text())["source"]
    if set(orig["catalog_taxa"])!=set(freeze["source"]["fixed_four_taxa"]):
        raise ValueError("Original source taxa changed")
    output={"original_source":"Movebank Utah four-ungulate MD5-pinned multi-species study",
        "source_doi":orig["doi"],
        "estimator":"Post-first-outcome grid-cluster and day/night absolute component ecological follow-up",
        "source_first_six_reproduced":False,
        "pairs":[]}
    path=args.out/"original_utah_provider.zip"
    try:
        matches=[x for x in original_files(orig["package_uuid"]) if x["bitstream_uuid"]==orig["original_bitstream_uuid"]]
        if len(matches)!=1 or matches[0]["checksum"]["value"].lower()!=orig["original_md5"].lower():
            raise ValueError("Provider original file identity or MD5 metadata mismatch")
        output["original_source_md5_verified"]=checksum_and_download(matches[0],path)
        all_animals,counts,unknown=extract_time_only_original_source(path,orig["catalog_taxa"])
        output["source_taxa_original_rows"]={name:counts[name]["rows"] for name in orig["catalog_taxa"]}
        output["source_other_taxon_rows"]=unknown
        per_taxon={}
        for taxon in orig["catalog_taxa"]:
            per_taxon[taxon]=source_cell_month(all_animals[taxon])
            all_animals[taxon].clear()
        # This verification cannot use old entire GPS outcome: it independently
        # recreates the pre-existing 6 cell-month q contrasts in this new reader.
        previous=compare_sites({k:{cell:row[0] for cell,row in v.items()} for k,v in per_taxon.items()})
        assert len(previous)==6
        for x in previous:
            name="|".join(x["taxa"])
            oldvalue=freeze["source_effect_replay"][name]
            oldcount=freeze["source_overlap_count_replay"][name]
            if x["shared_1degree_calendar_month_cells"]!=oldcount:
                raise ValueError("Previously frozen common site-month opportunity count altered "+name)
            delta=x["diel_contrast_a_minus_b_on_common_cells"]
            if delta is None or abs(delta-oldvalue)>1e-11:
                raise ValueError("Previously frozen shared cell-month diel effect changed "+name)
        output["source_first_six_reproduced"]=True
        # Only after source-replay validation calculate new component/cluster outcomes.
        names=orig["catalog_taxa"]
        for i,a in enumerate(names):
            for b in names[i+1:]:
                result=summarize_pair(a,b,per_taxon)
                output["pairs"].append(result)
                print("UTAH_SPATIAL_BLOCK_PAIR "+json.dumps(result,sort_keys=True),flush=True)
        output["status"]="six_original_pairs_replayed_new_spatial_block_results"
    except Exception as e:
        output.update(status="source_hold",error=f"{type(e).__name__}: {e}")
    finally:
        path.unlink(missing_ok=True)
    (args.out/"utah_spatial_block_ecological_results.json").write_text(
        json.dumps(output,indent=2,ensure_ascii=False)+"\n")
    print("UTAH_SPATIAL_BLOCK_SUMMARY "+json.dumps({
        "status":output["status"],
        "six_first_effects_reproduced":output["source_first_six_reproduced"],
        "supported_pairs":len(output["pairs"]),
        "spatial_bootstrap_available":sum(x.get("spatial_block_cluster_bootstrap_95_interval") is not None for x in output["pairs"])
    },sort_keys=True))
if __name__=="__main__":main()
