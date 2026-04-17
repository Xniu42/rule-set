# GeoSite Sync Architecture

## Overview

This document describes how the repository converts selected GeoSite data from `MetaCubeX/meta-rules-dat` into Egern-compatible rule-set files.

This document describes repository behavior only. It does not replace the upstream project documentation or upstream license terms.

## Public Repository Position

- This repository is an unofficial compatibility project for Egern usage.
- It is not affiliated with or endorsed by MetaCubeX or Egern.
- Generated files are derived from selected upstream open-source data and then transformed into Egern-compatible syntax.
- Generated files should not be described as official MetaCubeX or Egern releases.
- Repository licensing and upstream attribution notes are documented in [`LICENSE`](../LICENSE) and [`NOTICE.md`](../NOTICE.md).

The repository is intentionally narrow in scope:

- GeoSite only
- selected targets only
- Egern domain rule sets only
- automated sync through GitHub Actions

## Scope

### Included

- selected GeoSite sources from the MetaCubeX `meta` branch
- conversion into Egern `domain_set` and `domain_suffix_set`
- optional local include/exclude patches
- scheduled and manual sync

### Excluded

- GeoIP conversion
- full GeoSite mirroring
- direct editing of generated files
- modification of hand-maintained files under `Egern/`

## Upstream Source

- repository: `MetaCubeX/meta-rules-dat`
- branch: `meta`
- directory: `geo/geosite`
- file path pattern: `geo/geosite/<source>.yaml`

Upstream attribution and reuse notes are recorded in [`NOTICE.md`](../NOTICE.md).

## Why Only Two Egern Domain Fields Are Generated

Egern supports five domain rule-set fields:

- `domain_set`
- `domain_suffix_set`
- `domain_keyword_set`
- `domain_regex_set`
- `domain_wildcard_set`

The current upstream GeoSite YAML payloads used by this repository contain only:

- exact domains such as `openaiapi-site.azureedge.net`
- suffix domains prefixed with `+.` such as `+.openai.com`

That data maps directly to:

- exact domains -> `domain_set`
- `+.` suffix domains -> `domain_suffix_set`

If upstream introduces unsupported syntax in the future, the build fails instead of guessing a conversion.

## Repository Layout

```text
rule-set/
├── Egern/
│   ├── claude.yaml
│   ├── custom.yaml
│   └── generated/
├── config/
│   └── geosite.yaml
├── overrides/
├── scripts/
│   └── build_geosite.py
├── tests/
│   └── test_build_geosite.py
├── docs/
│   └── geosite-sync-architecture.md
└── .github/
    └── workflows/
        └── sync-geosite.yml
```

## Directory Responsibilities

- `Egern/claude.yaml`: hand-maintained
- `Egern/custom.yaml`: hand-maintained
- `Egern/generated/`: generated outputs only
- `config/geosite.yaml`: source selection and output identity
- `overrides/`: optional local patches
- `scripts/build_geosite.py`: conversion entry point
- `tests/`: unit tests for conversion and cleanup behavior

## Configuration Model

Each target in `config/geosite.yaml` declares:

- `id`: stable local identifier and output filename stem
- `enabled`: whether the target is built
- `sources`: one or more upstream GeoSite names
- `include`: optional local additions
- `exclude`: optional local removals

The local `id` is intentionally separated from upstream source names so that upstream names containing characters such as `!` or `@` do not leak into filenames.

Example:

```yaml
targets:
  - id: scholar-non-cn
    enabled: true
    sources:
      - category-scholar-!cn
```

This generates:

- `Egern/generated/scholar-non-cn.yaml`

## Override Format

Override files accept one rule item per line:

- `example.com`
- `+.example.com`

Blank lines and `#` comments are ignored. Other syntaxes are rejected.

## Conversion Rules

Input:

```yaml
payload:
  - openaiapi-site.azureedge.net
  - +.openai.com
```

Output:

```yaml
domain_set:
  - openaiapi-site.azureedge.net

domain_suffix_set:
  - openai.com
```

Behavior:

- deduplicate automatically
- sort entries for stable diffs
- omit empty keys
- remove stale generated `.yaml` files that are no longer produced by current configuration
- fail on unsupported upstream syntax

Because the output format differs from upstream input format, generated files are compatibility artifacts rather than raw mirrors.

## Generated File Contract

Each generated file is written to:

- `Egern/generated/<id>.yaml`

The file header records:

- source repository
- source branch
- source names

Build timestamps are intentionally excluded to avoid meaningless diffs.

## Sync Workflow

The workflow lives in:

- `.github/workflows/sync-geosite.yml`

Execution flow:

1. checkout repository
2. set up Python
3. install dependencies
4. run unit tests
5. rebuild all enabled targets
6. detect changes under `Egern/generated/`
7. commit and push only when generated files changed

The workflow supports:

- daily scheduled sync
- manual `workflow_dispatch`

## Validation Strategy

Current tests cover:

- special source name URL encoding
- exact domain and suffix domain classification
- unsupported syntax rejection
- override parsing
- multi-source merge behavior
- config validation
- stable output rendering
- stale generated file cleanup

## Operational Notes

- Raw files under `Egern/generated/` are the only files intended for direct remote use in Egern.
- Hand-maintained files remain outside `Egern/generated/`.
- Removing or disabling a target in `config/geosite.yaml` removes its generated file on the next build.
- When describing this repository publicly, prefer wording such as "derived from selected MetaCubeX GeoSite definitions" instead of wording that implies ownership of upstream data.

## References

- MetaCubeX repository: <https://github.com/MetaCubeX/meta-rules-dat>
- MetaCubeX `meta` GeoSite directory: <https://github.com/MetaCubeX/meta-rules-dat/tree/meta/geo/geosite>
- Egern rules documentation: <https://egernapp.com/docs/configuration/rules/>
