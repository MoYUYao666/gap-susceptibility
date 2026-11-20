"""Regression tests for the public release integrity contract."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

class IntegrityTest(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).with_name("verify_release.py")
        spec = importlib.util.spec_from_file_location("release_verifier", path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        payload = b'{"value": 1}\n'
        (self.root/"record.json").write_bytes(payload)
        self.manifest = {"files": {"record.json": {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}}}
        self.save()
    def save(self):
        (self.root/"MANIFEST.json").write_text(json.dumps(self.manifest), encoding="utf-8")
    def test_valid(self):
        self.assertEqual(self.module.integrity(self.root), 1)
    def test_missing(self):
        (self.root/"record.json").unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            self.module.integrity(self.root)
    def test_tampered(self):
        (self.root/"record.json").write_text('{"value": 2}\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Hash"):
            self.module.integrity(self.root)
    def test_extra(self):
        (self.root/"unexpected.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            self.module.integrity(self.root)
    def test_traversal(self):
        self.manifest["files"]["../outside"] = self.manifest["files"].pop("record.json")
        self.save()
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            self.module.integrity(self.root)
    def test_nonfinite(self):
        payload = b'{"value": NaN}\n'
        (self.root/"record.json").write_bytes(payload)
        self.manifest["files"]["record.json"] = {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
        self.save()
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            self.module.integrity(self.root)
    def test_overflow(self):
        self.replace_payload(b'{"value": 1e309}\n')
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            self.module.integrity(self.root)
    def test_duplicate_keys(self):
        self.replace_payload(b'{"value": 1, "value": 2}\n')
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.module.integrity(self.root)
    def test_duplicate_manifest_keys(self):
        (self.root/"MANIFEST.json").write_bytes(b'{"files": {}, "files": {}}')
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.module.integrity(self.root)
    def replace_payload(self, payload):
        (self.root/"record.json").write_bytes(payload)
        self.manifest["files"]["record.json"] = {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
        self.save()

if __name__ == "__main__":
    unittest.main(verbosity=2)
