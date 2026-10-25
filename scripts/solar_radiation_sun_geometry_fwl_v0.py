"""Frisch–Waugh–Lovell solar-altitude/fine-solar-clock sensitivity.

Original GPS sun-relative movement response Y = cos(heading - sun azimuth).
For each original tagged animal and calendar month × 4h apparent-solar-clock
block, demean modeled shortwave X, sin(original sun elevation) Z1 and
continuous apparent solar time Z2, and response Y. Partial out Z1,Z2
WITHOUT ridge or imputation. Hold low-support or singular environmental
contrasts as UNIDENTIFIABLE, never as a biological zero.

No source animal IDs, GPS positions, event timestamps or hourly weather
request geography appears in returned public results.
"""
from __future__ import annotations
from collections import defaultdict
import math
from statistics import mean

RAW_SHORTWAVE_SD_MIN=60.0
GEOMETRY_RESIDUAL_SD_MIN=30.0
GEOMETRY_VARIANCE_RETAIN_FRACTION=.10
GEOMETRY_CORR_DET_MIN=1e-8


def _finite(*values):
    return all(isinstance(v,(float,int)) and math.isfinite(v) for v in values)


def conditional_shortwave_slope_one_animal(records):
    """Return same-samples marginal and solar-geometry-adjusted slopes.

    Every record: original UTC hour, original source solar day, original
    continuous apparent-solar hour, original GPS moving travel bearing,
    original source contemporaneous sun azimuth/elevation and ERA5 shortwave.
    """
    blocks=defaultdict(list)
    for r in records:
        utc,solar_day,solar_hour,travel_az,sun_az,sun_el,shortwave=r
        if not _finite(solar_hour,travel_az,sun_az,sun_el,shortwave):
            continue
        if shortwave<0 or not 0<=sun_el<=90:
            continue
        blocks[(utc.year,utc.month,int(solar_hour//4))].append((
            solar_day,shortwave,
            math.cos(math.radians(travel_az-sun_az)),
            math.sin(math.radians(sun_el)),solar_hour))
    sxx=sxy=syy=z11=z12=z22=xz1=xz2=yz1=yz2=0.0
    nblocks=nsteps=0
    for rows in blocks.values():
        if len(rows)<8 or len({v[0] for v in rows})<3:
            continue
        mx,my,mz1,mz2=(mean(v[i] for v in rows) for i in (1,2,3,4))
        rx=[v[1]-mx for v in rows]
        ry=[v[2]-my for v in rows]
        rz1=[v[3]-mz1 for v in rows]
        rz2=[v[4]-mz2 for v in rows]
        xx=sum(v*v for v in rx)
        if xx/len(rows)<RAW_SHORTWAVE_SD_MIN**2:
            continue
        sxx+=xx
        sxy+=sum(x*y for x,y in zip(rx,ry))
        syy+=sum(v*v for v in ry)
        z11+=sum(v*v for v in rz1)
        z12+=sum(a*b for a,b in zip(rz1,rz2))
        z22+=sum(v*v for v in rz2)
        xz1+=sum(a*b for a,b in zip(rx,rz1))
        xz2+=sum(a*b for a,b in zip(rx,rz2))
        yz1+=sum(a*b for a,b in zip(ry,rz1))
        yz2+=sum(a*b for a,b in zip(ry,rz2))
        nblocks+=1
        nsteps+=len(rows)
    if nblocks<2 or nsteps<20 or sxx<=0:
        return {"status":"INSUFFICIENT_ORIGINAL_BLOCKS","eligible_blocks":nblocks,
                "eligible_steps":nsteps,"unadjusted_same_step_slope":None,
                "solar_geometry_conditional_slope":None}

    marginal=sxy/sxx*100
    if z11<=1e-12 or z22<=1e-12:
        return {"status":"SUN_GEOMETRY_UNIDENTIFIABLE","eligible_blocks":nblocks,
                "eligible_steps":nsteps,"unadjusted_same_step_slope":marginal,
                "solar_geometry_conditional_slope":None}
    std_det=1-(z12*z12/(z11*z22))
    if std_det<=GEOMETRY_CORR_DET_MIN:
        return {"status":"SUN_GEOMETRY_MULTICOLLINEAR","eligible_blocks":nblocks,
                "eligible_steps":nsteps,"unadjusted_same_step_slope":marginal,
                "solar_geometry_conditional_slope":None,
                "geometry_standardized_determinant":max(0,std_det)}
    det=z11*z22-z12*z12
    if det<=0:
        return {"status":"SUN_GEOMETRY_SINGULAR","eligible_blocks":nblocks,
                "eligible_steps":nsteps,"unadjusted_same_step_slope":marginal,
                "solar_geometry_conditional_slope":None}
    def bilinear(a,b,c,d):
        return (z22*a*c-z12*(a*d+b*c)+z11*b*d)/det
    residual_xx=sxx-bilinear(xz1,xz2,xz1,xz2)
    residual_xy=sxy-bilinear(xz1,xz2,yz1,yz2)
    residual_fraction=residual_xx/sxx
    residual_sd=math.sqrt(max(0,residual_xx)/nsteps)
    if (residual_xx<=0 or residual_fraction<GEOMETRY_VARIANCE_RETAIN_FRACTION
            or residual_sd<GEOMETRY_RESIDUAL_SD_MIN):
        return {"status":"INSUFFICIENT_SUN_INDEPENDENT_SHORTWAVE",
                "eligible_blocks":nblocks,"eligible_steps":nsteps,
                "unadjusted_same_step_slope":marginal,
                "solar_geometry_conditional_slope":None,
                "residual_shortwave_SD_Wm2":residual_sd,
                "fraction_shortwave_variance_after_solar_geometry":max(0,residual_fraction)}
    return {
        "status":"GEOMETRY_ADJUSTED_SOURCE_ANIMAL_ESTIMABLE",
        "eligible_blocks":nblocks,"eligible_steps":nsteps,
        "unadjusted_same_step_slope":marginal,
        "solar_geometry_conditional_slope":residual_xy/residual_xx*100,
        "residual_shortwave_SD_Wm2":residual_sd,
        "fraction_shortwave_variance_after_solar_geometry":residual_fraction,
        "geometry_standardized_determinant":std_det,
        "mechanism":"Observational FWL altitude and within-four-hour solar-clock regression, not causal cloud/solar compass attribution."
    }
