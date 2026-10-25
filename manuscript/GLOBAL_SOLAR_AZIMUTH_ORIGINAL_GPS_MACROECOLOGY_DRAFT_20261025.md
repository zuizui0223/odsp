# Solar-relative movement geometry across mammalian tracking populations: a registry-first original-GPS analysis

*Independent ODSP macroecology manuscript, preliminary draft (2026-10-25). This is primary analysis of original public GPS fixes, not a meta-analysis of published effect sizes.*

## Abstract — exploratory source-backed version

Animal movements can be described relative to the geographic bearing of the Sun, but observed relationships can arise from fixed travel corridors and diel schedules without animal orientation to solar cues. We initiated a registry-first original-observation analysis from a fixed snapshot of **437** public Movebank Data Repository packages, including **259** GPS/GNSS sensor-labelled packages. In the first staged original-source analysis, all **nine** pre-existing source archives were authenticated against original provider MD5 values and **13** study×taxon cohorts spanning **nine literal mammal taxa** were evaluated with identical GPS step geometry and source-specific timestamp selection rules. The original archives yielded **10,898,358 GPS rows** and **1,087,873 source-qualified daylight moving intervals**. Solar-relative movement direction was summarized both as a raw circular mean cosine and as a clock-restricted marginal-compass-adjusted covariance. The raw movement-sun alignment was not uniform: among mule deer, for instance, Utah and Wyoming source populations had oppositely signed raw means (**+0.02339**, **−0.04876**, respectively), with descriptive original-animal bootstrap intervals on opposite sides of zero. At fixed within-individual monthly two-hour solar-clock resolution, both corresponding circular covariances were close to zero with intervals spanning zero. African elephant cohorts in Etosha and Kruger similarly did not share a strong raw directional signature, but their underlying geography, sample size and observation timing differ. These results establish feasibility of a portable original-GPS/solar-bearing comparative database and reveal sample-specific observational heterogeneity. They do **not** identify animal solar compass use, ecological causation, biome-general effect sizes, or a global phylogenetic rule. Next, the complete registry frame is being used for source-original bitstream screening and geographically replicated ecological-covariate analysis.

## Introduction — central ecological problem

The astronomical solar bearing is a moving directional reference that all diurnally observed tracked animals encounter, but species cannot be assumed to travel toward or away from the Sun. Apparent relative orientation may emerge from movement corridors, landscape aspect, daily commuting, GPS schedule or seasonal movement history. A useful macroecological test requires original georeferenced animal displacements and sun positions, not published study-specific "diurnality" percentages or fitted models from other publications.

Three targets are distinct:

- **Observed temporal-directional organization:** what fraction of GPS movement bearings follow sun-relative versus absolute compass orientation?
- **Context dependence:** how does the magnitude and sign of that association vary across independent geography, ecological season and movement guilds?
- **Ecological modulation:** can measured wind, terrain aspect, temperature/water history, habitat openness and phenology explain population differences better than a universal solar-direction preference?

The first source-verified analysis directly addresses observational variability; environmental modulation and independence of source field populations remain pending.

## Methods — original observation frame

Use archived public registry snapshot 2026-10-19, all 437 package UUIDs and original source metadata. GPS or GNSS is recorded on 259 archive package metadata entries, with 161 literal scientific-name labels. Do not equate packages, source animal counts, image records or names with unique species or independent ecological regions. A later independent 259-package file metadata preflight must retain source holds and original filenames. The original nine pilot archives were previously used for different movement/night-day outcomes and are therefore explicitly **post-prior-outcome exploratory** for the new solar-bearing response.

Each original GPS track was parsed after source provider MD5 verification; date/time/lat/lon validation preceded within-track sorting. For each observed adjacent interval, derive initial WGS84 great-circle bearing B, approximate NOAA solar azimuth A at the original interval's UTC midpoint position, and solar elevation h at original endpoints/midpoint. The principal daytime movement sample uses 0.5–2h observed step intervals, step length >=100 m, speed <=60 km/h, solar h >=10° at both endpoints and midpoint, and no solar-date crossing. Within all four Southern sources, source observations were first reduced to at most one timestamp-closest-to-UTC-hour-start GPS fix per individual; Northern source observation schedules use earlier source-specific fixed selection rules. This is a **comparability limitation**, not a hidden uniform common field protocol.

Primary raw directional outcome is mean cos(B−A). Axial endpoint mean cos[2(B−A)] is preserved. Independent-compass-marginal excess removes expected alignment from separate observed B and A marginal distributions. The further clock-restricted estimand uses within-individual-year / source-month / two-hour apparent-solar-time blocks with >=8 steps spanning >=3 solar dates and >=5° solar-bearing arc. Eligible animal-year has >=30 directional steps across >=5 solar dates. Block, year and animal weights are equal under each corresponding group statistic. Sampling support is always published alongside estimates. Report source-animal 1000-draw bootstrap percentiles as descriptive; use no source-independent p-values or familywise significance claims.

