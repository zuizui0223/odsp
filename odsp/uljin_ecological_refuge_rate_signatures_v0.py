"""Two biologically distinct temporal-refuge signatures at matched daylength.

H1 daylight CORE vs daylight EDGES, H2 NIGHT vs all DAYLIGHT;
all four ungulates, original 41 matched daylength pairs and
the SAME eligible original physical camera station×date roster.

Not a new time transform comparison. Critically: only ORIGINAL
independently authenticated source camera operation HOUR intervals
may enter denominators. An eligible site×paired date must have
positive operation in ALL THREE solar zones on BOTH matched dates;
selection may NEVER depend on an ungulate event count.

Outputs DESCRIPTIVE detected-event rate per 100 verified hours and
two log-ratios-of-ratios, no pseudo-count smoothing or ecological
causal inference. Without independently calibrated q the latent
animal activity and temperature/human mechanism remain unidentified.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping,Sequence
from datetime import date
from math import isfinite,log

from .uljin_ecological_temporal_refuge_v0 import (
    TAXA,ZONES,BRANCHES,assert_frozen_ecology,
    parse_clock_minutes,solar_zone_operation_minutes,
    classify_event_time
)
from .uljin_photoperiod_mirror_design_v0 import (
    generate_preoutcome_2022_mirror_calendar
)

METHOD="uljin_matched_daylength_ecological_zone_signature_v0"
CONTRAST_IDS=("CORE_VS_EDGE","NIGHT_VS_DAYLIGHT")


def _freeze(plan:Mapping[str,object],ecology:Mapping[str,object],
            calendar:Mapping[str,object])->list[dict[str,object]]:
    if not isinstance(plan,Mapping) or not isinstance(ecology,Mapping):
        raise ValueError("original biology zone rate contrast frozen plan missing")
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
            "FROZEN_BEFORE_ORIGINAL_ECOBANK_2022_EVENT_AND_HOURLY_EFFORT_OUTCOME_OPEN"
        or plan.get("parent_ecology_pr")!=264
        or plan.get("original_41_calendar_pairs_and_82_dates_immutable") is not True
        or plan.get("original_four_taxa")!=list(TAXA)
        or plan.get("biological_zone_categories")!=list(ZONES)
        or [x.get("id") for x in plan.get("rate_contrasts",[])]!=list(CONTRAST_IDS)
        or plan.get("no_real_data_available_at_freeze") is not True
    ):
        raise ValueError("original four-species matched-daylength biology plan modified")
    assert_frozen_ecology(ecology,calendar)
    pairs=generate_preoutcome_2022_mirror_calendar(calendar)["matched_dates"]
    if len(pairs)!=41:
        raise ValueError("original 41 daylength matched date pairs altered")
    return pairs


def _eligible_clock_minutes(
    operation:Mapping[tuple[str,str],Sequence[tuple[float,float]]],
    station:str,day_text:str
)->tuple[tuple[float,float],...]:
    values=operation[(station,day_text)]
    # solar_zone_operation_minutes independently rejects overlaps and
    # malformed or out-of-day intervals; preserve that guard.
    solar_zone_operation_minutes(date.fromisoformat(day_text),values)
    return tuple((float(a),float(b)) for a,b in values)


def _rate(events:int,minutes:float)->float:
    if minutes<=0 or not isfinite(minutes):
        raise ValueError("verified original source operation exposure must be positive")
    if events<0:
        raise ValueError("real ungulate independent-event count cannot be negative")
    return float(events)/(minutes/60.)*100.


def _signed_log_rate_interaction(
    early_left:float,early_right:float,
    late_left:float,late_right:float
)->dict[str,object]:
    if not all(isfinite(v) and v>=0 for v in
               (early_left,early_right,late_left,late_right)):
        raise ValueError("invalid source-frozen rate cell")
    if min(early_left,early_right,late_left,late_right)==0:
        return {
            "status":"UNDEFINED_ZERO_EVENT_RATE_NO_PSEUDOCOUNT",
            "falling_minus_rising_log_rate_ratio":None,
            "direction":None
        }
    value=log(late_left/late_right)-log(early_left/early_right)
    return {
        "status":"DESCRIPTIVE_FINITE_DETECTION_RATE_CONTRAST_ONLY",
        "falling_minus_rising_log_rate_ratio":float(value),
        "direction":(
            "positive" if value>0 else
            "negative" if value<0 else "zero"),
    }


def compute_matched_daylength_zone_signatures(
    plan:Mapping[str,object],ecology:Mapping[str,object],
    calendar:Mapping[str,object],
    event_rows:Sequence[Mapping[str,str]]|None,
    verified_operation_intervals:Mapping[
        tuple[str,str],Sequence[tuple[float,float]]
    ]|None,
    *,
    independently_verified_v1p1_event_member:bool=False,
    independently_verified_original_operation_log:bool=False,
)->dict[str,object]:
    pairs=_freeze(plan,ecology,calendar)
    if (independently_verified_v1p1_event_member is not True
        or independently_verified_original_operation_log is not True):
        return {
            "status":"HOLD_REAL_EVENT_AND_INDEPENDENT_HOURLY_OPERATION_SOURCE_NOT_ATTESTED",
            "rate_effect_computed":False,
            "calendar_pairs_preserved":41,
            "four_species_preserved":list(TAXA)
        }
    if not isinstance(event_rows,(list,tuple)) or not isinstance(
        verified_operation_intervals,Mapping):
        raise ValueError("source original event and hour-exact operating members required")
    if not verified_operation_intervals:
        return {"status":"HOLD_EMPTY_SOURCE_PHYSICAL_CAMERA_OPERATION_ROSTER",
                "rate_effect_computed":False}
    roster=set()
    for key in verified_operation_intervals:
        if (not isinstance(key,tuple) or len(key)!=2 or
            not isinstance(key[0],str) or not key[0]):
            raise ValueError("malformed independently identified physical camera station")
        roster.add(key[0])
    all_dates={
        p[k] for p in pairs
        for k in ("ascending_date","descending_date")
    }
    expected={(station,day) for station in roster for day in all_dates}
    if set(verified_operation_intervals)!=expected:
        return {
            "status":"HOLD_INCOMPLETE_INDEPENDENT_CAMERA_STATION_DATE_OPERATION",
            "rate_effect_computed":False,
            "expected_camera_date_cells":len(expected),
            "provided_camera_date_cells":len(verified_operation_intervals)
        }
    durations={}
    verified_intervals={}
    for station,day in sorted(expected):
        source_intervals=_eligible_clock_minutes(
            verified_operation_intervals,station,day)
        verified_intervals[(station,day)]=source_intervals
        durations[(station,day)]=solar_zone_operation_minutes(
            date.fromisoformat(day),source_intervals)

    # Only the independent camera operation LOG determines inclusion.
    included=[]
    excluded=0
    for pair_index,pair in enumerate(pairs):
        a,b=pair["ascending_date"],pair["descending_date"]
        for station in sorted(roster):
            if all(durations[(station,day)][zone]>0
                   for day in (a,b) for zone in ZONES):
                included.append((station,pair_index,a,b))
            else:
                excluded+=1
    if not included:
        return {
            "status":"HOLD_NO_COMMON_SITE_PAIR_WITH_POSITIVE_SOURCE_HOURS_ALL_ZONES",
            "rate_effect_computed":False,
            "physical_station_count_from_original_operation_log":len(roster),
            "original_calendar_pairs":41
        }
    included_days={
        (station,a) for station,_,a,_ in included
    }|{(station,b) for station,_,_,b in included}
    eligible_day_branch={
        (station,a):"rising" for station,_,a,_ in included
    }|{
        (station,b):"falling" for station,_,_,b in included
    }
    counts=Counter()
    events_outside_calendar=0
    events_outside_eligible_effort=0
    eligible_events=0
    for e in event_rows:
        if not isinstance(e,Mapping) or any(
            k not in e for k in ("Station","Date","Time","Species")
        ):
            raise ValueError("source originally released event member columns missing")
        day=e["Date"]
        # Validate every row's date, not only the ones selected for ecology.
        try:
            parsed=date.fromisoformat(day)
        except (TypeError,ValueError) as exc:
            raise ValueError("malformed source original calendar date") from exc
        if parsed.isoformat()!=day:
            raise ValueError("malformed original Date YYYY-MM-DD")
        if day not in all_dates:
            events_outside_calendar+=1
            continue
        station=e["Station"]
        if station not in roster:
            return {
                "status":"HOLD_EVENT_STATION_NOT_IN_INDEPENDENT_CAMERA_OPERATION_ROSTER",
                "rate_effect_computed":False,
                "unknown_station_label":str(station)
            }
        if e["Species"] not in TAXA:
            raise ValueError("original matched-date ungulate taxonomy unexpected")
        minute=parse_clock_minutes(e["Time"])
        if not any(a<=minute<b for a,b in verified_intervals[(station,day)]):
            return {
                "status":"HOLD_SOURCE_EVENT_OUTSIDE_VERIFIED_CAMERA_OPERATION",
                "rate_effect_computed":False,
                "source_conflicting_station":station,
                "source_conflicting_date":day
            }
        if (station,day) not in included_days:
            events_outside_eligible_effort+=1
            continue
        zone=classify_event_time(parsed,minute)
        counts[(e["Species"],eligible_day_branch[(station,day)],zone)]+=1
        eligible_events+=1

    hours=Counter()
    for station,_,a,b in included:
        for branch,day in (("rising",a),("falling",b)):
            for zone,minutes in durations[(station,day)].items():
                hours[(branch,zone)]+=minutes/60.
    branch_days={
        branch:sum(hours[(branch,z)] for z in ZONES)
        for branch in BRANCHES
    }
    result=[]
    for taxon in TAXA:
        entries={}
        for branch in BRANCHES:
            r={}
            for z in ZONES:
                n=counts[(taxon,branch,z)]
                h=hours[(branch,z)]
                r[z]={
                    "independent_events":int(n),
                    "source_camera_hours":h,
                    "detections_per_100_verified_camera_hours":_rate(n,h*60)
                }
            night=r["night"]["detections_per_100_verified_camera_hours"]
            total_day_n=r["daylight_core"]["independent_events"]+r[
                "daylight_edge"]["independent_events"]
            total_day_h=r["daylight_core"]["source_camera_hours"]+r[
                "daylight_edge"]["source_camera_hours"]
            r["combined_daylight"]={
                "independent_events":total_day_n,
                "source_camera_hours":total_day_h,
                "detections_per_100_verified_camera_hours":(
                    total_day_n/total_day_h*100.)
            }
            entries[branch]=r
        e,f=entries["rising"],entries["falling"]
        c1=_signed_log_rate_interaction(
            e["daylight_core"]["detections_per_100_verified_camera_hours"],
            e["daylight_edge"]["detections_per_100_verified_camera_hours"],
            f["daylight_core"]["detections_per_100_verified_camera_hours"],
            f["daylight_edge"]["detections_per_100_verified_camera_hours"])
        c2=_signed_log_rate_interaction(
            e["night"]["detections_per_100_verified_camera_hours"],
            e["combined_daylight"]["detections_per_100_verified_camera_hours"],
            f["night"]["detections_per_100_verified_camera_hours"],
            f["combined_daylight"]["detections_per_100_verified_camera_hours"])
        result.append({
            "Species":taxon,
            "zone_rates_by_branch":entries,
            "H1_core_vs_daylight_edge":c1,
            "H2_night_vs_all_daylight":c2,
            "total_matched_pair_events":sum(
                counts[(taxon,br,z)] for br in BRANCHES for z in ZONES)
        })
    return {
        "status":"VERIFIED_EFFORT_ADJUSTED_DETECTION_RATE_SIGNATURES_DESCRIPTIVE_ONLY",
        "rate_effect_computed":True,
        "real_latent_animal_activity_or_thermal_cause_estimated":False,
        "original_41_calendar_pairs_unchanged":True,
        "all_four_species_reported_including_zero_event":True,
        "original_physical_camera_roster_size":len(roster),
        "operation_only_selected_site_pair_cells":len(included),
        "excluded_site_pair_cells_based_only_on_operation_hours":excluded,
        "source_events_selected_for_zone_descriptive_rates":eligible_events,
        "source_events_outside_original_82_dates":events_outside_calendar,
        "source_events_with_observed_hours_but_excluded_pair_support":
            events_outside_eligible_effort,
        "all_three_original_zone_camera_hours_by_branch":[{
            "branch":br,"zone":z,"camera_hours":hours[(br,z)]
        } for br in BRANCHES for z in ZONES],
        "four_ungulate_ecological_detection_rate_signatures":result,
        "site_exposure_not_species_event_selection":True,
        "external_detector_q_NOT_calibrated_no_true_activity_zeitgeber_claim":True,
        "no_independent_site_population_significance_claim":True,
    }
