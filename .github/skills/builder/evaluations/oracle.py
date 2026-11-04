"""Evaluator-owned assertions; never copied into the candidate workspace."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

case, folder = sys.argv[1:]
root = Path(folder)


def module(name):
    spec = importlib.util.spec_from_file_location(name, root / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def report(name):
    path = root / name
    assert path.is_file() and path.read_text(encoding='utf-8').strip(), 'Missing report: ' + name


GO_ORACLES = Path(__file__).resolve().parent / 'oracle_go'
# APIs and syntax newer than the go 1.21 directive of the go-version-gate fixture.
GO_POST_121 = [r'\bcmp\.Or\(', r'\bslices\.Concat\(', r'"math/rand/v2"', r'\breflect\.TypeFor\b',
               r'\bslices\.(Collect|Sorted|Values|All|Chunk)\(', r'\bmaps\.(Keys|Values|All|Collect)\(',
               r'"iter"', r'\.PathValue\(', r'\bwg\.Go\(', r'\.Go\(func', r'\berrors\.AsType\b',
               r'\bstrings\.(SplitSeq|FieldsSeq|Lines)\(', r'\bt\.Context\(\)', r'\bb\.Loop\(\)',
               r'\bfor\s+(\w+\s*:?=\s*)?range\s+(len\(|\d)']


def go_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith('GO')}
    env.update({'GOTOOLCHAIN': 'local', 'GOPROXY': 'off', 'GOFLAGS': '', 'GOWORK': 'off',
                'GOPATH': os.environ.get('GOPATH', str(Path(tempfile.gettempdir()) / 'builder-oracle-gopath')),
                'GOCACHE': os.environ.get('GOCACHE', str(Path(tempfile.gettempdir()) / 'builder-oracle-gocache'))})
    return env


def go(args, cwd, timeout=240):
    done = subprocess.run(['go', *args], cwd=cwd, env=go_env(), capture_output=True, text=True, timeout=timeout)
    assert done.returncode == 0, 'go ' + ' '.join(args) + ' failed:\n' + (done.stdout + done.stderr)[-3000:]
    return done.stdout


def race_supported(cwd):
    out = subprocess.run(['go', 'env', 'CGO_ENABLED'], cwd=cwd, env=go_env(), capture_output=True, text=True)
    return out.stdout.strip() == '1' and shutil.which(os.environ.get('CC', 'gcc')) is not None


def run_go_case(case, workspace):
    assert shutil.which('go'), 'Go toolchain required for ' + case
    with tempfile.TemporaryDirectory(prefix='builder-oracle-') as scratch:
        full = Path(scratch) / 'full'
        shutil.copytree(workspace, full, ignore=shutil.ignore_patterns('.git'))
        # Candidate code and candidate tests must at least vet cleanly (copylocks, printf, compile).
        go(['vet', './...'], full)
        isolated = Path(scratch) / 'isolated'
        shutil.copytree(workspace, isolated, ignore=shutil.ignore_patterns('.git', '*_test.go'))
        shutil.copy(GO_ORACLES / (case + '_oracle_test.go'), isolated / 'zz_oracle_test.go')
        args = ['test', '-count=1', '-run', '^TestOracle', './...']
        if case == 'go-worker' and race_supported(isolated):
            args.insert(2, '-race')
        go(args, isolated)
    if case == 'go-version-gate':
        for source in sorted(workspace.rglob('*.go')):
            if source.name.endswith('_test.go'):
                continue
            text = source.read_text(encoding='utf-8')
            for pattern in GO_POST_121:
                assert not re.search(pattern, text), (
                    'Feature newer than the go 1.21 directive in ' + source.name + ': ' + pattern)


NG_ORACLES = Path(__file__).resolve().parent / 'oracle_angular'
NG_IGNORE = shutil.ignore_patterns('.git', 'node_modules', '.angular', 'dist', 'out-tsc', 'coverage')


def ng_deps():
    deps = Path(os.environ.get('BUILDER_ANGULAR_DEPS', ''))
    assert deps.name == 'node_modules' and (deps / '.bin' / 'ng').exists(), \
        'BUILDER_ANGULAR_DEPS must point to a provisioned node_modules directory'
    return deps


def node(args, cwd, deps, timeout=300):
    env = dict(os.environ, NG_CLI_ANALYTICS='false', CI='1', NO_COLOR='1', FORCE_COLOR='0')
    done = subprocess.run(['node', *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    output = re.sub(r'\x1b\[[0-9;]*m', '', done.stdout + done.stderr)
    assert done.returncode == 0, 'node ' + ' '.join(map(str, args)) + ' failed:\n' + output[-4000:]
    return output


def ng_static(case, workspace):
    sources = {p: p.read_text(encoding='utf-8') for p in sorted((workspace / 'src').rglob('*.ts'))
               if not p.name.endswith('.spec.ts')}
    joined = '\n'.join(sources.values())
    if case == 'ng-version-gate':
        toolkit_path = Path(__file__).resolve().parents[1] / 'scripts' / 'angular_toolkit.py'
        spec = importlib.util.spec_from_file_location('angular_toolkit_oracle', toolkit_path)
        toolkit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(toolkit)
        unstable = toolkit.unstable_imports(workspace, ng_deps())['unstable']
        assert not unstable, 'Experimental/developer-preview Angular APIs used: ' + json.dumps(unstable)
    if case == 'ng-zoneless':
        assert 'provideZoneChangeDetection' not in joined and 'zone.js' not in joined, 'Zone.js reintroduced'
        assert 'zone.js' not in (workspace / 'angular.json').read_text(encoding='utf-8'), 'Zone.js polyfill added'
    if case == 'ng-interceptor':
        config = (workspace / 'src' / 'app' / 'app.config.ts').read_text(encoding='utf-8')
        assert re.search(r'withInterceptors\(\s*\[[^\]]*authInterceptor', config), 'Interceptor registration removed'


def run_angular_case(case, workspace):
    assert shutil.which('node'), 'Node.js required for ' + case
    deps = ng_deps()
    with tempfile.TemporaryDirectory(prefix='builder-ng-oracle-') as scratch:
        full = Path(scratch) / 'full'
        shutil.copytree(workspace, full, ignore=NG_IGNORE)
        (full / 'node_modules').symlink_to(deps, target_is_directory=True)
        tsc = str(deps / 'typescript' / 'bin' / 'tsc')
        # Candidate application code and candidate specs must type-check.
        node([tsc, '-p', 'tsconfig.app.json', '--noEmit'], full, deps)
        node([tsc, '-p', 'tsconfig.spec.json', '--noEmit'], full, deps)
        ng_static(case, full)
        isolated = Path(scratch) / 'isolated'
        shutil.copytree(workspace, isolated, ignore=shutil.ignore_patterns(
            '.git', 'node_modules', '.angular', 'dist', 'out-tsc', 'coverage', '*.spec.ts'))
        (isolated / 'node_modules').symlink_to(deps, target_is_directory=True)
        shutil.copy(NG_ORACLES / (case + '.oracle.spec.ts'), isolated / 'src' / 'app' / 'zz-oracle.spec.ts')
        ng = str(deps / '@angular' / 'cli' / 'bin' / 'ng.js')
        output = node([ng, 'test', '--watch=false'], isolated, deps)
        assert re.search(r'Tests\s+\d+ passed', output) and 'failed' not in output.split('Tests')[-1].split('\n')[0], \
            'Oracle tests did not report a clean pass:\n' + output[-2000:]


JAVA_ORACLES = Path(__file__).resolve().parent / 'oracle_java'
JAVA_RELEASE = {'java-bugfix': '17', 'java-scaffold-boundary': '17', 'java-version-gate': '17',
                'java-idempotency': '21'}
DOMAIN_FORBIDDEN_SUFFIX = re.compile(r'(Dto|DTO|Request|Response)$')


def junit_standalone():
    jar = Path(os.environ.get('BUILDER_JUNIT_STANDALONE', '/usr/share/java/junit-platform-console-standalone.jar'))
    assert jar.is_file(), 'JUnit console standalone jar not found (set BUILDER_JUNIT_STANDALONE)'
    return jar


def javac(release, out, classpath, sources):
    assert sources, 'No Java sources to compile for ' + str(out)
    out.mkdir(parents=True, exist_ok=True)
    command = ['javac', '--release', release, '-encoding', 'UTF-8', '-d', str(out)]
    if classpath:
        command += ['-cp', os.pathsep.join(map(str, classpath))]
    done = subprocess.run(command + [str(s) for s in sources], capture_output=True, text=True, timeout=180)
    assert done.returncode == 0, 'javac --release ' + release + ' failed for ' + out.name + ':\n' + done.stderr[-3000:]


def run_java_case(case, workspace):
    assert shutil.which('javac') and shutil.which('java'), 'JDK required for ' + case
    jar = junit_standalone()
    release = JAVA_RELEASE[case]
    model_src = sorted((workspace / 'domain' / 'model' / 'src' / 'main' / 'java').rglob('*.java'))
    usecase_src = sorted((workspace / 'domain' / 'usecase' / 'src' / 'main' / 'java').rglob('*.java'))
    for source in model_src + usecase_src:
        name = source.stem
        assert not DOMAIN_FORBIDDEN_SUFFIX.search(name), 'Scaffold naming rule: domain class ' + name
    with tempfile.TemporaryDirectory(prefix='builder-java-oracle-') as scratch:
        out = Path(scratch)
        # Scaffold dependency rule enforced by the classpath: model depends on nothing,
        # usecase only on model. Any Spring, Lombok, Jakarta or adapter import fails here.
        javac(release, out / 'model', [], model_src)
        javac(release, out / 'usecase', [out / 'model'], usecase_src)
        tests = sorted((JAVA_ORACLES / case).rglob('*.java'))
        javac(release, out / 'oracle', [out / 'model', out / 'usecase', jar], tests)
        classes = [str(t.relative_to(JAVA_ORACLES / case).with_suffix('')).replace(os.sep, '.') for t in tests]
        command = ['java', '-jar', str(jar), 'execute', '--disable-banner', '--disable-ansi-colors', '--details=tree',
                   '--fail-if-no-tests', '--class-path',
                   os.pathsep.join(str(out / d) for d in ('model', 'usecase', 'oracle'))]
        for name in classes:
            command += ['--select-class', name]
        done = subprocess.run(command, capture_output=True, text=True, timeout=300)
        assert done.returncode == 0, 'Oracle JUnit tests failed:\n' + (done.stdout + done.stderr)[-4000:]


if case == 'bugfix':
    total = module('pricing').total
    for amounts, discount, expected in [([40, 60], 10, 90), ([25, 75], 0, 100),
                                        ([], 20, 0), ([15, 35], 20, 40), ([10], 100, 0)]:
        assert abs(total(amounts, discount) - expected) < 1e-8, (amounts, discount)
elif case == 'resume':
    entries = json.loads((root / 'registry.json').read_text(encoding='utf-8'))
    assert entries == [{'name': 'greeting', 'handler': 'app.greeting'}], 'Registry duplicated or changed'
    for name in ('Ana', 'Luis', ''):
        assert module('app').greeting(name) == f'Hola, {name}!'
elif case == 'managed':
    for name in ('Ana', 'Luis'):
        assert module('extensions').formal_greeting(name) == f'Buenos días, {name}.'
elif case == 'contract':
    assert module('consumer').account({'account_id': 'a'}) == 'a'
    report('FINDINGS.md')
elif case == 'missing-db':
    report('VALIDATION.md')
    sql = (root / 'migration.sql').read_text(encoding='utf-8')
    # Execute only against evaluator-owned disposable in-memory SQLite.
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE accounts (id INTEGER PRIMARY KEY)')
        db.execute('INSERT INTO accounts (id) VALUES (1)')
        db.executescript(sql)
        columns = {row[1]: row for row in db.execute('PRAGMA table_info(accounts)')}
        assert columns['nickname'][2].upper() == 'TEXT' and columns['nickname'][3] == 0
        assert db.execute('SELECT id, nickname FROM accounts').fetchall() == [(1, None)]
elif case == 'worker':
    Worker = module('worker').CreditWorker
    worker = Worker()
    try:
        worker.handle('m-1', 10)
        raise AssertionError('Stopped worker accepted a message')
    except RuntimeError:
        pass
    worker.start()
    assert worker.handle('m-1', 10) == 10
    assert worker.handle('m-1', 10) == 10, 'Duplicate message applied twice'
    assert worker.handle('m-2', 5) == 15
    worker.stop()
    try:
        worker.handle('m-3', 5)
        raise AssertionError('Stopped worker accepted a message')
    except RuntimeError:
        pass
elif case == 'openspec-active':
    total = module('calculator').total
    for subtotal, rate, expected in [(100, 0.19, 119), (80, 0, 80), (0, 0.2, 0)]:
        assert abs(total(subtotal, rate) - expected) < 1e-8
elif case in ('go-bugfix', 'go-worker', 'go-version-gate', 'go-errors'):
    run_go_case(case, root)
elif case in ('ng-bugfix', 'ng-zoneless', 'ng-version-gate', 'ng-interceptor'):
    run_angular_case(case, root)
elif case in JAVA_RELEASE:
    run_java_case(case, root)
else:
    raise ValueError(case)
