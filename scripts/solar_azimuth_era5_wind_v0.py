"""ERA5 hourly environmental vectors for original-GPS solar-bearing ecology.

Derived, optional weather measurement; NEVER treat reanalysis wind as measured
bird flight-altitude wind or shortwave as actual animal solar exposure.
No GPS coordinates, individual IDs, UTC timestamps or weather URLs are emitted.
"""
from __future__ import annotations
from datetime import datetime
import hashlib
import json
import math
import time
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
from urllib.request import Request,urlopen

API="https://archive-api.open-meteo.com/v1/archive"
FIELDS=("wind_speed_100m","wind_direction_100m","shortwave_radiation","temperature_2m")
UNITS={"wind_speed_100m":"m/s","wind_direction_100m":"°",
       "shortwave_radiation":"W/m²","temperature_2m":"°C"}
MAX_BYTES=6_000_000


class ERA5OriginalSourceHold(ValueError):
    pass


def _finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def wind_flow_to(wind_from_degrees):
    """Meteorological FROM direction is 180° opposite the downwind TO heading."""
    if not _finite(wind_from_degrees) or not 0<=wind_from_degrees<=360:
        raise ERA5OriginalSourceHold("Invalid original ERA5 wind-from direction")
    return (wind_from_degrees+180)%360


def wrap_cos_degrees(a,b):
    return math.cos(math.radians(a-b))


def year_request_parameters(latitude_floor,longitude_floor,year):
    if not (-90<=latitude_floor<=89 and -180<=longitude_floor<=179):
        raise ERA5OriginalSourceHold("Invalid source coarse 1-degree grid center")
    if not 1940<=year<=2026:
        raise ERA5OriginalSourceHold("Original observed GPS year outside model availability")
    return {
       "latitude":latitude_floor+.5,"longitude":longitude_floor+.5,
       "start_date":f"{year:04d}-01-01","end_date":f"{year:04d}-12-31",
       "hourly":",".join(FIELDS),"models":"era5","timezone":"UTC",
       "wind_speed_unit":"ms","elevation":"nan","cell_selection":"nearest"
    }


def get_original_hourly_response(params):
    """Unmodified public provider original weather JSON, byte cap, guarded requests."""
    url=API+"?"+urlencode(params)
    last_exc=None
    for attempt in range(2):
        try:
            req=Request(url,headers={
                "User-Agent":"ODSP-original-GPS-ecology-wind-study/0.1",
                "Accept":"application/json"
            })
            with urlopen(req,timeout=100) as response:
                raw=response.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES:
                raise ERA5OriginalSourceHold("Original ERA5 response size exceeds byte cap")
            return raw
        except (HTTPError,URLError,TimeoutError) as e:
            last_exc=e
            if isinstance(e,HTTPError) and e.code in (400,401,403,404):
                break
            if attempt==0:time.sleep(2)
    # Do not expose URL, original exact request grids or animal observations in logs.
    raise ERA5OriginalSourceHold(
        "Source ERA5 API call unavailable: "+type(last_exc).__name__
        + (" HTTP "+str(last_exc.code) if isinstance(last_exc,HTTPError) else "")
    )


def validate_and_parse_weather(raw,expected_year):
    try:
        result=json.loads(raw)
    except (ValueError,UnicodeError) as exc:
        raise ERA5OriginalSourceHold("Original ERA5 JSON invalid") from exc
    units=result.get("hourly_units") or {}
    if any(units.get(k)!=u for k,u in UNITS.items()):
        raise ERA5OriginalSourceHold("Original ERA5 hourly units do not match frozen contract")
    if result.get("utc_offset_seconds")!=0:
        raise ERA5OriginalSourceHold("Expected original ERA5 UTC timestamps")
    hourly=result.get("hourly") or {}
    dates=hourly.get("time") or []
    if not dates or any(len(hourly.get(f,[]))!=len(dates) for f in FIELDS):
        raise ERA5OriginalSourceHold("Original ERA5 hourly vectors lack aligned elements")
    valid={}
    missing=0
    for i,label in enumerate(dates):
        try:
            utc=datetime.fromisoformat(label)
        except (ValueError,TypeError) as e:
            raise ERA5OriginalSourceHold("Original ERA5 time not valid ISO8601") from e
        if utc.tzinfo is not None or utc.year!=expected_year or utc in valid:
            raise ERA5OriginalSourceHold("Original ERA5 UTC-hour identity incorrect")
        if utc.minute!=0 or utc.second!=0 or utc.microsecond!=0:
            raise ERA5OriginalSourceHold("ERA5 record not aligned to UTC hour")
        vals=tuple(hourly[f][i] for f in FIELDS)
        if (not all(_finite(v) for v in vals) or vals[0]<0 or not 0<=vals[1]<=360
                or vals[2]<0 or not -100<=vals[3]<=70):
            valid[utc]=None
            missing+=1
        else:
            valid[utc]=vals
    if len(dates) not in (8760,8784):
        raise ERA5OriginalSourceHold("Original ERA5 year incomplete")
    first=datetime(expected_year,1,1)
    last=datetime(expected_year,12,31,23)
    if first not in valid or last not in valid:
        raise ERA5OriginalSourceHold("Original ERA5 source year hour range incomplete")
    receipt={
        "original_raw_json_sha256":hashlib.sha256(raw).hexdigest(),
        "source_hourly_records":len(valid),
        "climate_missing_or_invalid_hours":missing,
        "original_requested_year_covers_full_calendar":True,
        "source_weather_model":"era5",
        "source_weather_variables":list(FIELDS)
    }
    return valid,receipt
