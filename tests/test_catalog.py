from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml
from raes import parse_sdl_file
from raes_env_packs.kits import KitSource, build_kit_catalog, load_kit_release

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_all_releases_are_closed_and_deterministic(self):
        source = KitSource(id="reference", revision="test-revision", root=str(ROOT))
        first = build_kit_catalog((source,))
        second = build_kit_catalog((source,))
        self.assertEqual(first, second)
        self.assertEqual(len(first["entries"]), 38)

    def test_every_release_composes_with_two_parameter_sets(self):
        for manifest in sorted(ROOT.glob("kits/*/1.0.0/kit.yaml")):
            release = load_kit_release(manifest.parent)
            cases = yaml.safe_load((manifest.parent / "tests/composition.yaml").read_text())
            for name in ("default", "variation"):
                with self.subTest(kit=release.id, case=name), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    shutil.copy2(manifest.parent / "module.sdl.yaml", root / "module.sdl.yaml")
                    document = {"name": "composition", "imports": [{"source": "local:module.sdl.yaml", "namespace": "subject", "version": "1.0.0", "parameters": cases[name]}]}
                    (root / "scenario.sdl.yaml").write_text(yaml.safe_dump(document, sort_keys=False))
                    parse_sdl_file(root / "scenario.sdl.yaml")

    def test_representative_multi_kit_environment_composes(self):
        selected = [
            "infrastructure.windows-active-directory-domain-controller",
            "infrastructure.browser-workstation",
            "infrastructure.authoritative-dns-service",
            "infrastructure.application-api-service",
            "infrastructure.postgresql-database",
            "infrastructure.wazuh-security-monitoring-stack",
            "infrastructure.telemetry-collector",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            imports = []
            for index, kit_id in enumerate(selected):
                source = ROOT / "kits" / kit_id / "1.0.0" / "module.sdl.yaml"
                target = root / f"module-{index}.sdl.yaml"
                shutil.copy2(source, target)
                imports.append({"source": f"local:{target.name}", "namespace": f"kit{index}", "version": "1.0.0", "parameters": {"deployment_profile": "compact", "service_label": f"service-{index}"}})
            (root / "scenario.sdl.yaml").write_text(yaml.safe_dump({"name": "realistic-environment", "imports": imports}, sort_keys=False))
            scenario = parse_sdl_file(root / "scenario.sdl.yaml")
            self.assertGreaterEqual(len(scenario.nodes), 9)


if __name__ == "__main__":
    unittest.main()
