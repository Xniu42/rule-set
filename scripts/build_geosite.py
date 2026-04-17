#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

import yaml


ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
EXACT_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
SUFFIX_PATTERN = re.compile(r"^\+\.[A-Za-z0-9._-]+$")


class BuildError(RuntimeError):
    """Raised when config or upstream data cannot be converted safely."""


@dataclass(frozen=True)
class UpstreamConfig:
    repo: str
    branch: str
    path: str


@dataclass(frozen=True)
class TargetConfig:
    id: str
    enabled: bool
    sources: tuple[str, ...]
    include: str | None = None
    exclude: str | None = None
    allow_empty: bool = False


def load_yaml_file(path: Path) -> object:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except FileNotFoundError as exc:
        raise BuildError(f"Config file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise BuildError(f"Failed to parse YAML file: {path}") from exc


def load_config(path: Path) -> tuple[UpstreamConfig, list[TargetConfig]]:
    data = load_yaml_file(path)
    if not isinstance(data, dict):
        raise BuildError(f"Config root must be a mapping: {path}")

    upstream_data = data.get("upstream")
    if not isinstance(upstream_data, dict):
        raise BuildError("Config missing mapping: upstream")

    repo = require_non_empty_string(upstream_data, "repo", "upstream")
    branch = require_non_empty_string(upstream_data, "branch", "upstream")
    upstream_path = require_non_empty_string(upstream_data, "path", "upstream")
    upstream = UpstreamConfig(repo=repo, branch=branch, path=upstream_path)

    raw_targets = data.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise BuildError("Config field targets must be a non-empty list")

    targets: list[TargetConfig] = []
    seen_ids: set[str] = set()
    for index, raw_target in enumerate(raw_targets, start=1):
        if not isinstance(raw_target, dict):
            raise BuildError(f"Target #{index} must be a mapping")

        target_id = require_non_empty_string(raw_target, "id", f"target #{index}")
        if not ID_PATTERN.fullmatch(target_id):
            raise BuildError(
                f"Target id must match {ID_PATTERN.pattern}: {target_id}"
            )
        if target_id in seen_ids:
            raise BuildError(f"Duplicate target id: {target_id}")
        seen_ids.add(target_id)

        enabled = raw_target.get("enabled", True)
        if not isinstance(enabled, bool):
            raise BuildError(f"Target enabled must be boolean: {target_id}")

        raw_sources = raw_target.get("sources")
        if not isinstance(raw_sources, list) or not raw_sources:
            raise BuildError(f"Target sources must be a non-empty list: {target_id}")
        sources: list[str] = []
        for source in raw_sources:
            if not isinstance(source, str) or not source.strip():
                raise BuildError(f"Target source must be non-empty string: {target_id}")
            sources.append(source.strip())

        include = optional_string(raw_target, "include")
        exclude = optional_string(raw_target, "exclude")
        allow_empty = raw_target.get("allow_empty", False)
        if not isinstance(allow_empty, bool):
            raise BuildError(f"Target allow_empty must be boolean: {target_id}")

        targets.append(
            TargetConfig(
                id=target_id,
                enabled=enabled,
                sources=tuple(sources),
                include=include,
                exclude=exclude,
                allow_empty=allow_empty,
            )
        )

    return upstream, targets


def require_non_empty_string(data: dict[str, object], key: str, scope: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BuildError(f"Missing non-empty string {scope}.{key}")
    return value.strip()


def optional_string(data: dict[str, object], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise BuildError(f"Optional field must be non-empty string when set: {key}")
    return value.strip()


def build_source_url(upstream: UpstreamConfig, source: str) -> str:
    source_name = quote(f"{source}.yaml", safe="")
    return (
        "https://raw.githubusercontent.com/"
        f"{upstream.repo}/{upstream.branch}/{upstream.path}/{source_name}"
    )


def fetch_remote_yaml(url: str) -> object:
    try:
        with urlopen(url) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise BuildError(f"Failed to download {url}: HTTP {exc.code}") from exc
    except URLError as exc:
        raise BuildError(f"Failed to download {url}: {exc.reason}") from exc

    try:
        return yaml.safe_load(body)
    except yaml.YAMLError as exc:
        raise BuildError(f"Failed to parse upstream YAML: {url}") from exc


def classify_rule_item(item: str, source_name: str) -> tuple[str, str]:
    if SUFFIX_PATTERN.fullmatch(item):
        return "domain_suffix_set", item[2:]
    if EXACT_PATTERN.fullmatch(item):
        return "domain_set", item
    raise BuildError(f"Unsupported rule syntax in {source_name}: {item}")


def parse_payload(data: object, source_name: str) -> tuple[set[str], set[str]]:
    if not isinstance(data, dict):
        raise BuildError(f"Upstream YAML root must be a mapping: {source_name}")
    payload = data.get("payload")
    if not isinstance(payload, list):
        raise BuildError(f"Missing payload list in upstream source: {source_name}")

    domains: set[str] = set()
    suffixes: set[str] = set()
    for raw_item in payload:
        if not isinstance(raw_item, str):
            raise BuildError(f"Rule item must be string in {source_name}: {raw_item!r}")
        field_name, normalized = classify_rule_item(raw_item.strip(), source_name)
        if field_name == "domain_set":
            domains.add(normalized)
        else:
            suffixes.add(normalized)
    return domains, suffixes


def parse_override_file(path: Path) -> tuple[set[str], set[str]]:
    domains: set[str] = set()
    suffixes: set[str] = set()
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                field_name, normalized = classify_rule_item(line, f"{path}:{line_number}")
                if field_name == "domain_set":
                    domains.add(normalized)
                else:
                    suffixes.add(normalized)
    except FileNotFoundError as exc:
        raise BuildError(f"Override file not found: {path}") from exc
    return domains, suffixes


def build_target_rule_sets(
    target: TargetConfig,
    upstream: UpstreamConfig,
    repo_root: Path,
    fetcher: Callable[[str], object],
) -> tuple[list[str], list[str]]:
    domains: set[str] = set()
    suffixes: set[str] = set()

    for source in target.sources:
        url = build_source_url(upstream, source)
        upstream_data = fetcher(url)
        source_domains, source_suffixes = parse_payload(upstream_data, source)
        domains.update(source_domains)
        suffixes.update(source_suffixes)

    if target.include:
        include_domains, include_suffixes = parse_override_file(repo_root / target.include)
        domains.update(include_domains)
        suffixes.update(include_suffixes)

    if target.exclude:
        exclude_domains, exclude_suffixes = parse_override_file(repo_root / target.exclude)
        domains.difference_update(exclude_domains)
        suffixes.difference_update(exclude_suffixes)

    if not domains and not suffixes and not target.allow_empty:
        raise BuildError(f"Target generated empty rule set: {target.id}")

    return sorted(domains), sorted(suffixes)


def render_rule_set(
    target: TargetConfig,
    upstream: UpstreamConfig,
    domains: list[str],
    suffixes: list[str],
) -> str:
    lines = [
        f"# source_repo: {upstream.repo}",
        f"# source_branch: {upstream.branch}",
        f"# source_names: {', '.join(target.sources)}",
    ]

    if domains:
        lines.extend(["", "domain_set:"])
        lines.extend(f"  - {domain}" for domain in domains)

    if suffixes:
        lines.extend(["", "domain_suffix_set:"])
        lines.extend(f"  - {suffix}" for suffix in suffixes)

    return "\n".join(lines) + "\n"


def build_outputs(
    upstream: UpstreamConfig,
    targets: list[TargetConfig],
    repo_root: Path,
    fetcher: Callable[[str], object],
) -> dict[str, str]:
    outputs: dict[str, str] = {}
    enabled_targets = [target for target in targets if target.enabled]
    if not enabled_targets:
        raise BuildError("No enabled targets in config")

    for target in enabled_targets:
        domains, suffixes = build_target_rule_sets(target, upstream, repo_root, fetcher)
        outputs[target.id] = render_rule_set(target, upstream, domains, suffixes)
    return outputs


def write_outputs(output_dir: Path, outputs: dict[str, str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_paths = {output_dir / f"{target_id}.yaml" for target_id in outputs}

    for existing_path in output_dir.glob("*.yaml"):
        if existing_path not in expected_paths:
            existing_path.unlink()

    for target_id, content in outputs.items():
        output_path = output_dir / f"{target_id}.yaml"
        with output_path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert selected MetaCubeX GeoSite sources into Egern rule sets."
    )
    parser.add_argument(
        "--config",
        default="config/geosite.yaml",
        help="Path to geosite config file.",
    )
    parser.add_argument(
        "--output-dir",
        default="Egern/generated",
        help="Directory for generated Egern rule-set files.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    config_path = (repo_root / args.config).resolve()
    output_dir = (repo_root / args.output_dir).resolve()

    try:
        upstream, targets = load_config(config_path)
        outputs = build_outputs(upstream, targets, repo_root, fetch_remote_yaml)
        write_outputs(output_dir, outputs)
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {len(outputs)} rule-set files in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
