# ODSP 0.11.0 release handoff

This file separates repository-complete release engineering from the two account-level actions that cannot be performed by the source repository itself.

## Repository state required before release

Before publishing `0.11.0`:

1. `package-build` is green.
2. Core tests are green on Python 3.10–3.13.
3. `pyproject.toml`, `CITATION.cff` and `.zenodo.json` all say `0.11.0`.
4. `python -m build` and `python -m twine check dist/*` pass.
5. A clean environment can install the built wheel and run `odsp --help`.

## One-time PyPI trusted-publisher setup

The release workflow uses PyPI Trusted Publishing (OIDC), not a long-lived API token.

For the first release, configure a PyPI **pending trusted publisher** with:

- PyPI project name: `odsp-niche-geometry`
- GitHub owner: `zuizui0223`
- GitHub repository: `odsp`
- workflow filename: `publish-pypi.yml`
- environment name: `pypi`

Also create the GitHub repository environment named `pypi`. No PyPI password or API token should be stored in GitHub secrets.

## Preferred first release: one workflow run

After the one-time publisher setup, open GitHub Actions → `publish-pypi` → **Run workflow**, select `main`, leave the version input as `0.11.0`, and run it.

The workflow then performs, in order:

1. checks that the requested `0.11.0` exactly matches `pyproject.toml`;
2. builds the wheel and source distribution;
3. runs `twine check`;
4. publishes to PyPI by OIDC;
5. only after PyPI succeeds, creates the `v0.11.0` GitHub tag and Release at the exact workflow commit and attaches the distributions.

This path avoids a pre-created tag pointing at a release that never reached PyPI. A traditional pushed `v0.11.0` tag remains supported and is checked against the package version before publication.

## Zenodo

Zenodo's GitHub integration archives GitHub **releases**, not ordinary commits. To mint a DOI from the same release:

1. sign in to Zenodo;
2. enable the `zuizui0223/odsp` repository in the GitHub integration **before** creating the release;
3. run the `publish-pypi` workflow;
4. verify the resulting Zenodo record and DOI;
5. add the DOI to the final accepted manuscript and, if desired, to `CITATION.cff` in a follow-up metadata-only release.

`.zenodo.json` supplies the software metadata for that deposit.

## Double-anonymous review boundary

Methods in Ecology and Evolution permits packages to have been uploaded publicly before submission, but the manuscript/review files must keep links suitably anonymised. The existing anonymous review bundle remains the review surface; this public release workflow does not rewrite it.

If preserving the strongest possible identity separation is preferred, publish to PyPI now but defer enabling Zenodo/GitHub release archiving until acceptance. The journal requires a stable archived version by acceptance, not a public DOI to evaluate the initial anonymised code bundle.

## Alternative tag-driven release

If a tag-driven release is preferred after the account-level publisher setup:

```bash
git checkout main
git pull --ff-only
git tag -a v0.11.0 -m "ODSP 0.11.0"
git push origin v0.11.0
```

Do not reuse a failed release tag for changed code. If the code changes after a public artifact has been published, increment the package version.
