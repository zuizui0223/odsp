# Independent vignette: Palmer Penguins

This example is deliberately outside the four empirical systems used in the ODSP manuscript. It asks a small transfer question: **can penguin morphology predict island state across collection years, beyond a lower-information training marginal?** The purpose is method portability, not a new biological claim.

The source is the `palmerpenguins` simplified data (344 penguins, three species, three islands), pinned to upstream commit `8957207b78d6ccd1b4654a9dd9c9041b657478ab`. The upstream package is CC0 1.0. `prepare_penguins.py` keeps complete morphology + sex rows and creates a synthetic unique `row_id`; it does not alter states or measurements.

The contract declares island as the state, four morphology measurements as predictors, individual rows as independent scoring units, sex as a descriptive stratum, and year as the held-out fold. The pooled training marginal is the prospective comparator; sex-stratified marginals are retained only for the additive baseline decomposition. Equal sex / equal individual training weighting is explicit.

```bash
python examples/penguins/prepare_penguins.py
odsp run --contract examples/penguins/endpoint.json \
  --out examples/penguins/receipt.json
```

The receipt records the exact contract and prepared-data SHA256 values, every independent-row gain, the pooled→sex→model decomposition, and the terminal sign category. No manuscript endpoint, frozen receipt, or terminal class is read or modified by this vignette.

Source: Allison Horst, Alison Hill & Kristen Gorman, `palmerpenguins`; original observations from Palmer Station LTER / Gorman et al. The example is an operational demonstration, not evidence that morphology causally determines island occupancy.
