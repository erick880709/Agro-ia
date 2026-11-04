import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'angular_toolkit.py'
spec = importlib.util.spec_from_file_location('angular_toolkit', SCRIPT)
toolkit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(toolkit)

ANGULAR_JSON = '''{
  // comments are allowed by the CLI
  "version": 1,
  "projects": {
    "portal": {
      "projectType": "application", "root": "", "sourceRoot": "src", "prefix": "bc",
      "schematics": {"@schematics/angular:component": {"changeDetection": "OnPush", "type": "component"}},
      "architect": {
        "build": {"builder": "@angular/build:application"},
        "test": {"builder": "@angular/build:unit-test", "options": {"runner": "karma"}},
        "lint": {"builder": "@angular-eslint/builder:lint"}
      }
    }
  }
}'''

CORE_DTS = '''/**
 * Stable thing.
 * @publicApi 20.0
 */
declare function linkedSignal<D>(c: () => D): D;
/**
 * @experimental 19.0
 */
declare function resource<T>(o: unknown): T;
/**
 * @developerPreview 20.0
 */
declare function pendingUntilEvent<T>(): T;
/**
 * @publicApi 19.0
 */
interface InputFunction {}
declare const input: InputFunction;
'''
FORMS_SIGNALS_DTS = '''/**
 * @experimental 21.0.0
 */
declare function form<T>(model: T): T;
'''


class Workspace:
    def __init__(self, root):
        self.root = Path(root)
        (self.root / 'src' / 'app').mkdir(parents=True)
        (self.root / 'angular.json').write_text(ANGULAR_JSON)
        (self.root / 'package.json').write_text(json.dumps({
            'scripts': {'test': 'ng test'},
            'dependencies': {'@angular/core': '^21.2.0', '@ngrx/signals': '^21.0.0', 'zone.js': '~0.15.0'},
            'devDependencies': {'karma': '~6.4.0', 'typescript': '~5.9.2'}}))
        (self.root / 'AGENTS.md').write_text('Use Promises, not RxJS.\n')
        (self.root / 'src' / 'app' / 'CLAUDE.md').write_text('Always external templates.\n')
        (self.root / 'src' / 'app' / 'legacy.ts').write_text(
            "@NgModule({})\nexport class LegacyModule {}\n@Input() x;\n")
        (self.root / 'src' / 'app' / 'legacy.html').write_text('<li *ngFor="let i of items">{{ i }}</li>\n')
        (self.root / 'src' / 'app' / 'modern.ts').write_text(
            "import { input } from '@angular/core';\nimport { form } from '@angular/forms/signals';\n"
            "readonly a = input<string>();\nconst f = form;\n")

    def install(self, version='21.2.25'):
        core = self.root / 'node_modules' / '@angular' / 'core'
        (core / 'types').mkdir(parents=True)
        (core / 'package.json').write_text(json.dumps({'version': version}))
        (core / 'types' / 'core.d.ts').write_text(CORE_DTS)
        forms = self.root / 'node_modules' / '@angular' / 'forms' / 'types'
        forms.mkdir(parents=True)
        (forms / 'signals.d.ts').write_text(FORMS_SIGNALS_DTS)
        (self.root / 'node_modules' / '.bin').mkdir()


class DiscoverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ws = Workspace(self.temp.name)

    def test_declared_version_when_not_installed(self):
        result = toolkit.discover(self.ws.root / 'src' / 'app')
        self.assertTrue(result['angular_workspace'])
        self.assertEqual(result['angular_version'], [21, 2])
        self.assertEqual(result['version_source'], 'package.json range')
        self.assertFalse(result['dependencies_installed'])
        project = result['projects']['portal']
        self.assertEqual(project['test_runner'], 'karma')
        self.assertEqual(project['targets']['lint'], '@angular-eslint/builder:lint')
        self.assertEqual(project['schematics_defaults']['@schematics/angular:component']['changeDetection'], 'OnPush')
        self.assertIn('AGENTS.md', result['agent_instruction_files'])
        self.assertIn('src/app/CLAUDE.md', result['agent_instruction_files'])
        self.assertEqual(set(result['libraries']) >= {'ngrx-signals', 'zone.js', 'karma'}, True)
        usage = result['usage']
        self.assertEqual((usage['ng_modules'], usage['decorator_inputs'], usage['structural_directives']), (1, 1, 1))
        self.assertEqual((usage['signal_inputs'], usage['signal_forms']), (1, 1))

    def test_installed_version_wins(self):
        self.ws.install('21.2.25')
        result = toolkit.discover(self.ws.root)
        self.assertEqual((result['angular_installed'], result['version_source']), ('21.2.25', 'node_modules'))

    def test_non_workspace(self):
        with tempfile.TemporaryDirectory() as other:
            self.assertFalse(toolkit.discover(other)['angular_workspace'])
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(toolkit.main(['discover', other]), 1)
                self.assertEqual(toolkit.main(['discover', os.path.join(other, 'missing')]), 2)


class ApiStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ws = Workspace(self.temp.name)
        self.ws.install()

    def test_reads_installed_tags(self):
        status = toolkit.api_status(self.ws.root / 'node_modules',
                                    ['linkedSignal', 'resource', 'pendingUntilEvent', 'input', 'nothing'])
        self.assertEqual(status['linkedSignal']['status'], 'stable')
        self.assertEqual(status['linkedSignal']['declarations'][0]['tags'], {'publicApi': '20.0'})
        self.assertEqual(status['resource']['status'], 'experimental')
        self.assertEqual(status['pendingUntilEvent']['status'], 'developer-preview')
        self.assertEqual(status['input']['status'], 'stable')  # resolved through InputFunction
        self.assertEqual(status['nothing']['status'], 'unknown')
        with self.assertRaises(toolkit.InputError):
            toolkit.api_status(self.ws.root / 'node_modules', ['bad name'])

    def test_unstable_imports(self):
        result = toolkit.unstable_imports(self.ws.root)
        self.assertEqual([(f['symbol'], f['status']) for f in result['unstable']], [('form', 'experimental')])
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(toolkit.main(['unstable', str(self.ws.root)]), 1)


class FakeRunner:
    def __init__(self, responses=()):
        self.responses = list(responses)
        self.commands = []

    def __call__(self, command, cwd, timeout, env=None):
        self.commands.append(command)
        for needle, response in self.responses:
            if needle in ' '.join(command):
                return response
        return 0, ''


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ws = Workspace(self.temp.name)

    def test_without_dependencies_nothing_is_installed(self):
        runner = FakeRunner()
        result = toolkit.validate(self.ws.root, runner=runner)
        self.assertEqual({c['result'] for c in result['checks']}, {'not_run'})
        self.assertEqual(runner.commands, [])
        self.assertFalse(result['passed'])

    def test_ladder_uses_local_binaries_and_runner_flags(self):
        self.ws.install()
        (self.ws.root / 'tsconfig.app.json').write_text('{}')
        (self.ws.root / 'tsconfig.spec.json').write_text('{}')
        runner = FakeRunner([('ng test', (1, '\x1b[31mFAIL\x1b[0m src/app/x.spec.ts\n')),
                             ('node --version', (0, 'v22.22.2\n'))])
        result = toolkit.validate(self.ws.root, include='src/app/x.spec.ts', build=True, runner=runner)
        by_check = {c['check']: c for c in result['checks']}
        self.assertEqual(by_check['typecheck-app']['result'], 'passed')
        self.assertEqual(by_check['lint']['result'], 'passed')
        self.assertEqual(by_check['test']['result'], 'failed')
        self.assertNotIn('\x1b', by_check['test']['output_tail'])
        test_cmd = by_check['test']['command']
        self.assertIn('--watch=false', test_cmd)
        self.assertIn('--browsers=ChromeHeadless', test_cmd)  # karma runner
        self.assertIn('--include src/app/x.spec.ts', test_cmd)
        self.assertIn('--output-path', by_check['build']['command'])
        for command in runner.commands:
            self.assertNotIn('npm', command[0])
            self.assertNotIn('npx', command[0])
        self.assertFalse(result['passed'])

    def test_rejects_option_injection(self):
        for include in ('--watch', 'a b'):
            with self.subTest(include=include), self.assertRaises(toolkit.InputError):
                toolkit.validate(self.ws.root, include=include, runner=FakeRunner())


if __name__ == '__main__':
    unittest.main()
