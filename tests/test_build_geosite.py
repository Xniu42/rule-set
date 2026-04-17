from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import build_geosite


class BuildGeoSiteTests(unittest.TestCase):
    def test_build_source_url_encodes_special_source_name(self) -> None:
        upstream = build_geosite.UpstreamConfig(
            repo="MetaCubeX/meta-rules-dat",
            branch="meta",
            path="geo/geosite",
        )

        url = build_geosite.build_source_url(upstream, "category-scholar-!cn")

        self.assertTrue(url.endswith("category-scholar-%21cn.yaml"))

    def test_classify_rule_item_supports_exact_and_suffix(self) -> None:
        self.assertEqual(
            build_geosite.classify_rule_item("openai.com", "source"),
            ("domain_set", "openai.com"),
        )
        self.assertEqual(
            build_geosite.classify_rule_item("+.openai.com", "source"),
            ("domain_suffix_set", "openai.com"),
        )

    def test_classify_rule_item_rejects_unsupported_syntax(self) -> None:
        with self.assertRaises(build_geosite.BuildError):
            build_geosite.classify_rule_item("keyword:openai", "source")

    def test_parse_override_file_ignores_comments_and_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            override_path = Path(tmpdir) / "sample.include.txt"
            override_path.write_text(
                "# comment\n\napi.example.com\n+.example.org\n",
                encoding="utf-8",
            )

            domains, suffixes = build_geosite.parse_override_file(override_path)

        self.assertEqual(domains, {"api.example.com"})
        self.assertEqual(suffixes, {"example.org"})

    def test_build_target_rule_sets_merges_sources_and_overrides(self) -> None:
        upstream = build_geosite.UpstreamConfig(
            repo="MetaCubeX/meta-rules-dat",
            branch="meta",
            path="geo/geosite",
        )
        target = build_geosite.TargetConfig(
            id="openai",
            enabled=True,
            sources=("openai", "anthropic"),
            include="overrides/openai.include.txt",
            exclude="overrides/openai.exclude.txt",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            overrides_dir = repo_root / "overrides"
            overrides_dir.mkdir()
            (overrides_dir / "openai.include.txt").write_text(
                "api.extra.example\n+.extra.example\n",
                encoding="utf-8",
            )
            (overrides_dir / "openai.exclude.txt").write_text(
                "drop.example\n+.drop.example\n",
                encoding="utf-8",
            )

            upstream_docs = {
                build_geosite.build_source_url(upstream, "openai"): {
                    "payload": [
                        "api.example.com",
                        "+.openai.com",
                        "drop.example",
                    ]
                },
                build_geosite.build_source_url(upstream, "anthropic"): {
                    "payload": [
                        "claude.ai",
                        "+.drop.example",
                    ]
                },
            }

            domains, suffixes = build_geosite.build_target_rule_sets(
                target,
                upstream,
                repo_root,
                lambda url: upstream_docs[url],
            )

        self.assertEqual(domains, ["api.example.com", "api.extra.example", "claude.ai"])
        self.assertEqual(suffixes, ["extra.example", "openai.com"])

    def test_load_config_validates_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "geosite.yaml"
            config_path.write_text(
                """
upstream:
  repo: MetaCubeX/meta-rules-dat
  branch: meta
  path: geo/geosite
targets:
  - id: openai
    enabled: true
    sources: [openai]
  - id: openai
    enabled: true
    sources: [anthropic]
""".strip()
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(build_geosite.BuildError):
                build_geosite.load_config(config_path)

    def test_render_rule_set_is_stable_without_generated_timestamp(self) -> None:
        upstream = build_geosite.UpstreamConfig(
            repo="MetaCubeX/meta-rules-dat",
            branch="meta",
            path="geo/geosite",
        )
        target = build_geosite.TargetConfig(
            id="openai",
            enabled=True,
            sources=("openai",),
        )

        rendered = build_geosite.render_rule_set(
            target,
            upstream,
            domains=["api.example.com"],
            suffixes=["openai.com"],
        )

        self.assertIn("# source_repo: MetaCubeX/meta-rules-dat", rendered)
        self.assertNotIn("generated_at", rendered)

    def test_write_outputs_removes_stale_yaml_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            stale_path = output_dir / "stale.yaml"
            keep_path = output_dir / "keep.txt"
            stale_path.write_text("old\n", encoding="utf-8")
            keep_path.write_text("keep\n", encoding="utf-8")

            build_geosite.write_outputs(
                output_dir,
                {
                    "openai": "# source_repo: test\n\ndomain_set:\n  - openai.com\n",
                },
            )

            self.assertFalse(stale_path.exists())
            self.assertTrue(keep_path.exists())
            self.assertTrue((output_dir / "openai.yaml").exists())


if __name__ == "__main__":
    unittest.main()
