"""Observable installation behavior, including refusal without partial overwrite."""

from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from install_builder import PackageError, RECEIPT, collect, install, verify  # noqa: E402


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.target = self.root / "project" / ".agents" / "skills" / "builder"
        self.source.mkdir()
        (self.source / "SKILL.md").write_text("---\nname: builder\ndescription: Test package\n---\n", encoding="utf-8")
        (self.source / "references").mkdir()
        (self.source / "references" / "guide.md").write_text("Guide\n", encoding="utf-8")

    def snapshot(self):
        return {p.relative_to(self.target).as_posix(): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}

    def test_install_is_self_contained_and_idempotent(self):
        self.assertEqual(install(self.source, self.target)["status"], "installed")
        before = self.snapshot()
        timestamp = (self.target / RECEIPT).stat().st_mtime_ns
        self.assertEqual(install(self.source, self.target)["status"], "unchanged")
        self.assertEqual(before, self.snapshot())
        self.assertEqual(timestamp, (self.target / RECEIPT).stat().st_mtime_ns)
        self.assertEqual(verify(self.source, self.target)["status"], "verified")
        self.assertEqual(collect(self.source), collect(self.target))

    def test_update_preserves_unrelated_file(self):
        install(self.source, self.target)
        (self.target / "notes.txt").write_text("local", encoding="utf-8")
        (self.source / "references" / "guide.md").write_text("New guide", encoding="utf-8")
        with self.assertRaises(PackageError):
            install(self.source, self.target)
        self.assertEqual(install(self.source, self.target, update=True)["status"], "updated")
        self.assertEqual((self.target / "notes.txt").read_text(), "local")

    def test_local_edit_prevents_any_update(self):
        install(self.source, self.target)
        (self.target / "references" / "guide.md").write_text("User edit", encoding="utf-8")
        (self.source / "SKILL.md").write_text("Changed source", encoding="utf-8")
        before = self.snapshot()
        with self.assertRaises(PackageError):
            install(self.source, self.target, update=True)
        self.assertEqual(before, self.snapshot())
        with self.assertRaises(PackageError):
            verify(self.source, self.target)

    def test_missing_managed_file_is_not_silently_recreated(self):
        install(self.source, self.target)
        (self.target / "references" / "guide.md").unlink()
        with self.assertRaises(PackageError):
            install(self.source, self.target, update=True)

    def test_existing_nonpackage_directory_is_preserved(self):
        self.target.mkdir(parents=True)
        (self.target / "notes.txt").write_text("keep", encoding="utf-8")
        with self.assertRaises(PackageError):
            install(self.source, self.target)
        self.assertEqual(set(self.snapshot()), {"notes.txt"})

    def test_new_file_collision_aborts_before_other_changes(self):
        install(self.source, self.target)
        (self.target / "references" / "new.md").write_text("local", encoding="utf-8")
        (self.source / "references" / "new.md").write_text("source", encoding="utf-8")
        (self.source / "SKILL.md").write_text("changed", encoding="utf-8")
        before = self.snapshot()
        with self.assertRaises(PackageError):
            install(self.source, self.target, update=True)
        self.assertEqual(before, self.snapshot())

    def test_source_retirement_requires_explicit_migration(self):
        install(self.source, self.target)
        (self.source / "references" / "guide.md").unlink()
        before = self.snapshot()
        with self.assertRaises(PackageError):
            install(self.source, self.target, update=True)
        self.assertEqual(before, self.snapshot())

    def test_traversal_receipt_is_rejected_without_writing(self):
        install(self.source, self.target)
        receipt = json.loads((self.target / RECEIPT).read_text())
        receipt["files"]["references/../../outside"] = "a" * 64
        (self.target / RECEIPT).write_text(json.dumps(receipt), encoding="utf-8")
        before = self.snapshot()
        with self.assertRaises(PackageError):
            install(self.source, self.target, update=True)
        self.assertEqual(before, self.snapshot())

    def test_external_reference_and_missing_reference_rejected(self):
        for link in ("../outside.md", "references/missing.md"):
            with self.subTest(link=link):
                (self.source / "SKILL.md").write_text(f"[Guide]({link})", encoding="utf-8")
                with self.assertRaises(PackageError):
                    install(self.source, self.target)
                self.assertFalse(self.target.exists())

    def test_overlap_rejected(self):
        for target in (self.source, self.source / "child", self.root):
            with self.subTest(target=target), self.assertRaises(PackageError):
                install(self.source, target)

    def test_symlink_rejected(self):
        link = self.root / "linked"
        try:
            link.symlink_to(self.source, target_is_directory=True)
        except OSError:
            self.skipTest("OS does not grant symlink creation")
        with self.assertRaises(PackageError):
            install(self.source, link / "target")

    def test_cache_files_not_distributed(self):
        cache = self.source / "scripts" / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "x.pyc").write_bytes(b"cache")
        (self.source / "scripts" / "run.py").write_text("print('hi')", encoding="utf-8")
        install(self.source, self.target)
        self.assertFalse((self.target / "scripts" / "__pycache__").exists())
        self.assertTrue((self.target / "scripts" / "run.py").is_file())


if __name__ == "__main__":
    unittest.main()
