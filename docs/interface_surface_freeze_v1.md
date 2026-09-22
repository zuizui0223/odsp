# ODSP public interface freeze v1

## Decision

For the v0.11 release line, ODSP stops adding top-level command variants.

The public command surface is:

```text
odsp run
odsp transfer
odsp experimental
```

This is an interface consolidation only. No estimator, certification rule,
bootstrap, frozen empirical endpoint or receipt schema is changed by this policy.

## Stable transfer entrypoint

Ordinary externally scored information-transfer analyses use:

```bash
odsp transfer --contract endpoint.json
```

Advanced existing contract families are selected with one option rather than a
new command:

```bash
odsp transfer --variant refits --contract endpoint.json
odsp transfer --variant external-refits --contract endpoint.json
odsp transfer --variant external-paired --contract endpoint.json
odsp transfer --variant external-paired-lattice --contract endpoint.json
```

The default variant is `scores`.

## Experimental governance entrypoint

Pre-outcome freeze generation and method-registry inspection are grouped under
`experimental` because they are governance/qualification operations rather
than ordinary scoring:

```bash
odsp experimental freeze --variant external --plan plan.json --manifest-out freeze.json
odsp experimental freeze --variant paired --plan plan.json --manifest-out freeze.json
odsp experimental freeze --variant paired-lattice --plan plan.json --manifest-out freeze.json
odsp experimental method-route --request request.json
```

The method router is therefore no longer part of the normal user path.

## Legacy compatibility

Existing scripts and frozen receipts remain reproducible. The previous command
spellings continue to execute but are hidden from the default help surface:

| Legacy spelling | Canonical interface |
| --- | --- |
| `transfer-refits` | `transfer --variant refits` |
| `transfer-refits-external` | `transfer --variant external-refits` |
| `transfer-refits-external-paired` | `transfer --variant external-paired` |
| `transfer-refits-external-paired-lattice` | `transfer --variant external-paired-lattice` |
| `freeze-refits-external` | `experimental freeze --variant external` |
| `freeze-refits-external-paired` | `experimental freeze --variant paired` |
| `freeze-refits-external-paired-lattice` | `experimental freeze --variant paired-lattice` |
| `method-route` | `experimental method-route` |

No historical receipt is rewritten to use the new spelling.

## Feature-freeze rule

Until the current manuscript submission cycle is complete:

- no new inferential variant receives a new top-level CLI command;
- no new bootstrap or interval family is added merely to rescue an endpoint;
- new methodological ideas must first be expressed as an estimand or scientific
  question, not as another command surface;
- compatibility aliases may be maintained, but the documented public surface
  remains `run / transfer / experimental`.

The population-transfer addition follows this rule: it changed the estimand and
was added to the existing `transfer` receipt rather than creating another
subcommand.
