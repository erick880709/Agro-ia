import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'python_toolkit.py'
spec = importlib.util.spec_from_file_location('python_toolkit', SCRIPT)
toolkit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(toolkit)

PYPROJECT = '''\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "payments"
requires-python = ">=3.11"
dependencies = ["fastapi>=0.115", "pydantic>=2.0"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.6"]

[tool.ruff]
line-length = 120

[tool.mypy]
strict = true

[tool.pytest.ini_options]
addopts = "-q"
'''


class DiscoverTests(unittest.TestCase):
    def test_discover_pyproject(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'pyproject.toml').write_text(PYPROJECT, encoding='utf-8')
            (root / 'src').mkdir()
            (root / 'tests').mkdir()
            (root / 'uv.lock').write_text('', encoding='utf-8')
            d = toolkit.discover(str(root))
            self.assertTrue(d['is_python'])
            self.assertEqual(d['package_manager'], 'uv')
            self.assertEqual(d['requires_python'], '>=3.11')
            self.assertEqual(d['build_backend'], 'hatchling.build')
            self.assertIn('fastapi>=0.115', d['dependencies'])
            self.assertTrue(d['ruff'])
            self.assertTrue(d['mypy'])
            self.assertTrue(d['pytest'])
            self.assertEqual(d['layout'], 'src')
            self.assertIn('tests', d['test_dirs'])

    def test_discover_requirements_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'requirements.txt').write_text('requests==2.32\n', encoding='utf-8')
            d = toolkit.discover(str(root))
            self.assertTrue(d['is_python'])
            self.assertEqual(d['package_manager'], 'pip')
            self.assertIsNone(d['requires_python'])

    def test_discover_not_python(self):
        with tempfile.TemporaryDirectory() as td:
            d = toolkit.discover(str(Path(td)))
            self.assertFalse(d['is_python'])
            self.assertEqual(d['manifests'], [])


if __name__ == '__main__':
    unittest.main()
