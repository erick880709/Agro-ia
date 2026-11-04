"""Go profile helper for Builder: static discovery and a read-only validation ladder.

discover  Reads go.mod/go.work, tooling and CI files without executing Go.
validate  Runs gofmt -l, go vet, go build, go test (optionally -race and
          golangci-lint) on the given packages and returns evidence rows.
          It never rewrites sources, never installs tools and builds binaries
          into a temporary directory.

Exit codes: 0 no failures, 1 failures observed (or nothing could be run,
or no Go module found), 2 invalid input or harness error.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

SKIP_DIRS = {'.git', 'vendor', 'node_modules', 'testdata', '.idea', '.vscode', 'bin', 'dist'}
MAX_SCANNED_FILES = 5000
SIGNALS = {
    'testify': ('github.com/stretchr/testify',),
    'gomock': ('go.uber.org/mock', 'github.com/golang/mock'),
    'mockery': ('github.com/vektra/mockery',),
    'goleak': ('go.uber.org/goleak',),
    'go-cmp': ('github.com/google/go-cmp',),
    'testcontainers': ('github.com/testcontainers/testcontainers-go',),
    'wire': ('github.com/google/wire',),
    'fx': ('go.uber.org/fx',),
    'dig': ('go.uber.org/dig',),
    'samber-do': ('github.com/samber/do',),
    'cobra': ('github.com/spf13/cobra',),
    'viper': ('github.com/spf13/viper',),
    'gin': ('github.com/gin-gonic/gin',),
    'echo': ('github.com/labstack/echo',),
    'chi': ('github.com/go-chi/chi',),
    'fiber': ('github.com/gofiber/fiber',),
    'gorilla-mux': ('github.com/gorilla/mux',),
    'grpc': ('google.golang.org/grpc',),
    'pgx': ('github.com/jackc/pgx',),
    'sqlx': ('github.com/jmoiron/sqlx',),
    'gorm': ('gorm.io/gorm',),
    'zap': ('go.uber.org/zap',),
    'zerolog': ('github.com/rs/zerolog',),
    'logrus': ('github.com/sirupsen/logrus',),
    'errgroup': ('golang.org/x/sync',),
    'bancolombia-reactive-commons': ('github.com/bancolombia/reactive-commons-go',),
    'bancolombia-commons-mq': ('github.com/bancolombia/commons-mq-go',),
    'bancolombia-secrets-manager': ('github.com/bancolombia/secrets-manager-go',),
}
LINT_CONFIGS = ('.golangci.yml', '.golangci.yaml', '.golangci.toml', '.golangci.json')
CI_FILES = ('.gitlab-ci.yml', 'azure-pipelines.yml', 'Jenkinsfile', 'bitbucket-pipelines.yml')
GENERATOR_FILES = ('buf.yaml', 'buf.gen.yaml', 'sqlc.yaml', 'sqlc.yml', 'sqlc.json',
                   '.mockery.yaml', '.mockery.yml', 'gqlgen.yml', 'oapi-codegen.yaml')
LAYER_NAMES = {'domain', 'entity', 'entities', 'usecase', 'usecases', 'port', 'ports',
               'adapter', 'adapters', 'infrastructure', 'repository', 'service', 'handler'}
GENERATED = re.compile(r'^// Code generated .* DO NOT EDIT\.$', re.M)


class InputError(ValueError):
    """Invalid arguments or unreadable project."""


def parse_version(text):
    match = re.fullmatch(r'(?:go)?(\d+)\.(\d+)(?:\.(\d+))?(?:\S*)', text or '')
    if not match:
        return None
    return [int(match.group(1)), int(match.group(2))]


def parse_go_mod(text):
    """Parse the parts of go.mod that matter for Builder without running Go."""
    result = {'module': None, 'go': None, 'toolchain': None,
              'require': [], 'replace': [], 'tool': [], 'retract': 0}
    block = None
    for raw in text.splitlines():
        indirect = '// indirect' in raw
        line = raw.split('//', 1)[0].strip()
        if not line:
            continue
        if block:
            if line == ')':
                block = None
                continue
            entry = line
        else:
            match = re.match(r'(module|go|toolchain|require|replace|tool|retract|exclude|godebug|ignore)\b\s*(.*)', line)
            if not match:
                continue
            keyword, entry = match.groups()
            if entry == '(':
                block = keyword
                continue
            if keyword in ('module', 'go', 'toolchain'):
                result[keyword] = entry.strip().strip('"')
                continue
            block_once = keyword
            entry = entry.strip()
            _store(result, block_once, entry, indirect)
            continue
        _store(result, block, entry, indirect)
    return result


def _store(result, keyword, entry, indirect=False):
    parts = entry.split()
    if keyword == 'require' and parts:
        result['require'].append({'path': parts[0], 'version': parts[1] if len(parts) > 1 else None,
                                  'indirect': indirect})
    elif keyword == 'replace' and '=>' in entry:
        left, right = (side.strip() for side in entry.split('=>', 1))
        result['replace'].append({'from': left, 'to': right})
    elif keyword == 'tool' and parts:
        result['tool'].append(parts[0])
    elif keyword == 'retract':
        result['retract'] += 1


def parse_go_work(text):
    uses, block = [], False
    version = None
    for raw in text.splitlines():
        line = raw.split('//', 1)[0].strip()
        if not line:
            continue
        if block:
            if line == ')':
                block = False
            else:
                uses.append(line.strip('"'))
            continue
        if line.startswith('go '):
            version = line[3:].strip()
        elif line == 'use (':
            block = True
        elif line.startswith('use '):
            uses.append(line[4:].strip().strip('"'))
    return {'go': version, 'use': uses}


def make_targets(text):
    targets = []
    for line in text.splitlines():
        match = re.match(r'^([A-Za-z0-9][A-Za-z0-9_.-]*)\s*:(?!=)', line)
        if match and match.group(1) not in targets and not match.group(1).startswith('.'):
            targets.append(match.group(1))
    return targets


def taskfile_tasks(text):
    tasks, inside = [], False
    for line in text.splitlines():
        if re.match(r'^tasks:\s*$', line):
            inside = True
            continue
        if inside:
            if line and not line.startswith(' '):
                break
            match = re.match(r'^  ([A-Za-z0-9][\w:.-]*):\s*', line)
            if match:
                tasks.append(match.group(1))
    return tasks


def find_module_dir(path):
    path = Path(path).resolve()
    if path.is_file():
        path = path.parent
    for candidate in (path, *path.parents):
        if (candidate / 'go.mod').is_file():
            return candidate
    return None


def scan_sources(root):
    generate, tags, packages, generated = [], set(), set(), 0
    layers = set()
    scanned = 0
    truncated = False
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')
                         and not (Path(current, d) / 'go.mod').exists())
        rel_dir = Path(current).relative_to(root)
        for part in rel_dir.parts:
            if part.lower() in LAYER_NAMES:
                layers.add(part.lower())
        for name in sorted(files):
            if not name.endswith('.go'):
                continue
            scanned += 1
            if scanned > MAX_SCANNED_FILES:
                truncated = True
                break
            packages.add(rel_dir.as_posix() or '.')
            try:
                text = Path(current, name).read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            if GENERATED.search(text):
                generated += 1
            for match in re.finditer(r'^//go:generate\s+(.+)$', text, re.M):
                generate.append({'file': (rel_dir / name).as_posix(), 'command': match.group(1).strip()})
            for match in re.finditer(r'^//go:build\s+(.+)$', text, re.M):
                for tag in re.findall(r'[A-Za-z_][\w.]*', match.group(1)):
                    tags.add(tag)
        if truncated:
            break
    return {'packages': len(packages), 'generated_files': generated, 'go_generate': generate[:50],
            'build_tags': sorted(tags), 'layer_dirs': sorted(layers), 'scan_truncated': truncated}


def discover(path):
    target = Path(path)
    if not target.exists():
        raise InputError('Path does not exist: ' + str(path))
    module_dir = find_module_dir(target)
    if module_dir is None:
        return {'go_module': False, 'path': str(target.resolve()),
                'note': 'No go.mod found in this path or its parents; the Go profile does not apply.'}
    mod = parse_go_mod((module_dir / 'go.mod').read_text(encoding='utf-8'))
    required = {entry['path'] for entry in mod['require']}
    signals = sorted(name for name, prefixes in SIGNALS.items()
                     if any(req == p or req.startswith(p + '/') for req in required for p in prefixes))
    workspace = None
    for candidate in (module_dir, *module_dir.parents):
        if (candidate / 'go.work').is_file():
            workspace = {'path': str(candidate / 'go.work'),
                         **parse_go_work((candidate / 'go.work').read_text(encoding='utf-8'))}
            break
    repo_root = next((c for c in (module_dir, *module_dir.parents) if (c / '.git').exists()), module_dir)
    makefile = next((module_dir / n for n in ('Makefile', 'makefile', 'GNUmakefile')
                     if (module_dir / n).is_file()), None)
    taskfile = next((module_dir / n for n in ('Taskfile.yml', 'Taskfile.yaml')
                     if (module_dir / n).is_file()), None)
    lint_config = next((str(c / n) for c in (module_dir, repo_root) for n in LINT_CONFIGS
                        if (c / n).is_file()), None)
    workflows = sorted(str(p.relative_to(repo_root)) for p in (repo_root / '.github' / 'workflows').glob('*.y*ml')) \
        if (repo_root / '.github' / 'workflows').is_dir() else []
    workflows += [n for n in CI_FILES if (repo_root / n).exists()]
    layout = {name: (module_dir / name).is_dir() for name in ('cmd', 'internal', 'pkg', 'api')}
    return {
        'go_module': True,
        'module_dir': str(module_dir),
        'module': mod['module'],
        'go_directive': mod['go'],
        'language_version': parse_version(mod['go']),
        'toolchain': mod['toolchain'],
        'workspace': workspace,
        'direct_requires': len([r for r in mod['require'] if not r['indirect']]),
        'replace': mod['replace'],
        'tool_directives': mod['tool'],
        'signals': signals,
        'lint_config': lint_config,
        'make_targets': make_targets(makefile.read_text(encoding='utf-8', errors='replace')) if makefile else [],
        'task_targets': taskfile_tasks(taskfile.read_text(encoding='utf-8', errors='replace')) if taskfile else [],
        'magefile': (module_dir / 'magefile.go').is_file(),
        'ci': workflows,
        'generator_configs': [n for n in GENERATOR_FILES if (module_dir / n).exists()],
        'layout': layout,
        **scan_sources(module_dir),
        'note': 'Static discovery only. Inspect the affected code and the reference module before deciding.',
    }


def run(command, cwd, timeout):
    try:
        done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return None, 'Command not found: ' + command[0]
    except subprocess.TimeoutExpired:
        return 124, 'Timed out after %ss' % timeout
    return done.returncode, (done.stdout + done.stderr)


def tail(text, lines=40):
    return '\n'.join(text.strip().splitlines()[-lines:])


def row(check, command, result, summary, output=''):
    return {'check': check, 'command': ' '.join(command) if command else '', 'result': result,
            'summary': summary, 'output_tail': tail(output)}


def validate(path, packages, *, race=False, lint=False, run_pattern=None, tags=None,
             timeout=600, runner=run, which=shutil.which):
    module_dir = find_module_dir(path) if Path(path).exists() else None
    if module_dir is None:
        raise InputError('No go.mod found for: ' + str(path))
    packages = packages or ['./...']
    for pattern in packages:
        if not re.fullmatch(r'[\w./@~+-]+', pattern) or pattern.startswith('-'):
            raise InputError('Unsupported package pattern: ' + pattern)
    if run_pattern is not None and run_pattern.startswith('-'):
        raise InputError('Unsupported -run pattern')
    if tags is not None and not re.fullmatch(r'[\w.,]+', tags):
        raise InputError('Unsupported build tags')
    tag_args = ['-tags=' + tags] if tags else []
    checks = []
    context = {'module_dir': str(module_dir), 'packages': packages, 'tags': tags}
    mod = parse_go_mod((module_dir / 'go.mod').read_text(encoding='utf-8'))
    context['go_directive'] = mod['go']
    if not which('go'):
        for name in ('gofmt', 'vet', 'build', 'test'):
            checks.append(row(name, None, 'not_run', 'Go toolchain not available in PATH'))
        return finish(context, checks)
    code, out = runner(['go', 'version'], module_dir, 60)
    context['go_version'] = out.strip() if code == 0 else None
    code, out = runner(['go', 'env', 'GOOS', 'GOARCH', 'CGO_ENABLED', 'GOTOOLCHAIN', 'GOFLAGS'], module_dir, 60)
    if code == 0:
        values = (out.splitlines() + [''] * 5)[:5]
        context.update(dict(zip(('goos', 'goarch', 'cgo_enabled', 'gotoolchain', 'goflags'), values)))

    list_cmd = ['go', 'list', *tag_args, '-f',
                '{{.Dir}}\t{{join .GoFiles " "}} {{join .TestGoFiles " "}} {{join .XTestGoFiles " "}}',
                *packages]
    code, out = runner(list_cmd, module_dir, timeout)
    if code != 0:
        checks.append(row('list', list_cmd, 'failed', 'go list could not load the packages', out))
        for name in ('gofmt', 'vet', 'build', 'test'):
            checks.append(row(name, None, 'blocked', 'Packages could not be loaded'))
        return finish(context, checks)
    files = []
    for line in out.splitlines():
        if '\t' in line:
            directory, names = line.split('\t', 1)
            files += [str(Path(directory, n)) for n in names.split() if n]
    if files and which('gofmt'):
        fmt_cmd = ['gofmt', '-l', *files]
        code, fmt_out = runner(fmt_cmd, module_dir, timeout)
        unformatted = [line for line in fmt_out.splitlines() if line.strip()]
        result = 'passed' if code == 0 and not unformatted else 'failed'
        summary = 'All files formatted' if result == 'passed' else '%d file(s) need gofmt' % len(unformatted)
        checks.append(row('gofmt', ['gofmt', '-l', '<%d files>' % len(files)], result, summary, fmt_out))
    else:
        checks.append(row('gofmt', None, 'not_run', 'gofmt not available' if files else 'No Go files listed'))

    vet_cmd = ['go', 'vet', *tag_args, *packages]
    code, out = runner(vet_cmd, module_dir, timeout)
    checks.append(row('vet', vet_cmd, 'passed' if code == 0 else 'failed',
                      'go vet clean' if code == 0 else 'go vet reported issues', out))

    with tempfile.TemporaryDirectory(prefix='builder-go-build-') as scratch:
        build_cmd = ['go', 'build', *tag_args, '-o', scratch + os.sep, *packages]
        code, out = runner(build_cmd, module_dir, timeout)
    if code and 'no main packages to build' in out:
        # Without main packages go build writes nothing, so -o is unnecessary.
        build_cmd = ['go', 'build', *tag_args, *packages]
        code, out = runner(build_cmd, module_dir, timeout)
    checks.append(row('build', build_cmd, 'passed' if code == 0 else 'failed',
                      'Build succeeded (binaries discarded)' if code == 0 else 'Build failed', out))

    test_cmd = ['go', 'test', '-count=1', *tag_args]
    if run_pattern:
        test_cmd += ['-run', run_pattern]
    code, out = runner(test_cmd + packages, module_dir, timeout)
    checks.append(test_row('test', test_cmd + packages, code, out))

    if race:
        race_cmd = test_cmd + ['-race'] + packages
        code, out = runner(race_cmd, module_dir, timeout)
        if code and re.search(r'-race requires cgo|race detector.*not supported|C compiler .* not found', out):
            checks.append(row('race', race_cmd, 'not_run', 'Race detector unavailable (CGO/compiler)', out))
        else:
            checks.append(test_row('race', race_cmd, code, out))

    if lint:
        config = next((n for n in LINT_CONFIGS if (module_dir / n).is_file()), None)
        if not config:
            checks.append(row('lint', None, 'not_run', 'No golangci-lint configuration in the module; not created by Builder'))
        elif not which('golangci-lint'):
            checks.append(row('lint', None, 'not_run', 'golangci-lint not installed; not installed by Builder'))
        else:
            lint_cmd = ['golangci-lint', 'run', *packages]
            code, out = runner(lint_cmd, module_dir, timeout)
            checks.append(row('lint', lint_cmd, 'passed' if code == 0 else 'failed',
                              'Linter clean' if code == 0 else 'Linter reported issues', out))
    return finish(context, checks)


def test_row(name, command, code, out):
    if code is None:
        return row(name, command, 'not_run', 'go not executable', out)
    if code == 124:
        return row(name, command, 'failed', 'Timed out', out)
    if code == 0 and 'no test files' in out and not re.search(r'^ok\s', out, re.M):
        return row(name, command, 'not_run', 'Compiled; the selected packages have no test files', out)
    if '(cached)' in out:
        return row(name, command, 'failed' if code else 'passed', 'Unexpected cached result despite -count=1', out)
    failed = re.findall(r'^--- FAIL: (\S+)', out, re.M)
    if code == 0:
        return row(name, command, 'passed', 'Tests passed', out)
    return row(name, command, 'failed', ('Failing: ' + ', '.join(failed[:10])) if failed else 'go test failed', out)


def finish(context, checks):
    executed = [c for c in checks if c['result'] in ('passed', 'failed')]
    failed = [c for c in checks if c['result'] in ('failed', 'blocked')]
    return {'context': context, 'checks': checks,
            'passed': bool(executed) and not failed,
            'note': 'Evidence of executed commands only; behavioural acceptance still needs criteria-specific tests.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    discover_cmd = commands.add_parser('discover', help='Static Go module discovery')
    discover_cmd.add_argument('path', nargs='?', default='.')
    validate_cmd = commands.add_parser('validate', help='Read-only validation ladder')
    validate_cmd.add_argument('path', nargs='?', default='.')
    validate_cmd.add_argument('--packages', nargs='+', default=None,
                              help='Package patterns relative to the module (default ./...)')
    validate_cmd.add_argument('--race', action='store_true')
    validate_cmd.add_argument('--lint', action='store_true')
    validate_cmd.add_argument('--run', dest='run_pattern')
    validate_cmd.add_argument('--tags')
    validate_cmd.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args(argv)
    try:
        if args.command == 'discover':
            result = discover(args.path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['go_module'] else 1
        result = validate(args.path, args.packages, race=args.race, lint=args.lint,
                          run_pattern=args.run_pattern, tags=args.tags, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['passed'] else 1
    except (InputError, OSError, UnicodeDecodeError) as exc:
        print(json.dumps({'error': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
