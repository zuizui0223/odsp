#!/usr/bin/env python3
"""Synchronized calendar-date CERRA wind labels and matched held-out height models.

The archived regional CERRA weather is SINGLE GRID for all tracking birds,
so randomization must exchange WHOLE climate-date labels within YYYY-MM,
identically for every tagged bird on that same UTC date. Shuffling independent
bird-date labels would create fictitious independent atmospheric samples.

The primitive Gyps source Wstar kernels are unchanged; this module only
adapts source 2019-21 weather labels and synchronized null structure.
"""
from __future__ import annotations
from collections import defaultdict
import numpy as np

from .gyps_thermal_height_kernel import pack_profiles,score as wind_vs_pooled
from .gyps_species_shared_wstar_kernel import build_shared_context,score_shared_vs_bird

STATE={"low":0,"high":1,"middle":-1}


def source_wind_labels(packed,weather_state):
    labels=np.zeros(len(packed["bird_days"]),dtype=np.int64)
    for i,(bird,day) in enumerate(packed["bird_days"]):
        v=weather_state.get(day)
        if v not in STATE:
            raise ValueError("Every GPS session requires a source preheight CERRA label")
        labels[i]=STATE[v]
    return labels


def sync_weather_shuffle(packed,original_labels,rng):
    original_labels=np.asarray(original_labels,dtype=np.int64)
    if len(original_labels)!=len(packed["bird_days"]):
        raise ValueError("Unmatched source native altitude-day vs weather regime array")
    by_date={}
    for (bird,day),label in zip(packed["bird_days"],original_labels):
        if day in by_date and by_date[day]!=label:
            raise ValueError("Site-wide wind state must agree for ALL birds on same UTC day")
        by_date[day]=int(label)
    by_month=defaultdict(list)
    for d in sorted(by_date):
        by_month[d[:7]].append(d)
    shuffled={}
    for month,dates in sorted(by_month.items()):
        vector=np.array([by_date[d] for d in dates],dtype=np.int64)
        if len(vector)>1:
            vector=rng.permutation(vector)
        for d,climate_state in zip(dates,vector):
            shuffled[d]=climate_state
    return np.array([shuffled[d] for bird,d in packed["bird_days"]],dtype=np.int64)


def two_channel_holm(channels):
    if set(channels)!={"GPS","BAROMETRIC"}:
        raise ValueError("Original matched two height channels must be retained")
    p={
        sensor:(row.get("calibration",{}).get("p_upper",1.)
                if row.get("terminal")=="tested_before_two_sensor_Holm" else 1.)
        for sensor,row in channels.items()
    }
    order=sorted(channels,key=lambda sensor:(p[sensor],sensor))
    adjusted=0.
    for i,sensor in enumerate(order):
        adjusted=max(adjusted,min(1.,(2-i)*p[sensor]))
        channels[sensor]["holm_upper_p"]=adjusted
        channels[sensor]["family_inference_p"]=p[sensor]
        if channels[sensor]["terminal"]=="tested_before_two_sensor_Holm":
            row=channels[sensor]
            row["terminal"]=(
                "supported_exploratory_bird_specific_wind_gain"
                if row["calibration"]["observed_minus_null_mean"]>0
                and adjusted<.05
                else "not_supported_exploratory_bird_specific_wind_gain"
            )
    return channels
