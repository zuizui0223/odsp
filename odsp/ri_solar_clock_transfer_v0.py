"""Solar-phase versus civil-clock diel-state prediction (new ecological lane).

This is a fresh exploratory ecological prediction contrast. It is neither
the closed Snapshot Serengeti result nor a qualified future-refit process route.

Both models predict EXACTLY the same six 4-hour *civil-clock* categories.
The solar model is fitted to an equinoctial double-anchored phase, then its
probability density is pushed forward to civil-clock bins using a conservative
exact piecewise-linear change of variables. Directly comparing log scores of
differently transformed response labels would be invalid; we never do that.

The transformation is motivated by daylength-sensitive wildlife activity,
but prospective cross-site/year transfer is a separate ecological question.
Camera detection time can still be biased by hardware, visibility and
survey targeting; astronomy alone does not identify causal behaviour.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
import hashlib
import math
from typing import Sequence
from zoneinfo import ZoneInfo

import numpy as np

VERSION = "odsp_ri_solar_vs_clock_transfer_v0"
EQUINOCTIAL_PHASE_EDGES = (0., 4., 8., 12., 16., 20., 24.)
SITE_HASH_SALT = "odsp-ri-solar-v0"
PSEUDOCOUNT = 0.5


def site_is_sealed(site_id: str, *, folds: int = 5, heldout_fold: int = 0) -> bool:
    """Outcome-blind entire-site split; repeated seasons stay together."""
    if not isinstance(site_id,str) or not site_id.strip():
        raise ValueError("site_id must be nonempty text")
    if folds != 5 or heldout_fold != 0:
        raise ValueError("frozen site fold scheme cannot change")
    digest = hashlib.sha256(
        f"{SITE_HASH_SALT}|{site_id.strip()}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") % folds == heldout_fold


def sunrise_sunset_local(
    day: date,
    latitude: float,
    longitude: float,
    *,
    timezone_name: str = "America/New_York",
) -> tuple[float, float]:
    """Approximate local apparent sunrise/sunset using NOAA solar geometry.

    Sunrise/sunset defined at apparent solar zenith 90.833 degrees.
    Output in local civil-clock fractional hours, including DST at noon.
    This approximate astronomical helper is not calibration of archived
    camera clocks or proof their source time zone is correct.
    """
    if not isinstance(day,date) or isinstance(day,datetime):
        raise ValueError("day must be a date")
    if timezone_name != "America/New_York":
        raise ValueError("this empirical lane freezes America/New_York")
    lat, lon = float(latitude), float(longitude)
    if (
        not math.isfinite(lat) or not math.isfinite(lon)
        or not -90.0 <= lat <= 90.0
        or not -180.0 <= lon <= 180.0
    ):
        raise ValueError("invalid geographic coordinates")
    doy = day.timetuple().tm_yday
    gamma = (2.0*math.pi/365.0) * (doy-1)
    eqt = 229.18 * (
        0.000075 + 0.001868*math.cos(gamma) - 0.032077*math.sin(gamma)
        - 0.014615*math.cos(2*gamma) - 0.040849*math.sin(2*gamma)
    )
    dec = (
        0.006918 - 0.399912*math.cos(gamma) + 0.070257*math.sin(gamma)
        - 0.006758*math.cos(2*gamma) + 0.000907*math.sin(2*gamma)
        - 0.002697*math.cos(3*gamma) + 0.00148*math.sin(3*gamma)
    )
    phi = math.radians(lat)
    denominator = math.cos(phi)*math.cos(dec)
    if abs(denominator)<1e-12:
        raise ValueError("polar or degenerate solar geometry")
    cos_h = (
        math.cos(math.radians(90.833)) / denominator
        - math.tan(phi)*math.tan(dec)
    )
    if not -1.0 < cos_h < 1.0:
        raise ValueError("sun never rises/sets on this date and location")
    ha_deg = math.degrees(math.acos(cos_h))
    stamp = datetime(day.year,day.month,day.day,12,tzinfo=ZoneInfo(timezone_name))
    offset_minutes = stamp.utcoffset().total_seconds() / 60.0
    local_noon_minutes = 720.0-4.0*lon-eqt+offset_minutes
    sunrise = (local_noon_minutes-4.0*ha_deg)/60.0
    sunset = (local_noon_minutes+4.0*ha_deg)/60.0
    if not 0.0 < sunrise < sunset < 24.0:
        raise ValueError("unsupported civil-day solar geometry")
    return sunrise, sunset


def equinoctial_solar_phase(
    civil_hour: float, sunrise: float, sunset: float
) -> float:
    """Two-anchor mapping: sunrise->06, sunset->18 on 24-hour phase."""
    h,sr,ss=map(float,(civil_hour,sunrise,sunset))
    if not math.isfinite(h) or not 0 <= h < 24:
        raise ValueError("civil_hour must lie in [0,24)")
    if not 0 < sr < ss < 24:
        raise ValueError("invalid sunrise/sunset")
    daylight=ss-sr
    night=24-daylight
    if sr <= h < ss:
        return 6.+12.*(h-sr)/daylight
    adjusted=h if h>=ss else h+24.
    return (18.+12.*(adjusted-ss)/night)%24.


def _phase_to_unwrapped_civil(phi: float, sr: float, ss: float) -> float:
    """Strictly monotone unwrapped inverse from phase in [0,24]."""
    daylight=ss-sr
    night=24-daylight
    if phi < 6:
        return ss+(phi+6.)*night/12.-24.
    if phi < 18:
        return sr+(phi-6.)*daylight/12.
    return ss+(phi-18.)*night/12.


def solar_phase_to_civil_bin_matrix(
    sunrise: float,
    sunset: float,
) -> np.ndarray:
    """Exact 6x6 conditional matrix P(clock_bin=j | solar_phase_bin=k).

    Assumes uniform within each four-hour SOLAR phase bin, as fitted by
    the frozen six-bin histogram. Integrates the piecewise linear inverse
    and wraps periodic civil intervals correctly around midnight.
    Every row sums to 1, and no result-bin transformation changes the
    heldout score target.
    """
    sr,ss=map(float,(sunrise,sunset))
    if not 0 < sr < ss < 24:
        raise ValueError("invalid sunrise/sunset for probability transport")
    out=np.zeros((6,6),dtype=float)
    edges=EQUINOCTIAL_PHASE_EDGES
    for k in range(6):
        left,right=edges[k:k+2]
        breaks=[left]+[v for v in (6.,18.) if left<v<right]+[right]
        for a,b in zip(breaks[:-1],breaks[1:]):
            t0=_phase_to_unwrapped_civil(a,sr,ss)
            t1=_phase_to_unwrapped_civil(b,sr,ss)
            if not t1>t0:
                raise ValueError("nonmonotone solar phase inverse")
            partial=(b-a)/4.
            for j in range(6):
                for shift in (-24.,0.,24.,48.):
                    v0=4.*j+shift
                    overlap=max(0.,min(t1,v0+4.)-max(t0,v0))
                    out[k,j]+=partial*overlap/(t1-t0)
    if not np.all(np.isfinite(out)) or np.any(out<-1e-12):
        raise ValueError("invalid probability transport matrix")
    if not np.allclose(out.sum(axis=1),1.,atol=1e-12):
        raise ValueError("solar mass failed conservation")
    return out


@dataclass(frozen=True)
class DielEvent:
    site_id: str
    species: str
    season: str
    season_year: int
    day: date
    clock_hour: float
    latitude: float
    longitude: float

    def __post_init__(self):
        if not self.site_id or not self.species:
            raise ValueError("missing physical site or species")
        if self.season not in ("winter","summer"):
            raise ValueError("only frozen winter/summer study groups admitted")
        if not 2018 <= self.season_year <= 2023:
            raise ValueError("outside study season years")
        if not isinstance(self.day,date) or isinstance(self.day,datetime):
            raise ValueError("event day must be a date")
        if not math.isfinite(self.clock_hour) or not 0<=self.clock_hour<24:
            raise ValueError("clock hour outside [0,24)")
        if any(not math.isfinite(v) for v in (self.latitude,self.longitude)):
            raise ValueError("invalid event coordinate")

    @property
    def clock_bin(self)->int:
        return min(5,int(self.clock_hour//4))

    @property
    def solar_bin(self)->int:
        sr,ss=cached_solar_times(
            self.day,round(self.latitude,5),round(self.longitude,5)
        )
        return min(5,int(equinoctial_solar_phase(
            self.clock_hour,sr,ss
        )//4))


@lru_cache(maxsize=100000)
def cached_solar_times(day:date,latitude:float,longitude:float)->tuple[float,float]:
    return sunrise_sunset_local(day,latitude,longitude)


@dataclass(frozen=True)
class DielSpeciesModel:
    species:str
    clock:tuple[float,...]
    solar:tuple[float,...]
    season_clock:dict[str,tuple[float,...]]
    season_solar:dict[str,tuple[float,...]]
    training_site_count:int
    training_event_count:int


def _histogram(
    observations:Sequence[tuple[int,float]], pseudocount:float=PSEUDOCOUNT
)->tuple[float,...]:
    bins=np.full(6,pseudocount,dtype=float)
    for category,weight in observations:
        if not 0<=category<6 or weight<0 or not math.isfinite(weight):
            raise ValueError("invalid weighted category")
        bins[category]+=weight
    return tuple((bins/bins.sum()).tolist())


def fit_species_profiles(
    train:Sequence[DielEvent],
    *,
    min_events:int=120,
    min_sites:int=8,
    min_season_events:int=25,
    min_season_sites:int=3,
)->tuple[dict[str,DielSpeciesModel],dict[str,object]]:
    """Fit only prior-year, physically disjoint training site events."""
    if (min_events,min_sites,min_season_events,min_season_sites)!=(120,8,25,3):
        raise ValueError("frozen species admission parameters changed")
    grouped:dict[str,list[DielEvent]]=defaultdict(list)
    for event in train:
        if event.season_year>2021 or site_is_sealed(event.site_id):
            raise ValueError("training contains future year or sealed site")
        grouped[event.species].append(event)
    models:dict[str,DielSpeciesModel]={}
    excluded={}
    for species,events in sorted(grouped.items()):
        sites={e.site_id for e in events}
        seasons={
            s:[e for e in events if e.season==s]
            for s in ("winter","summer")
        }
        valid=(
            len(events)>=min_events and len(sites)>=min_sites
            and all(len(seasons[s])>=min_season_events
                    and len({e.site_id for e in seasons[s]})>=min_season_sites
                    for s in ("winter","summer"))
        )
        if not valid:
            excluded[species]={
                "train_events":len(events),"train_sites":len(sites),
                "winter_events":len(seasons["winter"]),
                "summer_events":len(seasons["summer"]),
            }
            continue
        # Each site x season-year contributes equal mass within species.
        units=Counter((e.site_id,e.season,e.season_year) for e in events)
        weighted=[(e,1./units[e.site_id,e.season,e.season_year]) for e in events]
        models[species]=DielSpeciesModel(
            species=species,
            clock=_histogram([(e.clock_bin,w) for e,w in weighted]),
            solar=_histogram([(e.solar_bin,w) for e,w in weighted]),
            season_clock={
                s:_histogram([(e.clock_bin,w) for e,w in weighted if e.season==s])
                for s in ("winter","summer")
            },
            season_solar={
                s:_histogram([(e.solar_bin,w) for e,w in weighted if e.season==s])
                for s in ("winter","summer")
            },
            training_site_count=len(sites),
            training_event_count=len(events),
        )
    return models,{
        "schema_version":1,"accepted_species":sorted(models),
        "excluded_species":excluded,
        "training_events":sum(len(rows) for rows in grouped.values()),
        "training_species_count":len(grouped),
        "training_physical_sites":len({e.site_id for rows in grouped.values() for e in rows}),
        "primary_prospective_result":False,
    }


def _heldout_clock_probabilities(
    model:DielSpeciesModel,
    event:DielEvent,
    *,
    shift_date_days:int=0,
)->dict[str,np.ndarray]:
    date_to_use=event.day+timedelta(days=shift_date_days)
    sr,ss=cached_solar_times(date_to_use,round(event.latitude,5),round(event.longitude,5))
    T=solar_phase_to_civil_bin_matrix(sr,ss)
    return {
        "clock":np.asarray(model.clock,dtype=float),
        "solar":np.asarray(model.solar,dtype=float)@T,
        "clock_season":np.asarray(model.season_clock[event.season],dtype=float),
        "solar_season":np.asarray(model.season_solar[event.season],dtype=float)@T,
    }


def score_new_site_future_year(
    event:DielEvent,
    model:DielSpeciesModel,
)->dict[str,float]:
    """All proper scores target the SAME observed civil-clock time bin."""
    if event.season_year not in (2022,2023) or not site_is_sealed(event.site_id):
        raise ValueError("test event is not from sealed site in future years")
    if event.species!=model.species:
        raise ValueError("species model mismatch")
    probability=_heldout_clock_probabilities(model,event)
    false_solar=_heldout_clock_probabilities(
        model,event,shift_date_days=183
    )["solar"]
    observed=event.clock_bin
    if any(
        len(p)!=6 or not np.isfinite(p).all() or np.any(p<0)
        or not np.isclose(p.sum(),1.,atol=1e-10)
        for p in (*probability.values(),false_solar)
    ):
        raise ValueError("ill-formed heldout six-state prediction")
    score={name:math.log(float(probs[observed]))
           for name,probs in probability.items()}
    score["solar_wrong_season_sun"]=math.log(float(false_solar[observed]))
    score["solar_over_clock"]=score["solar"]-score["clock"]
    score["solar_season_over_solar"]=score["solar_season"]-score["solar"]
    score["clock_season_over_clock"]=score["clock_season"]-score["clock"]
    score["true_solar_over_wrong_sun"]=(
        score["solar"]-score["solar_wrong_season_sun"]
    )
    return score


def summarize_site_level_transfer(
    scored:Sequence[tuple[DielEvent,dict[str,float]]],
    *,
    draws:int=2000,
    seed:int=2026100803,
)->dict[str,object]:
    """Bootstrap PHYSICAL sites, never rows/cameras/site-years as iid."""
    if draws!=2000 or seed!=2026100803:
        raise ValueError("frozen bootstrap schedule changed")
    names=(
        "solar_over_clock","solar_season_over_solar",
        "clock_season_over_clock","true_solar_over_wrong_sun"
    )
    site_season:dict[tuple[str,str],dict[str,list[float]]]=defaultdict(
        lambda:defaultdict(list)
    )
    for event,row in scored:
        if not site_is_sealed(event.site_id) or event.season_year<2022:
            raise ValueError("validation score not at an authorized site/year")
        for name in names:
            value=row[name]
            if not math.isfinite(value):
                raise ValueError("nonfinite heldout log-score comparison")
            site_season[event.site_id,event.season][name].append(value)
    site_average={
        group:{name:float(np.mean(vals)) for name,vals in values.items()}
        for group,values in site_season.items()
    }
    result={
        "schema_version":1,
        "method_version":VERSION,
        "inference_target":"camera-detected local-clock category at new sites and later seasons, not underlying activity",
        "independent_sampling_unit":"physical camera site",
        "bootstrap_site_iid_sampling_proven":False,
        "prior_empirical_endpoints_reclassified":False,
        "season_groups":{},
    }
    rng=np.random.default_rng(seed)
    for season in ("winter","summer"):
        sites=sorted(site for site,s in site_average if s==season)
        season_rows={}
        for name in names:
            values=np.asarray([site_average[site,season][name] for site in sites])
            mean=float(values.mean()) if len(values) else None
            lower=None
            if len(sites)>=8:
                ix=rng.integers(len(values),size=(draws,len(values)))
                lower=float(np.quantile(values[ix].mean(axis=1),0.05))
            season_rows[name]={
                "mean":mean,"one_sided_95_percent_cluster_bootstrap_lower":lower
            }
        result["season_groups"][season]={
            "unique_physical_site_count":len(sites),
            "metrics":season_rows,
        }
    result["all_season_site_floor_met"]=all(
        result["season_groups"][s]["unique_physical_site_count"]>=8
        for s in ("winter","summer")
    )
    result["solar_transfer_both_seasons_positive"]=(
        result["all_season_site_floor_met"]
        and all(
            result["season_groups"][s]["metrics"]["solar_over_clock"]
            ["one_sided_95_percent_cluster_bootstrap_lower"]>0
            for s in ("winter","summer")
        )
    )
    result["physical_negative_control_both_seasons_positive"]=(
        result["all_season_site_floor_met"]
        and all(
            result["season_groups"][s]["metrics"]["true_solar_over_wrong_sun"]
            ["one_sided_95_percent_cluster_bootstrap_lower"]>0
            for s in ("winter","summer")
        )
    )
    result["scientific_status"]=(
        "EXPLORATORY_SOLAR_TRANSPORT_SIGNAL"
        if (result["solar_transfer_both_seasons_positive"]
            and result["physical_negative_control_both_seasons_positive"])
        else "EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE"
    )
    return result
