# Oppel red-kite source schema: first-line-only pre-outcome screen

## Existing evidence and next narrowly frozen action

ODSP main already verifies the official Zenodo source record
\`10.5281/zenodo.13736049\`: exact six published file names, MD5
manifest strings, sizes, CC BY 4.0 license, and original first-run
GitHub Actions ZIP/JSON hashes. No biological response was examined
during that inventory.

The source describes **a different biological prediction target**
from the original BOP four-bin altitude-state random forest.
Oppel et al. reported 258 Swiss training birds (697 individual-seasons)
and 63 German birds (99 eligible individual-seasons) in their already
published reproductive-state analysis. Neither those historical paper
counts nor a six-file *metadata inventory* establishes compatible
tracking/year-state columns or authenticated independent individuals.

This step first commits
\`research/BOP_RED_KITE_HEADER_ONLY_V1_CONTRACT.json\`
**before inspecting file headers**, and then restricts access to the
**first physical CSV header line** of exactly four pinned files:

- \`GER_indseasondata.csv\` (provider MD5
  \`bdf5445971195ca8cc27760d242b1563\`)
- \`SUI_indseasondata.csv\` (provider MD5
  \`91394907a2d036e3dbacf5cd4f70475b\`)
- \`GER_trackingdata.csv\` (provider MD5
  \`ec5dd057fc6d704a09f15bbbffe00129\`)
- \`SUI_trackingdata.csv\` (provider MD5
  \`f654300e9a77b8dc41221f44d468ea2c\`)

The reader asks the fixed Zenodo record for only HTTP
\`Range: bytes=0-4095\` and consumes only as many bytes as needed
to reach the first newline (limit 4,096 per file), then closes the
connection. A provider may ignore HTTP Range and return 200 OK;
the script still **parses no rows or values after the header** and
does not retrieve entire file bodies intentionally. This screen
does **not** compute downloaded-file MD5 values; provider checksums
remain inventory metadata.

The header can disclose *column names* such as \`year_id\`,
\`nest\` and \`success\`, but not the contents of those columns.
The results include the exact names, first-line SHA256, observed
first-line length, whether each source has a candidate year linkage,
and which prospective animal-ID or nesting-state column aliases
exist. This is schema discovery, **not** observing the distribution
of success, breeding events, animal movement or altitude.

## Scientific decision rules

- Four complete acceptable headers: \`SOURCE_HEADERS_RECORDED_NO_FULL_DATA_ACCESS\`;
  this means **header fields observed only**.
- Missing a year linkage or candidate individual key:
  \`HOLD_MISSING_YEAR_OR_ANIMAL_IDENTIFIER_SCHEMA\`.
- Provider access, redirect or malformed-header failure:
  \`HEADER_ACCESS_OR_SCHEMA_HOLD\`, preserved as first result.
- **Regardless of header compatibility**, the scientific terminal
  remains \`HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER\`.

The next valid route would need its own pre-outcome fixed binary
nest-state model, training-only comparator, same-animal cross-year
identity mapping, German calibration/test group split, target study
population, and independent data-source provenance. The originally
published German nest-model evaluation is already known to the
literature; ODSP must not call it previously undiscovered biology.
The historical BOP RF is not run and the BOP
\`empirical_state_prediction_mixed\` remains untouched.

## Executable scope

\`scripts/bop_red_kite_header_only_preflight_v1.py\`
and
\`tests/test_bop_red_kite_header_only_preflight_v1.py\`
are purely a restrictive schema-access preflight. The latter tests
source URL tampering, duplicate headers, multiline rows, incomplete
prefixes, missing biological individual ID aliases, missing
season-link keys, no values read and permanent no-outcome status.

\`\`\`bash
python -m pytest tests/test_bop_red_kite_header_only_preflight_v1.py
python scripts/bop_red_kite_header_only_preflight_v1.py --out /tmp/red-kite-header-only.json
\`\`\`

No individual history values, nest attempts, breeding successes,
raw GPS data, model outputs or old BOP results are opened or changed
as part of this *header-only* route.
