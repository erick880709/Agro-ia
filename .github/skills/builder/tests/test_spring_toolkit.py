import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'spring_toolkit.py'
spec = importlib.util.spec_from_file_location('spring_toolkit', SCRIPT)
toolkit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(toolkit)
FIXTURES = SCRIPT.parents[1] / 'evaluations' / 'fixtures'


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


class DiscoverTests(unittest.TestCase):
    def test_scaffold_fixture_from_a_submodule(self):
        result = toolkit.discover(FIXTURES / 'java-scaffold-boundary' / 'domain' / 'usecase')
        self.assertTrue(result['java_project'])
        self.assertEqual(Path(result['root']).name, 'java-scaffold-boundary')
        self.assertEqual((result['build_tool'], result['java_release'], result['spring_boot']), ('gradle', 17, '3.5.6'))
        self.assertTrue(result['bancolombia_scaffold'])
        self.assertEqual(result['stack'], 'imperative')
        self.assertEqual(result['scaffold_properties']['lombok'], 'false')
        self.assertNotIn('lombok', result['libraries'])
        self.assertIn('data-jpa', result['libraries'])
        self.assertIn('usecase', result['modules'])
        self.assertEqual(result['usage']['transactional'], 1)

    def test_maven_reactive_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root / 'pom.xml', '''<project><parent><groupId>org.springframework.boot</groupId>
<artifactId>spring-boot-starter-parent</artifactId><version>4.0.1</version></parent>
<properties><java.version>25</java.version></properties><modules><module>api</module></modules>
<dependencies><dependency><artifactId>spring-boot-starter-webflux</artifactId></dependency>
<dependency><artifactId>lombok</artifactId></dependency><dependency><artifactId>reactor-test</artifactId></dependency></dependencies></project>''')
            write(root / 'api' / 'pom.xml', '<project><artifactId>api</artifactId></project>')
            write(root / 'api' / 'src' / 'main' / 'java' / 'A.java',
                  'class A { @Autowired private Repo repo; Mono<String> f() { return Mono.just("x"); } void g() { f().block(); } }')
            write(root / 'api' / 'src' / 'test' / 'java' / 'ATest.java', 'class ATest { @MockBean Repo r; void t() { m().block(); } }')
            write(root / 'CLAUDE.md', 'conventions')
            result = toolkit.discover(root / 'api' / 'src')
            self.assertEqual(Path(result['root']), root.resolve())
            self.assertEqual((result['build_tool'], result['java_release'], result['spring_boot']), ('maven', 25, '4.0.1'))
            self.assertEqual(result['stack'], 'reactive')
            self.assertTrue({'webflux', 'lombok', 'reactor-test'} <= set(result['libraries']))
            usage = result['usage']
            self.assertEqual((usage['field_injection'], usage['block_calls_main'], usage['mock_bean']), (1, 1, 1))
            self.assertIn('CLAUDE.md', result['agent_instruction_files'])

    def test_non_project(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertFalse(toolkit.discover(temp)['java_project'])
            with redirect_stdout(io.StringIO()):
                self.assertEqual(toolkit.main(['discover', temp]), 1)
                self.assertEqual(toolkit.main(['discover', temp + '/missing']), 2)


class ClassStatusTests(unittest.TestCase):
    def test_reads_jar_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            jar = Path(temp) / 'spring-boot-webmvc-test-4.0.1.jar'
            with zipfile.ZipFile(jar, 'w') as archive:
                archive.writestr('org/springframework/boot/webmvc/test/autoconfigure/WebMvcTest.class', b'not-a-class')
            result = toolkit.class_status(
                ['org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest',
                 'org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest'],
                jars=[temp], javap=lambda name: None)
            classes = result['classes']
            self.assertTrue(classes['org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest']['exists'])
            self.assertFalse(classes['org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest']['exists'])
            with self.assertRaises(toolkit.InputError):
                toolkit.class_status(['not a class'], jars=[temp])

    @unittest.skipUnless(shutil.which('javac') and shutil.which('javap'), 'JDK required')
    def test_detects_deprecation_with_javap(self):
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp) / 'src' / 'demo'
            write(src / 'Old.java', 'package demo;\n@Deprecated\npublic class Old {}\n')
            write(src / 'New.java', 'package demo;\npublic class New {}\n')
            out = Path(temp) / 'out'
            subprocess.run(['javac', '-d', str(out), str(src / 'Old.java'), str(src / 'New.java')], check=True)
            jar = Path(temp) / 'demo-1.0.jar'
            with zipfile.ZipFile(jar, 'w') as archive:
                for cls in out.rglob('*.class'):
                    archive.write(cls, cls.relative_to(out).as_posix())
            classes = toolkit.class_status(['demo.Old', 'demo.New'], jars=[str(jar)])['classes']
            self.assertTrue(classes['demo.Old']['deprecated'])
            self.assertFalse(classes['demo.New']['deprecated'])


class FakeRunner:
    def __init__(self, responses=()):
        self.responses = list(responses)
        self.commands = []

    def __call__(self, command, cwd, timeout):
        self.commands.append(command)
        for needle, response in self.responses:
            if needle in ' '.join(command):
                return response
        return 0, ''


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'p'
        shutil.copytree(FIXTURES / 'java-scaffold-boundary', self.root)

    def test_without_wrapper_nothing_runs(self):
        runner = FakeRunner()
        result = toolkit.validate(self.root, runner=runner)
        self.assertEqual([c['result'] for c in result['checks']], ['not_run'])
        self.assertEqual([c[0] for c in runner.commands], ['java'])
        self.assertFalse(result['passed'])

    def test_gradle_ladder_with_scaffold_and_filters(self):
        write(self.root / 'gradlew', '#!/bin/sh\n')
        runner = FakeRunner([(':test --tests', (1, 'FAILED BlockCardUseCaseTest\n'))])
        result = toolkit.validate(self.root, module='usecase', tests='*BlockCard*', runner=runner)
        by_check = {c['check']: c for c in result['checks']}
        self.assertEqual(by_check['compile']['result'], 'passed')
        self.assertIn(':usecase:compileJava', by_check['compile']['command'])
        self.assertEqual(by_check['test']['result'], 'failed')
        self.assertIn('--tests *BlockCard*', by_check['test']['command'])
        self.assertIn('scaffold-validate-structure', by_check)
        self.assertFalse(result['passed'])

    def test_network_failure_is_not_a_code_failure(self):
        write(self.root / 'gradlew', '#!/bin/sh\n')
        runner = FakeRunner([('compileJava', (1, 'Could not resolve org.springframework.boot:spring-boot-starter'))])
        result = toolkit.validate(self.root, runner=runner)
        by_check = {c['check']: c['result'] for c in result['checks']}
        self.assertEqual(by_check['compile'], 'not_run')
        self.assertEqual(by_check['test'], 'blocked')

    def test_rejects_injection(self):
        write(self.root / 'gradlew', '#!/bin/sh\n')
        for kwargs in ({'module': 'a b'}, {'tests': '--init-script=evil'}):
            with self.subTest(**kwargs), self.assertRaises(toolkit.InputError):
                toolkit.validate(self.root, runner=FakeRunner(), **kwargs)


if __name__ == '__main__':
    unittest.main()
