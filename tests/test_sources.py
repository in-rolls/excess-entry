"""The pinned source must be verified even when it is already cached."""

import hashlib
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "sources", Path(__file__).resolve().parents[1] / "src/sources.py"
)
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name).resolve()
        self.payload = b"candidate_name,votes\nA,20\nB,30\n"
        self.spec = {
            "provider": "local_elections_test",
            "ref": "a" * 40,
            "path": "data/raw/candidates.csv",
            "sha256": hashlib.sha256(self.payload).hexdigest(),
        }
        self.target = (
            self.cache / self.spec["provider"] / self.spec["ref"] / self.spec["path"]
        )
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(self.payload)
        self.settings = patch.dict(sources.SOURCES, {"fixture": self.spec})
        self.settings.start()
        self.addCleanup(self.settings.stop)

    def test_valid_cache_is_reused_without_network(self):
        with patch.dict(os.environ, {"INDIA_DATA_HOME": str(self.cache)}):
            with patch(
                "requests.sessions.Session.request",
                side_effect=AssertionError("network"),
            ):
                self.assertEqual(sources.source_path("fixture"), self.target)

    def test_corrupt_cache_triggers_a_download_instead_of_being_used(self):
        self.target.write_bytes(b"changed")
        with patch.dict(os.environ, {"INDIA_DATA_HOME": str(self.cache)}):
            with patch(
                "requests.sessions.Session.request",
                side_effect=RuntimeError("download required"),
            ):
                with self.assertRaisesRegex(RuntimeError, "download required"):
                    sources.source_path("fixture")

    def test_explicit_file_must_match_the_pin(self):
        self.assertEqual(sources.source_path("fixture", self.target), self.target)
        self.target.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Source checksum mismatch"):
            sources.source_path("fixture", self.target)

    def test_missing_cache_requests_commit_url_and_checksum(self):
        self.target.unlink()
        with patch.dict(os.environ, {"INDIA_DATA_HOME": str(self.cache)}):
            with patch.object(
                sources.pooch, "retrieve", return_value=str(self.target)
            ) as retrieve:
                sources.source_path("fixture")
        retrieve.assert_called_once_with(
            url="https://raw.githubusercontent.com/in-rolls/local_elections_test/"
            + "a" * 40
            + "/data/raw/candidates.csv",
            known_hash="sha256:" + self.spec["sha256"],
            path=self.target.parent,
            fname=self.target.name,
        )

    def test_declared_sources_use_immutable_commits_and_sha256(self):
        for spec in sources.SOURCES.values():
            self.assertRegex(spec["ref"], r"^[0-9a-f]{40}$")
            self.assertRegex(spec["sha256"], r"^[0-9a-f]{64}$")
            self.assertFalse(Path(spec["path"]).is_absolute())
            self.assertNotIn("..", Path(spec["path"]).parts)


if __name__ == "__main__":
    unittest.main()
