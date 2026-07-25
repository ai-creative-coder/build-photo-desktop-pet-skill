#!/usr/bin/env python3
"""Offline tests for the external-provider bridge and release-review gate."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validate_release_review import CHECKS, STATES, validate_review


SCRIPTS = Path(__file__).resolve().parent


class SkillGuardTests(unittest.TestCase):
    def test_external_provider_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            provider = root / "provider.py"
            provider.write_text(
                "from pathlib import Path\n"
                "def generate_image(*, request, api_key, settings):\n"
                "    out = Path(request['output_dir']) / 'result.png'\n"
                "    out.write_bytes(b'png')\n"
                "    return {'outputs': [str(out)], 'model': settings['model']}\n",
                encoding="utf-8",
            )
            config = root / "config.json"
            config.write_text(json.dumps({
                "provider_file": str(provider),
                "api_key_env": "TEST_DESKTOP_PET_IMAGE_KEY",
                "settings": {"model": "offline-test-model"},
            }), encoding="utf-8")
            request = root / "request.json"
            request.write_text(json.dumps({"output_dir": str(root)}), encoding="utf-8")
            environment = os.environ.copy()
            environment["TEST_DESKTOP_PET_IMAGE_KEY"] = "not-a-real-key"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "external_image_provider.py"),
                    "--config",
                    str(config),
                    "--request",
                    str(request),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(result["model"], "offline-test-model")
            self.assertTrue((root / "result.png").is_file())

    def test_release_review_requires_every_state_and_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "src-tauri").mkdir()
            (project / "src").mkdir()
            (project / "output" / "reviews").mkdir(parents=True)
            (project / "src-tauri" / "tauri.conf.json").write_text(
                json.dumps({"version": "9.9.9"}),
                encoding="utf-8",
            )
            (project / "src" / "styles.css").write_text(
                ".integrated-pet-stage { background: transparent; }\n",
                encoding="utf-8",
            )
            review = {
                "ok": True,
                "version": "9.9.9",
                "states_reviewed": sorted(STATES),
                "checks": {name: True for name in CHECKS},
            }
            review_path = project / "output" / "reviews" / "release-quality-decision.json"
            review_path.write_text(json.dumps(review), encoding="utf-8")
            self.assertEqual(validate_review(project), [])
            review["checks"]["no_ghosting"] = False
            review_path.write_text(json.dumps(review), encoding="utf-8")
            self.assertIn(
                "review.checks.no_ghosting must be true",
                validate_review(project),
            )


if __name__ == "__main__":
    unittest.main()
