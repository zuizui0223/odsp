# Equal sunlight, changing thermal gradient and GPS movement within elephants

**ODSP original-source exploratory ecology — 2026-10-19.** This is an explicitly new within-elephant matched-photoperiod question, **not** a novel claim that elephant speed and temperature are generally associated.

## Ecological question

Does the annual seasonal change in the daytime-minus-nighttime relative thermal environment of an African elephant correspond to its simultaneous change in relative nighttime-versus-daytime GPS displacement, even when **astronomical daylength is nearly identical** in the two seasons?

This builds on the previous [two geographically independent elephant telemetry source results](solar_calendar_multispecies_ecological_results_20261019.md): Etosha `Loxodonta africana` hourly-source night-relative contrast **−0.15013** (14 animals, 14/14 negative) and Kruger **−0.02889** (13 animals, 11/13 negative). It seeks ecological explanation of the seasonal temporal response, not prediction score improvement or sensor calibration as a standalone paper.

## Source originality, credit, and measurement limits

Original archived tracking source: [Slotow, Thaker & Vanak 2019, Movebank Data Repository 10.5441/001/1.403h24q5](https://doi.org/10.5441/001/1.403h24q5) (provider-declared CC0), with 283,688 original GPS fixes including `external-temperature` in degrees Celsius from 14 tagged female elephants (one each from different herds). Original Kruger CSV, 43,776,326 bytes, provider MD5 `970ea06b9de69f1cc0d9f733d7f7e463` was matched before biological analysis. The source README explicitly defines external temperature as **tag-measured temperature, different from actual ambient and internal animal body temperatures**.

[Thaker et al. (2019)](https://doi.org/10.3389/fevo.2019.00004) already showed that collar temperature tracks relative ambient thermal variation and relates to movement, water shuttling, habitat and season. The sensor itself is heated by circuits and the elephant, so we report **relative collar thermal conditions**, never body temperature or an uncalibrated absolute microclimate. Their overall temperature–movement association is **prior literature**, not our discovery.

## Our distinct research contrast

The [source/estimator contract](../research/MOVEBANK_KRUGER_THERMAL_DIEL_V0_20261019.json) was fixed before reading the original numerical temperature field for this outcome, although the prior GPS movement results and the 2019 source publication were already known. Source checksum and previous exact elephant hourly GPS effect **−0.0288936554833** were replayed first. The independent [workflow 39211773115 passed all six known-truth tests](https://github.com/zuizui0223/odsp/actions/runs/39211773115).

For each elephant and Southern summer-solstice cycle, the preserved GPS sampling architecture chooses one fix per UTC clock hour **using timestamp only**, then uses observed 30–120-minute great-circle step displacement in same solar day/night zones. The rising/falling matched dates must have ≤5-minute modeled photoperiod difference, be separated ≥30 calendar days, have ≥3 valid GPS segments per daypart per date, satisfy 0.5–2 step-count-ratio balance, and include ≥10 pairs per individual-cycle. The collar-temperature reading at the **starting fix** is summarized as a daypart median; each daypart requires ≥2 valid sensor temperatures.

Define the new within-individual paired-day quantities:

- `ΔGPS = (log1p v_night - log1p v_day)_falling - (log1p v_night - log1p v_day)_rising`, where `v` is median observed GPS step displacement speed in km/h.
- `ΔTgradient = (Tcollar_day - Tcollar_night)_falling - (Tcollar_day - Tcollar_night)_rising`, in °C.
- Within each elephant × solar-year, estimate the **centered linear association** of `ΔGPS` with `ΔTgradient`; only years with ≥10 temperature-complete dates and standard deviation of ΔTgradient ≥0.1 °C are estimable. Give animal years equal weight within elephant, then elephants equal weight; derive a 2000-replicate individual-cluster percentile interval.

This does not identify the causal effect of thermal conditions, and it avoids inflating the nominal number of independent animals with repeatedly observed date pairs.

## Source-backed ecological results

All **283,688** original source temperature values were numeric and fell inside the prespecified broad −40 to 90°C sensor QA range. **1,787/1,787** previously GPS-matched daylength date pairs had complete four-zone temperature medians; **13 elephants** and 21 animal × solar-year records remained qualified. The exact prior GPS result was reproduced.

| Source-level paired contrast (falling minus rising) | Elephant-equal mean |
| --- | ---: |
| Daytime collar temperature | **+1.0615°C** |
| Nighttime collar temperature | **+1.5326°C** |
| DAY-minus-NIGHT collar temperature gradient | **−0.4711°C** |
| Daytime log1p median GPS speed | **+0.05238** |
| Nighttime log1p median GPS speed | **+0.02349** |
| Relative NIGHT-minus-DAY GPS movement | **−0.02889** |

The relative daytime GPS displacement grows more than nighttime displacement, although both increase in this source during the declining-daylength side. Collar temperature likewise rises on both dayparts but increases more at night.

**Within-individual seasonal thermal-gradient association:**

| Statistic | Observed |
| --- | ---: |
| Equal-elephant mean within-year slope (relative log1p km/h per °C) | **+0.0011718** |
| 95% individual-bootstrap percentile interval | **−0.0020413 to +0.0041542** |
| Positive / negative individual slopes | **8 / 5** |
| Independent source elephants | **13** |

**Important interpretation:** The data show a repeatable within-source annual redistribution of GPS displacement toward the daylight period at near-equal photoperiod. However, variation in the **relative day/night thermal gradient** had **no clearly resolved linear association** with variation in that relative displacement among the individuals (interval crosses zero, mixed slope signs). This does **not** demonstrate that temperature is unimportant; a nonlinear response, direct temperature level, accessible water, woody cover, wet/dry resource stage, sampling context and sensor heating remain alternative explanations.

An ordinary temperature–GPS speed relationship, independently established by the original authors, and our matched-photoperiod thermal-gradient difference-of-differences are **different estimands**; one cannot be invoked as if it proves the other. The collar temperature association is exploratory, not an independent replication across another temperature-tagged elephant landscape.

## Ecological-paper consequence

We now have a positive **intraspecific cross-population ecological pattern** (two different original wild elephant study areas share a negative night-relative GPS seasonal contrast at roughly equal daylength), plus a direct Kruger sensor test that **does not independently identify a simple linear day/night thermal-gradient mechanism**. This combination motivates a broader hypothesis: elephant seasonal movement scheduling may depend on the calendar of water accessibility, habitat structure and thermoregulatory opportunities—not light duration or relative heat alone. This explanation is **to be tested**, not claimed as a discovered water mechanism.

Immediate ecological research priority: join seasonal **water/vegetation availability and habitat exposure** to matched elephant/other mammal location-days, preserving within-animal sampling and study-population dependence, then compare differences across independent populations and guilds. Do not promote stronger claims from the 1,787 within-animal pairs as though they were 1,787 independent animals.

## Provenance

- Main Movebank [437-package registry and original bundle inventory](../research/seasonal_database_catalog/README.md).
- Kruger independent source [original MD5-verified movement result](https://github.com/zuizui0223/odsp/actions/runs/39210827847).
- Sensor pairing and ecological slope [source and six-test verified CI](https://github.com/zuizui0223/odsp/actions/runs/39211773115).
- The new source and slope definitions remain in [protocol](../research/MOVEBANK_KRUGER_THERMAL_DIEL_V0_20261019.json), [script](../scripts/movebank_kruger_thermal_solar_20261019.py) and [known-truth tests](../tests/test_movebank_kruger_thermal_solar_20261019.py). No private tracking location, animal ID, precise timestamp or raw source event is re-exported.
