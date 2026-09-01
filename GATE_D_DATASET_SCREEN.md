# Chapter 2 Gate D — public dataset screen

Program ID: `niche-to-survey-four-chapter-v1`

Issue: #12

This screen is deliberately based on source architecture, public reproducibility, axis semantics and effort metadata. It is not based on an ODSP niche-thickness result. No Chapter-2 thickness outcome is computed here.

## Admission criteria

A Gate-D dataset must provide, before any ODSP outcome is opened:

1. explicit x-y position plus at least one genuine added ecological axis (`z` or `t`);
2. source-preserving timestamps / axis precision;
3. enough information about logging or sampling effort to state what was and was not observable;
4. cluster identifiers that permit leakage-resistant held-out validation;
5. public, citable data or a stable public archive sufficient for independent reproduction;
6. no need to treat locality elevation, bathymetry, upload time or another contextual field as organism z/t.

## Candidate screen

| Candidate | Added axis | Effort / coverage semantics | Public reproducibility | Gate-D status |
|---|---|---|---|---|
| **Fiordland penguin / tawaki, Milford Sound 2019–2020** | dive depth + biological time | combination GPS/dive loggers; depth recorded every 1 s; GPS attempt schedule declared by year; GPS failure while diving / during short surface intervals is documented | dive data + analysis code public on Zenodo/GitHub; raw tracks public through Movebank study | **ADMIT as first Gate-D dataset** |
| western North Atlantic juvenile grey seals, 2019–2023 | dive depth + time | strong: depth archived at 10 s, per-dive summaries, explicit Fastloc attempt schedule and transmission limitations | article/code public, but telemetry dataset is available only on reasonable request | **FAIL public-reproduction gate for first demonstration** |
| juvenile emperor penguins / Atka Bay | time + x-y | repeated Argos locations with deployment-level sampling | public Movebank Data Repository archive | **RESERVE: good t/x-y candidate, but no primary organism-z variable in the cited tracking design** |
| generic GBIF sampling-event data | time; occasionally other event dimensions | samplingProtocol, sampleSizeValue/unit and samplingEffort can be explicit | public and scalable | **RESERVE: excellent effort framework, but genuine within-cell z is not generally available** |

## Selected dataset

**Tawaki / Fiordland penguin (`Eudyptes pachyrhynchus`), Piopiotahi / Milford Sound, 2019–2020.**

Authoritative references:

- Otis et al. 2025, PeerJ 13:e19650, DOI `10.7717/peerj.19650`.
- Zenodo dataset DOI `10.5281/zenodo.14849008`.
- Movebank study ID `5596513373` for raw/unfiltered tracking data.
- Public analysis/data mirror `Myrene-O/Milford-Sound-Tawaki`, pinned for screening to commit `5e629d6053e6dcaaa44188e71ad6052533ad3cab`.

The public mirror includes `TawakiDiveDatasetComplete.csv` (all processed dive events used by the source analysis) and `OceanBirdsEV.csv`, whose published header demonstrates that dive-event rows can carry `birdID`, `Year`, `Colony`, `TripNumber`, event time, `EvtMaxDepth`, `Lat` and `Lon` together. The raw Movebank track remains the preferred source for reconstructing location linkage rather than treating the derived environmental table as the canonical biological dataset.

## Why this is admissible

The source methods report combination GPS/dive loggers recording depth every 1 s. GPS programming differed prospectively by field year (2019 approximately one fix per minute outside a reduced night schedule; 2020 approximately every 3 minutes / every second dive, again with a reduced overnight schedule). GPS acquisition required about 25–30 s at the surface, so dives with short surface intervals can lack a location fix. This is a real observation-process limitation, not biological absence.

That limitation is why the first ODSP empirical estimand is explicitly restricted to **location-resolved dive-depth state support**. Dives without a defensible x-y location remain in the effort denominator and are not fabricated, interpolated across long gaps, or treated as zero support.

## Important non-blindness disclosure

The source paper is already published and reports biological differences in foraging behaviour, including dive-depth patterns among year/colony groups. Therefore Gate D is **not** presented as a pristine source-paper-blind test of whether tawaki differ in depth use.

What remains prospective is the ODSP estimand and decision machinery: the x-y grain, depth-state bins, cluster split, eligibility gates, weighting, uncertainty and held-out score are frozen before calculating any ODSP niche-thickness or projection-loss result. Dataset selection is justified by measurement architecture and public reproducibility rather than by a precomputed ODSP effect.

## Excluded primary fields

The primary organism-z variable is dive maximum depth (`EvtMaxDepth` or its source-equivalent), not:

- `DEPTH` / `ELEVATION` environmental raster annotations;
- seafloor bathymetry (`nzbathy2016*`);
- locality elevation;
- sensor deployment height;
- GPS altitude.

Those contextual fields may be used only in separately declared explanatory/sensitivity work.

## Next permitted action

Implement and validate the pre-outcome Tawaki Gate-D contract. Do **not** compute `H(Z|X,Y)`, `axis_thickness_map`, projection-loss, colony/year contrasts or held-out outcome scores until that contract is merged on `main`.