## Results — 9 original archives, 13 source×taxon groups

The first stage contains all 13 preselected taxa-source combinations, including null and opposite-sign outcomes. Full machine-readable original-source derived table: [13-cohort matrix](../research/GLOBAL_SOLAR_AZIMUTH_V0_13_COHORT_PRIMARY_DATA_MATRIX_20261025.csv); cohort source MD5 and per-group intervals: [Northern group receipt](../research/GLOBAL_SOLAR_AZIMUTH_V0_FIRST_ORIGINAL_GPS_RESULT_20261025.json) and [Southern group receipt](../research/GLOBAL_SOLAR_AZIMUTH_V0_FIRST_SOUTHERN_ORIGINAL_GPS_RESULT_20261025.json).

- Total original GPS rows: **10,898,358**.
- Original daylight directional step intervals meeting source-prespecified criteria: **1,087,873**.
- Sum of eligible animals over source×taxon groups: **2,935**, not established as globally unique individuals.
- Literal taxon names: **9**; original provider-MD5 verified archives: **9**; actual independently sampled biome units: **NOT established**.
- Raw alignment group signs: **6 positive, 7 negative**; 7 of 13 source-animal descriptive bootstrap intervals exclude zero.
- Clock-restricted covariance: 3 of 13 source-animal descriptive bootstrap intervals exclude zero (Florida pig, Utah wapiti and Etosha jackal); no multiple-testing, region-independent or causal significance is claimed.

Mule deer original GPS source data: Utah mean raw +0.023393 (animal 95% bootstrap +0.016264 to +0.030673; n=1652) versus Wyoming −0.048758 (−0.068825 to −0.031284; n=110). Clock-restricted covariance Utah +0.000305 (−0.000071 to +0.000623, n=1509) and Wyoming −0.000743 (−0.002772 to +0.001236, n=106). Thus direct raw movement-sun geometry is not field-population invariant. Conditional covariances are DIFFERENT estimands with much weaker variation in sun angle; they cannot yield an attenuation percentage or prove the Sun has no behavioral role.

Africa: Etosha elephant raw +0.033136, clock +0.000755 (15) versus Kruger elephant raw −0.009027, clock +0.000075 (14); Kruger original-sample bootstrap for raw spans zero. Etosha jackal raw +0.026262 and conditional clock covariance −0.004163 (22) also vary by axis definition, with jackals and elephants belonging to the same wider Etosha ecological landscape rather than independent biome units. Brazil tapir raw −0.001762, clock −0.000512 in 40 original animals. These are observational study-cohort effects; underlying habitat variables and timing are not yet jointly analyzed.

The complete source metadata frame has a measurable study-ID duplication risk: amongst 259 GPS/GNSS packages, 254 distinct source study-ID strings appear, three are repeated across six packages, two packages omit study IDs and four omit scientific names. DOI uniqueness cannot certify source independence. Preserve this audit in the subsequent full-frame systematic analysis.

## Discussion and mechanistic limits

The first positive ecological insight is **non-universality of raw observed solar-relative displacement direction at the population level**, including a same-species source sign reversal. This is not equivalent to animals selecting solar headings; absolute geographical direction, weather, route geometry and timing can produce the observed response. The within-clock result shows limited conditional variation, not proof of absence of solar sensory effects. Species, habitat, collection hardware, year, latitude and movement corridors are not controlled in a globally representative design.

Next ecological analyses require source-resolved, independently sampled regional populations and environmental contrasts: terrain compass orientation, local wind vector relative to the travel direction, temperature/water and vegetation seasonal state, habitat cover and migration status. Local environmental solar exposure may depend jointly on sun *azimuth and elevation*, slope aspect and canopy structure, not azimuth alone. The biologically meaningful independent variable could be **relative incident solar exposure or thermal refuge** rather than simply signed sunward travel. Independent data on study location, climate and source event sampling are necessary before drawing that inference.

Crucially, **a complete original-dataset acquisition and qualification pipeline** and study/population deduplication are prerequisites for treating this as *macroecological* rather than nine handpicked original-study cases. Until original source populations from a systematic geographic/taxon sampling frame qualify, these results remain a comparative pilot, not a universal law.

## Source and ethics

Each public source is individually credited via DOI in the derived cohort matrix and preserves original licensing (including noncommercial original archives). Original location traces, animal identifiers and timestamps were never committed or exported. Prior ODSP terminals and unrelated models are unchanged.
