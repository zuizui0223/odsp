# Joint robustness radius

`odsp.joint_robustness_radius` quantifies how far an already certified ODSP transfer-sign conclusion survives as the bounded row-reweighting envelope is widened while retaining the declared block-bootstrap uncertainty.

The method starts at `gamma=1`. If the baseline joint audit is already uncertain, mixed or unavailable, no positive radius is reported. Otherwise the baseline joint robust category is treated as the target category and `gamma` is increased.

If the same category survives through the caller-declared search upper bound, the result is `robust_through_search_upper`; the returned certified gamma is a lower bound only. If the category fails inside the search range, ODSP returns a binary-search bracket:

- `certified_gamma`: last passing lower bound;
- `break_gamma`: first failing upper bound;
- `boundary_interval_width`: numerical bracket width.

For example, in the frozen known-truth 75% `+0.2` / 25% `-0.2` mixture the point gain is positive, but the sign ceases to be jointly certified once the reweighting envelope reaches the theoretical break near `sqrt(3)`.

The radius is **not** a probability of correctness, a detection probability, a causal-confounding parameter, or an estimated biological threshold. It is a sensitivity radius relative to the declared block definition, bootstrap design and row-reweighting envelope.
