from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "tei" / "minimal_galen.xml"


class NerWorkflowSmokeTest(unittest.TestCase):
    def test_build_token_index_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "token_index"
            cmd = [
                "python3",
                str(SCRIPTS / "build_token_index.py"),
                "--tei-file",
                str(FIXTURE),
                "--work-slug",
                "galen_smt_min",
                "--out",
                str(out_dir),
            ]
            subprocess.check_call(cmd, cwd=str(REPO_ROOT))
            subprocess.check_call(cmd, cwd=str(REPO_ROOT))

            out_path = out_dir / "galen_smt_min.json"
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["work_slug"], "galen_smt_min")
            self.assertEqual(payload["work_urn"], "urn:cts:greekLit:tlg0000.tlg000.1st1K-grc1")
            self.assertGreater(len(payload["tokens"]), 0)
            self.assertEqual(payload["tokens_norm"][0], payload["tokens_norm"][0].lower())

    def test_make_sample_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            token_index_dir = out_dir / "token_index"
            manifest_path = out_dir / "sample_manifest.json"

            subprocess.check_call(
                [
                    "python3",
                    str(SCRIPTS / "build_token_index.py"),
                    "--tei-file",
                    str(FIXTURE),
                    "--work-slug",
                    "galen_smt_min",
                    "--out",
                    str(token_index_dir),
                ],
                cwd=str(REPO_ROOT),
            )
            subprocess.check_call(
                [
                    "python3",
                    str(SCRIPTS / "make_sample_manifest.py"),
                    "--token-index",
                    str(token_index_dir),
                    "--works",
                    "galen_smt_min",
                    "--out",
                    str(manifest_path),
                    "--n-passages",
                    "2",
                    "--seed",
                    "0",
                ],
                cwd=str(REPO_ROOT),
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["items"]), 2)
            self.assertIn("tokens", manifest["items"][0])


if __name__ == "__main__":
    unittest.main()

