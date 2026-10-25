# Original four-ungulate source: ERA5 hydrothermal associations with diel GPS contrasts

**Checked source receipt: 2026-10-19, reviewed 2026-10-22.** The [original Utah GPS/ERA5 source workflow](https://github.com/zuizui0223/odsp/actions/runs/39220101404) completed successfully, and its six previous original source GPS contrasts were **all exactly reproduced**.

## What can already be supported biologically?

The same *original Movebank Utah UDWR source* (DOI [10.5441/001/1.711](https://doi.org/10.5441/001/1.711)) yielded four ungulate cohorts, 2,618 source-qualified animals, and six taxon pairs on 1° geography × year-month calendar support. Nineteen distinct original geographic ERA5 cells were retrieved; **zero weather grids failed**. Each shared cell-month carried the **same modeled ERA5 weather** for the two compared taxa.

* First established observational result: pronghorn was relatively dayward in GPS displacement compared with mule deer and elk, largely due to **higher daytime GPS step speed** (see [spatial-block ecological comparison](spatial_block_day_night_components.csv)).
* New environmental screen: this stronger pronghorn daytime movement was **not strongly associated** with the marginal monthly ERA5 temperature or climatic P−ET0 slope across the six original pronghorn–mule deer geographic blocks; source bootstrap intervals encompass zero (T: **−0.002350 to +0.001367** log1p speed per °C; water: **−0.01115 to +0.02479** per 100 mm).
* In contrast, mule deer minus bighorn's relative night/day speed difference was associated with **warmer** (+0.0027955 per °C, block-bootstrap interval **+0.001575 to +0.004247**) and **lower monthly P−ET0** (−0.028233 per 100 mm, interval **−0.040889 to −0.017472**) across **12** qualified source geographic blocks.
* Wapiti minus mule deer was approximately zero in the common source grid-month comparison, and its individual climate-associated slopes had bootstrap intervals encompassing zero.

These are observations of **GPS minimum straight-line movement rates**, not animal daytime activity duration. Monthly ERA5 temperature and water-balance proxy do **not** measure individual thermal microclimate, plant forage, direct soil moisture or water access. The significant-looking marginal slopes for mule deer versus bighorn are **not yet independent of season**: temperature, P−ET0 and astronomical daylength all change across the calendar.

## All six pairwise source environmental associations

The complete six-pair [source-derived, publicly reusable CSV](era5_marginal_climate_associations.csv) contains all original sample and weather-support counts, source mean monthly T and P−ET0, marginal within-geographic-block slopes for temperature (per °C) and water (per 100 mm) and their geographic block-bootstrap intervals where supported. Missing intervals are **unsupported**, not zero or harmless omissions. The 19 source ERA5 grid series are **not 19 independent ecosystems**, and multiple calendar months within a grid are not independent animals.

This environmental addition is **post-GPS-outcome exploratory**. It establishes an environmental association in one original public field-study source, not evolutionary ecological universality or a temperature/water causal mechanism.

## Remaining important biological contrast

The next ecological test should ask whether the apparent mule deer–bighorn heat/water links remain when **mid-month astronomical daylength** is included in the within-cell comparison. If the links disappear, the generalizable insight is chiefly calendar-linked movement heterogeneity; if they remain, the result motivates better independent vegetation, habitat and predator-disturbance exposure measurements. Neither outcome establishes mechanism without direct resource/physiology evidence.

[Calendar-conditioned original-source contract](../MOVEBANK_UTAH_CALENDAR_CONDITIONED_V0_20261022.json) fixes six original marginal climate values before a separate run. It does not reclassify the earlier original `equal photoperiod rising-vs-falling` study, which qualified **zero Utah individual-years** and stays **UNAVAILABLE**.

## Provenance

- Movebank public original UDWR four-species archive DOI **10.5441/001/1.711**; original provider ZIP checksum MD5 `08200c9dbdf7989fb5a35467213b7e5a` (source metadata CC0).
- First GPS four-species observation: [GitHub Actions 39216810610](https://github.com/zuizui0223/odsp/actions/runs/39216810610).
- All six GPS contrasts and source spatial-block component analysis: [39218494366](https://github.com/zuizui0223/odsp/actions/runs/39218494366).
- First ERA5 source weather association: [39220101404](https://github.com/zuizui0223/odsp/actions/runs/39220101404); six source contrasts replayed, original 19 grids, zero weather source failures.
- Source code: [original matching](../../scripts/movebank_utah_shared_spatial_20261019.py) and [ERA5 join](../../scripts/movebank_utah_era5_climate_20261019.py).
- No animal-specific movement positions, individual IDs or source event timestamps are released.
