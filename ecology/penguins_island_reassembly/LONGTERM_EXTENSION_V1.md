# Long-term island-reassembly extension v1

Status: **pre-outcome design**. Do not inspect long-term colony-count outcomes
before fixing the extraction and scoring rules below.

## Aim

Test whether long-term functional change among Palmer Archipelago penguin
breeding islands is driven mainly by **species replacement** rather than
persistent within-species morphology shifts.

## Data lanes

### Lane A: colony abundance

Use a public annual colony-count source with explicit island, species, year and
count type. Preferred source order:

1. Palmer LTER colony census where a reproducible public series is available;
2. Antarctic Penguin Biogeography Project / MAPPPD standardized breeding-colony
   counts.

Restrict the primary analysis to islands with repeated counts for at least two
of the three Pygoscelis species or a documented colonization/extirpation
transition. Keep Biscoe, Dream and Torgersen as named focal islands when their
time series satisfy this rule.

### Lane B: trait distributions

Use the pinned Palmer Penguins 2007--2009 measurements for species-specific
trait distributions:

- culmen length;
- culmen depth;
- flipper length;
- body mass.

Body mass is analyzed separately from the three structural traits because it is
condition-sensitive.

Do not infer unobserved historical within-species trait change from these
measurements.

### Lane C: environment

Regional annual sea-ice metrics may be joined only after the abundance
extraction is frozen. Island-specific snow, geomorphology or breeding phenology
may be added as a second mechanism layer when the same island-year support is
available.

## Primary quantities

For island i and year t with species s:

- relative abundance: p_sit = N_sit / sum_s N_sit
- community-weighted trait mean:
  CWM_it = sum_s p_sit * trait_mean_s
- effective species diversity: exp(Shannon)
- Bray-Curtis turnover between adjacent sampled years
- replacement contribution to trait change:
  delta_CWM_turnover = sum_s (p_s,i,t+1 - p_sit) * trait_mean_s

With fixed species trait means, total CWM change equals the abundance/species
replacement component by construction. This is intentional for the first
island-biogeographic test: it asks how much the **community phenotype** changes
through who is present and abundant.

## Primary hypotheses

### L1: directional functional reassembly

Within islands that experience a sustained decline of Adélie relative abundance
and increase of gentoo or chinstrap relative abundance, community trait
centroids will move toward the replacing species' trait centroid.

### L2: turnover precedes any within-species explanation

Between-year changes in island community trait centroids will be explainable
from species-abundance turnover without requiring inferred within-species
morphological shifts.

### L3: islands differ in reassembly trajectories

Neighboring islands will not necessarily move in parallel because species
colonization histories and breeding-habitat filters differ among islands.

### L4: regional forcing, local realization

After the turnover analysis is frozen, regional sea-ice variation is expected
to explain shared temporal forcing, while island-specific habitat/phenology
variables can explain deviations among islands. This is a mechanism hypothesis,
not part of the primary turnover test.

## Inclusion rules

- Keep one count unit per analysis (prefer breeding pairs / occupied nests).
- Never mix adults, chicks and nests in the same abundance series.
- If multiple surveys exist for an island-species-year, use the source's
  recommended census or a predeclared deterministic priority rule.
- No interpolation in the primary analysis.
- Require at least five observed years per island for a descriptive trajectory;
  require at least ten observed years spanning at least eight calendar years for
  trend models.
- Colonization/extirpation years are retained as zeros only when survey effort
  establishes true absence; otherwise use missing.

## Models

Primary descriptive model:

CWM_it ~ island + year + island:year

Long-term trend model, only where support permits:

CWM_it ~ smooth(year) + island + smooth(year, by=island)

Species-composition models should be fit directly to counts/proportions; CWM is
a derived ecological summary, not a substitute for the composition model.

## Falsification

The island-reassembly story is weakened if:

- focal islands show little species-composition change through time;
- CWM trajectories are flat despite large composition changes because species
  trait centroids overlap strongly;
- apparent transitions depend on mixing incompatible count types;
- long-term patterns are carried by a single poorly sampled island.

## Scope boundary

This extension concerns island community assembly and functional reassembly.
It does not test evolutionary local adaptation, and it does not convert the
three-year Palmer morphology sample into a historical trait time series.
