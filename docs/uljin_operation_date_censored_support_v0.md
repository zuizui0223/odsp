# Date-only camera maintenance logs: what can be certified without fabricating hours?

**Source-free pre-data method. Not an EcoBank admission result.**
The earlier original 41 astronomical mirror pairs, exact 3-of-4
camera-hour requirement in EACH of six time bins, and the original
hour-accurate operation algorithm remain unchanged. This distinct
route asks whether SOURCE-INDEPENDENT, COMPLETE but DATE-only
hardware deployment/retrieval/downtime logs can already certify
some calendar-day comparison support without inventing timestamps.

Let a source log declare a device installation date S and retrieval
date E, with UNKNOWN actual hardware timestamp inside each
named calendar day (Asia/Seoul), and let downtime dates follow the
same conservative censoring convention:

- **Possible deployment:** midnight S through midnight after E.
- **Guaranteed deployment:** midnight after S through midnight E.
- **Possible downtime:** midnight from downtime start through midnight
  after downtime end.
- **Guaranteed downtime:** midnight after downtime start through
  midnight of downtime end.

For multiple hardware windows, take UNION first. Then form a
**guaranteed operating subset** = guaranteed deployment EXCEPT
possible downtime, and a **possibly operating superset** = possible
deployment EXCEPT guaranteed downtime. For each original
site×mirror-date pair×6 fixed 4-hour bins compute interval
intersection bounds in HOURS (not camera NIGHTS).

Each original site/day pair has three mutually exclusive states:

- GUARANTEED_ELIGIBLE: all 12 bins (both dates) have >=3
  guaranteed camera hours;
- DEFINITELY_INELIGIBLE: any of 12 bins has <3 hours
  even under the possible upper bound;
- AMBIGUOUS: source dates do not decide, withhold rather than impute.

A missing or unverified downtime roster yields
HOLD_DOWNTIME_COMPLETENESS_UNKNOWN; zero detections from animals never
select which site/day pairs are included. Source-independent original
hardware log provenance remains ANOTHER REQUIRED GATE. Date-only
coverage cannot imply equal detection probability across day/season.

**Synthetic known truths:** a full-date device deployed Apr 1 to
Oct 1 with complete no-downtime records guarantees all 41
interior mirror pairs; an installation beginning May 1 leaves
the May 1 pair ambiguous; a May 1 same-date unknown-hour outage
also leaves one pair ambiguous; an outage spanning Apr 30 to May
2 guarantees one pair ineligible. A single calendar-day
deployment never supplies both matched dates.

This is a useful *partial-identification extension*, not a new
general theorem or a biological result. It does NOT contradict or
retroactively loosen the existing v0 source contract, which requires
EXACT offset-aware UTC+09 hardware operating times to quantify
device-hour offsets for fitted ecological detection rates.
A guaranteed >=3h bin is enough to certify a STRUCTURAL site-day
roster threshold, not enough to generate an **exact exposure offset**
inside a likelihood; such an inference still requires exact hours or
an independently validated interval-censored likelihood.

Only synthetically generated operation windows are accepted by
this v0; animal events, real operation rows, restricted coordinates
and source versions are NEVER accessed. Original source DOI
10.22756/ETC.20260000001022 is a dataset landing identifier, not a
verified direct archive download. Never imply that actual Uljin
camera uptime, species/site support or latent photoperiod memory
was measured. No registered ODSP method or historical empirical
route is modified.
