#!/usr/bin/env python3
"""Source-derived station×clock-window reanalysis, Jeong et al. 2025 Tables 1-2.

11 public camera IDs, each with 24 author-tabulated clock-hour rows.
Only derived three-block counts are preserved here, NOT original event CSV.
01–06 and 19–24 are *published row labels*, not verified solar-night hours.
No source camera ON/OFF, individual independence, detector q or causal claims.
"""
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json"
SITES=("G1","G3","G4","G9","G12","G17","G19","G21","G22","M1","M2")
WINDOWS=("01to06","07to18","19to24")
SPECIES=("water_deer","wild_boar")
STATUS="PUBLISHED_11_CAMERA_CLOCK_WINDOWS_REANALYZED_ONLY"

def read_source_contract(c):
    if (c.get("schema_version")!=1 or
        c.get("contract_id")!="bukhansan_2025_original_published_site_hour_derivative_v1" or
        c.get("stage")!="SOURCE_PUBLISHED_POST_OUTCOME_MANUAL_PDF_TABLE_VISION_VERIFIED_EXPLORATORY" or
        c["origin"].get("doi")!="10.14397/jals.2025.59.5.111" or
        c["origin"].get("reported_operated_days")!=83 or
        c["origin"].get("protected_precise_camera_GPS_accessed") is not False or
        len(c.get("limitations",{}))!=10 or any(c["limitations"].values())):
        raise ValueError("HOLD_WRONG_SOURCE_OR_INFERENCE_CONTRACT")
    if c["analysis"].get("selected_postpublication_equal_six_row_windows")!={
         "01to06":[1,2,3,4,5,6],"19to24":[19,20,21,22,23,24]}:
        raise ValueError("HOLD_CLOCK_WINDOW_CHANGED")
    rows=c["derived_publication_site_six_hour_window_counts"]
    if [x["site"] for x in rows]!=list(SITES) or [x["habitat"] for x in rows]!=["Forest"]*9+["Wetland"]*2:
        raise ValueError("HOLD_SOURCE_SITE_ROSTER")
    checks=c["published_table_independent_checks"]
    if (checks["water_deer_total"],checks["wild_boar_total"],checks["total"])!=(184,273,457):
        raise ValueError("HOLD_AUTHOR_SOURCE_TOTALS")
    for sp in SPECIES:
        h=checks["printed_hourly_both_species_totals"][sp]
        if len(h)!=24 or any(not isinstance(v,int) or v<0 for v in h):
            raise ValueError("HOLD_BAD_HOUR_VECTOR")
        for window,index in [("01to06",range(0,6)),("07to18",range(6,18)),("19to24",range(18,24))]:
            total=0
            for x in rows:
                d=x[sp]
                if set(d)!=set(WINDOWS) or any(not isinstance(v,int) or v<0 for v in d.values()):
                    raise ValueError("HOLD_INVALID_TABLE_VALUES")
                total+=d[window]
            if total!=sum(h[i] for i in index):
                raise ValueError("HOLD_SITE_HOUR_MARGINS_DISAGREE")
        if sum(h)!=checks[sp+"_total"]:
            raise ValueError("HOLD_HOUR_TOTAL_NOT_PUBLISHED")
        for habitat in ("Forest","Wetland"):
            if sum(sum(x[sp].values()) for x in rows if x["habitat"]==habitat)!=checks["species_by_habitat"][sp][habitat]:
                raise ValueError("HOLD_PUBLISHED_HABITAT_COUNTS_DISAGREE")
    return rows

def stratified(rows):
    score=variance=ad=bc=0.
    contributions=[]
    for r in rows:
        w=r["water_deer"];b=r["wild_boar"]
        a,bb,c,d=w["01to06"],w["19to24"],b["01to06"],b["19to24"]
        n=a+bb+c+d
        if n<2 or min(a+bb,c+d,a+c,bb+d)==0:continue
        expected=(a+bb)*(a+c)/n
        v=(a+bb)*(c+d)*(a+c)*(bb+d)/(n*n*(n-1))
        score+=a-expected; variance+=v; ad+=a*d/n;bc+=bb*c/n
        contributions.append({"site":r["site"],"score":round(a-expected,9)})
    if variance==0 or bc==0:
        return {"status":"NO_INFORMATIVE_STATION_OR_MH_DENOMINATOR"}
    chi=score*score/variance
    return {"n_informative_sites":len(contributions),
      "site_score_terms":contributions,
      "mh_morning_to_evening_water_vs_boar_OR":round(ad/bc,9),
      "approx_CMH_chi_square":round(chi,9),
      "UNVALIDATED_EVENT_INDEPENDENCE_p":round(math.erfc(math.sqrt(chi/2)),9),
      "cluster_robust_biological_significance":False,
      "score":round(score,9)}

