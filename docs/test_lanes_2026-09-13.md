# ODSP pytest lanes

ODSP now separates tests by repository role so the default development signal is dominated by scientific code rather than later governance infrastructure.

## Lanes

- `core` — scientific methods, mathematical validation and empirical endpoint tests. This is the default GitHub Actions matrix on Python 3.10–3.13.
- `governance` — provenance, trust, robustness and forecast-governance layers. These remain tested, but in a separate Python 3.12 workflow that is triggered only when relevant governance paths change or by manual dispatch.
- `submission` — manuscript, rendering, anonymous review, handoff and submission-package checks. These remain covered by their dedicated artifact workflows rather than the default unit-test matrix.

Every collected test is assigned exactly one marker by `tests/conftest.py` using the path policy in `test_lane_policy.py`.

## Commands

```bash
python -m pytest -m core
python -m pytest -m governance
python -m pytest -m submission
python -m pytest                 # explicit full suite when desired
```

## Policy

The lane split changes test scheduling only. It does not delete tests, relax scientific assertions, change frozen endpoint results or claim that governance code is invalid. New ordinary scientific tests default to `core`; infrastructure tests move out of the core lane only when their filename explicitly matches the governance or submission policy.

The double-anonymous MEE review distribution remains independently whitelist-audited and is not defined by these pytest markers.
