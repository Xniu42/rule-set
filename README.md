# rule-set

[![Sync GeoSite Rule Sets](https://github.com/Xniu42/rule-set/actions/workflows/sync-geosite.yml/badge.svg)](https://github.com/Xniu42/rule-set/actions/workflows/sync-geosite.yml)

English | [简体中文](./README.zh-CN.md)

Unofficial Egern-compatible rule-set files derived from selected GeoSite definitions published by [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat).

## Overview

Egern does not consume MetaCubeX `geosite` YAML files directly. This repository fetches selected GeoSite sources from the MetaCubeX `meta` branch, converts them into Egern rule-set syntax, and stores the generated files under [`Egern/generated/`](./Egern/generated).

This repository is a compatibility project maintained for Egern usage. It is not affiliated with or endorsed by MetaCubeX or Egern.

Current scope:

- GeoSite only
- Selected targets only
- Egern domain rule sets only
- Automatic sync through GitHub Actions

## Why This Repository Exists

MetaCubeX GeoSite data is convenient to reuse in sing-box and Clash/Mihomo through `geosite:xxx`, but Egern requires explicit rule-set files such as `domain_set` and `domain_suffix_set`.

This repository bridges that gap by:

- reusing selected upstream GeoSite definitions instead of manually maintaining large domain lists
- converting only the required targets
- keeping generated files stable and suitable for remote use
- preserving hand-maintained files separately from generated outputs

Generated outputs may differ from upstream source files because:

- Egern requires a different rule-set format
- this repository only selects part of the upstream catalog
- optional local include/exclude patches may be applied

## Repository Layout

- [`Egern/generated/`](./Egern/generated): generated Egern rule-set files
- [`Egern/claude.yaml`](./Egern/claude.yaml): hand-maintained file
- [`Egern/custom.yaml`](./Egern/custom.yaml): hand-maintained file
- [`Egern/iherb.yaml`](./Egern/iherb.yaml): hand-maintained file
- [`config/geosite.yaml`](./config/geosite.yaml): selected upstream GeoSite targets
- [`overrides/`](./overrides): optional local include/exclude patches
- [`scripts/build_geosite.py`](./scripts/build_geosite.py): conversion script
- [`tests/test_build_geosite.py`](./tests/test_build_geosite.py): unit tests
- [`docs/geosite-sync-architecture.md`](./docs/geosite-sync-architecture.md): architecture and maintenance notes
- [`NOTICE.md`](./NOTICE.md): upstream attribution and reuse notes

## Use in Egern

Use the generated raw file URL, not the GitHub `blob` page URL.

Examples:

- Raw GitHub:
  - `https://raw.githubusercontent.com/Xniu42/rule-set/main/Egern/generated/openai.yaml`
- jsDelivr:
  - `https://cdn.jsdelivr.net/gh/Xniu42/rule-set@main/Egern/generated/openai.yaml`

Example file content:

```yaml
domain_set:
  - openaiapi-site.azureedge.net

domain_suffix_set:
  - openai.com
  - chatgpt.com
```

## Sync Workflow

The GitHub Actions workflow is defined in [`sync-geosite.yml`](./.github/workflows/sync-geosite.yml).

It currently:

- runs on `workflow_dispatch`
- runs on a daily schedule
- installs dependencies
- runs unit tests
- rebuilds all enabled targets from [`config/geosite.yaml`](./config/geosite.yaml)
- commits and pushes only when files under `Egern/generated/` actually change

The current schedule is once per day at `03:17 UTC`.

## Local Development

### Requirements

- Python 3
- `PyYAML`

### Run tests

```bash
uv run --with PyYAML python3 -m unittest discover -s tests -p "test_*.py"
```

### Generate rule sets

```bash
uv run --with PyYAML python3 scripts/build_geosite.py
```

## Add or Update Targets

1. Edit [`config/geosite.yaml`](./config/geosite.yaml).
2. Add optional patch files under [`overrides/`](./overrides) when a small local adjustment is needed.
3. Run tests.
4. Run the build script.
5. Commit the updated generated files.

## Attribution

- Primary upstream source: [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat)
- Upstream path used by this repository: `meta/geo/geosite`
- Generated files in this repository are derived from selected upstream open-source data and then converted into Egern-compatible syntax
- Upstream authorship and project history remain with the original upstream projects and contributors

See [`NOTICE.md`](./NOTICE.md) for upstream attribution and reuse notes.

## Disclaimer

This repository is an unofficial compatibility project for Egern usage.

The generated files are provided on an "as is" basis, without warranty of any kind, and without any promise of technical support, compatibility, or continued availability.

This repository is not affiliated with or endorsed by MetaCubeX or Egern.

## Notes

- Only exact domains and `+.` suffix domains from upstream are currently converted.
- If upstream introduces unsupported syntax, the build fails instead of generating ambiguous output.
- Files removed from configuration are automatically removed from `Egern/generated/` on the next build.

## License

This repository is distributed under [GPL-3.0](./LICENSE).

Review [`NOTICE.md`](./NOTICE.md) for upstream attribution and reuse notes.