def analyze(c):
    rows=read_source_contract(c)
    profiles=[]
    for r in rows:
        w=r["water_deer"];b=r["wild_boar"]
        wn=w["01to06"]+w["19to24"];bn=b["01to06"]+b["19to24"]
        delta=w["01to06"]/wn-b["01to06"]/bn if wn>0 and bn>0 else None
        profiles.append({"site":r["site"],"habitat":r["habitat"],
          "water_deer_all":sum(w.values()),"wild_boar_all":sum(b.values()),
          "water_deer_late_01to06":w["01to06"],"water_deer_early_19to24":w["19to24"],
          "wild_boar_late_01to06":b["01to06"],"wild_boar_early_19to24":b["19to24"],
          "within_camera_late_share_difference":round(delta,9) if delta is not None else None})
    defined=[x for x in profiles if x["within_camera_late_share_difference"] not in (None,0)]
    positive=sum(x["within_camera_late_share_difference"]>0 for x in defined)
    n=len(defined)
    m=min(positive,n-positive)
    signp=min(1,2*sum(math.comb(n,k) for k in range(m+1))/2**n) if n>0 else 1.
    totals={sp:{win:sum(row[sp][win] for row in rows) for win in WINDOWS} for sp in SPECIES}
    w,b=totals["water_deer"],totals["wild_boar"]
    pooled=(w["01to06"]/w["19to24"])/(b["01to06"]/b["19to24"])
    return {"status":STATUS,"source_doi":c["origin"]["doi"],
      "count_grain":"DERIVED_FROM_PUBLISHED_11_STATION_X_24_HOUR_TABLES",
      "original_full_hour_table_or_raw_events_embedded":False,
      "all_11_public_station_code_summaries_with_zeros":profiles,
      "both_species_detected_site_count":sum(x["water_deer_all"]>0 and x["wild_boar_all"]>0 for x in profiles),
      "published_3_window_source_counts":totals,
      "pooled_water_vs_boar_late_early_odds_ratio":round(pooled,9),
      "site_direction_diagnostic":{"water_deer_later_count":positive,"boar_later_count":n-positive,
        "n_non_ties":n,"exact_two_sided_sign_p_not_independent_site_validated":round(signp,9)},
      "all_site_MH_CMH_PHOTO_INDEPENDENCE_NOT_VALIDATED":stratified(rows),
      "exclude_M2_MH_CMH_PHOTO_INDEPENDENCE_NOT_VALIDATED":stratified([x for x in rows if x["site"]!="M2"]),
      "forest_only_MH_CMH_PHOTO_INDEPENDENCE_NOT_VALIDATED":stratified([x for x in rows if x["habitat"]=="Forest"]),
      "wetland_only_MH_CMH_PHOTO_INDEPENDENCE_NOT_VALIDATED":stratified([x for x in rows if x["habitat"]=="Wetland"]),
      "M2_share_of_water_deer_published_events":round(next(x["water_deer_all"] for x in profiles if x["site"]=="M2")/184,9),
      "M2_share_of_wild_boar_published_events":round(next(x["wild_boar_all"] for x in profiles if x["site"]=="M2")/273,9),
      "hour_exact_operating_camera_effort_verified":False,
      "source_date_phase_recoverable":False,
      "genuine_site_cluster_independence_verified":False,
      "causal_mechanism_or_original_Uljin_41_pair_claimed":False}

if __name__=="__main__":
    print(json.dumps(analyze(json.loads(PLAN.read_text())),indent=2,ensure_ascii=False,sort_keys=True))
