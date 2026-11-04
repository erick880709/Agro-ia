"""Angular profile helper for Builder.

discover     Static workspace discovery (angular.json / Nx, versions, runners,
             conventions, agent instruction files). Never runs npm or ng.
api-status   Stability of Angular symbols in the *installed* packages, read from
             the JSDoc tags of node_modules/@angular/*/types (or index.d.ts):
             @publicApi <version>, @experimental, @developerPreview, @deprecated.
unstable     Lists imports from @angular/* in project sources whose installed
             declaration is @experimental or @developerPreview.
validate     Read-only ladder with local binaries only: tsc --noEmit (app/spec),
             ng lint (if configured), ng test --watch=false, optional ng build
             into a temporary output path. Never installs dependencies.

Exit codes: 0 no failures, 1 failures observed (or nothing could be run, or no
Angular workspace found), 2 invalid input or harness error.
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

SKIP_DIRS = {'node_modules', '.angular', 'dist', 'out-tsc', '.git', 'coverage', '.nx', 'tmp'}
MAX_SCANNED_FILES = 8000
AGENT_FILES = ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', '.github/copilot-instructions.md',
               '.cursorrules', '.windsurfrules', '.junie/guidelines.md')
AGENT_DIRS = ('.cursor/rules', '.claude/rules', '.github/instructions')
LIBS = {
    'ngrx-store': '@ngrx/store', 'ngrx-signals': '@ngrx/signals', 'ngrx-effects': '@ngrx/effects',
    'ngxs': '@ngxs/store', 'angular-material': '@angular/material', 'cdk': '@angular/cdk',
    'angular-aria': '@angular/aria', 'primeng': 'primeng', 'ng-zorro': 'ng-zorro-antd',
    'transloco': '@jsverse/transloco', 'ngx-translate': '@ngx-translate/core',
    'localize': '@angular/localize', 'ssr': '@angular/ssr', 'service-worker': '@angular/service-worker',
    'module-federation': '@angular-architects/module-federation',
    'native-federation': '@angular-architects/native-federation', 'nx': 'nx',
    'angular-eslint': 'angular-eslint', 'eslint': 'eslint', 'jest': 'jest', 'vitest': 'vitest',
    'karma': 'karma', 'jasmine': 'jasmine-core', 'cypress': 'cypress', 'playwright': '@playwright/test',
    'testing-library': '@testing-library/angular', 'zone.js': 'zone.js', 'tailwind': 'tailwindcss',
}
PATTERNS = {
    'control_flow_blocks': r'@(if|for|switch)\s*\(',
    'structural_directives': r'\*ng(If|For|Switch)\b',
    'signal_inputs': r'\b(input|input\.required|model)\s*[<(]',
    'decorator_inputs': r'@Input\s*\(',
    'ng_modules': r'@NgModule\s*\(',
    'standalone_false': r'standalone\s*:\s*false',
    'inject_fn': r'\binject\s*\(',
    'onpush': r'ChangeDetectionStrategy\.OnPush',
    'eager_or_default_cd': r'ChangeDetectionStrategy\.(Default|Eager)',
    'reactive_forms': r'ReactiveFormsModule|FormBuilder|FormGroup\b',
    'template_forms': r'\bFormsModule\b|ngModel',
    'signal_forms': r"@angular/forms/signals",
    'subscribe_calls': r'\.subscribe\s*\(',
    'take_until_destroyed': r'takeUntilDestroyed',
    'to_signal': r'\btoSignal\s*\(',
    'zoneless_provider': r'provide(Experimental)?ZonelessChangeDetection',
    'zone_provider': r'provideZoneChangeDetection',
    'http_resource': r'\bhttpResource\b',
}


class InputError(ValueError):
    """Invalid arguments or unreadable workspace."""


def read_json(path):
    text = Path(path).read_text(encoding='utf-8')
    # angular.json / tsconfig may contain comments.
    text = re.sub(r'^\s*//.*$', '', text, flags=re.M)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    return json.loads(text)


def major(version):
    match = re.search(r'(\d+)\.(\d+)', version or '')
    return [int(match.group(1)), int(match.group(2))] if match else None


def find_workspace(path):
    path = Path(path).resolve()
    if path.is_file():
        path = path.parent
    for candidate in (path, *path.parents):
        if (candidate / 'angular.json').is_file() or (candidate / 'nx.json').is_file():
            return candidate
        package = candidate / 'package.json'
        if package.is_file():
            try:
                data = read_json(package)
            except (ValueError, OSError):
                continue
            if '@angular/core' in {**data.get('dependencies', {}), **data.get('devDependencies', {})}:
                return candidate
    return None


def installed_version(root, package):
    manifest = Path(root) / 'node_modules' / package / 'package.json'
    if manifest.is_file():
        try:
            return read_json(manifest).get('version')
        except ValueError:
            return None
    return None


def runner_of(builder, options):
    builder = builder or ''
    if builder.endswith(':unit-test'):
        return (options or {}).get('runner', 'vitest')
    for name in ('karma', 'jest', 'vitest', 'web-test-runner'):
        if name in builder:
            return name
    return builder or None


def projects_of(root):
    projects = {}
    if (root / 'angular.json').is_file():
        for name, project in read_json(root / 'angular.json').get('projects', {}).items():
            projects[name] = {'root': project.get('root', ''), 'type': project.get('projectType'),
                              'targets': project.get('architect') or project.get('targets') or {},
                              'schematics': project.get('schematics', {}), 'prefix': project.get('prefix')}
    for project_json in sorted(root.glob('**/project.json')):
        if any(part in SKIP_DIRS for part in project_json.relative_to(root).parts):
            continue
        try:
            data = read_json(project_json)
        except ValueError:
            continue
        name = data.get('name') or project_json.parent.name
        projects.setdefault(name, {'root': project_json.parent.relative_to(root).as_posix(),
                                   'type': data.get('projectType'), 'targets': data.get('targets', {}),
                                   'schematics': data.get('generators', {}), 'prefix': data.get('prefix'),
                                   'tags': data.get('tags', [])})
    summary = {}
    for name, project in projects.items():
        targets = {}
        for target, config in project['targets'].items():
            builder = config.get('builder') or config.get('executor')
            targets[target] = builder
        test = project['targets'].get('test', {})
        summary[name] = {
            'root': project['root'], 'type': project['type'], 'prefix': project.get('prefix'),
            'targets': targets,
            'test_runner': runner_of(test.get('builder') or test.get('executor'), test.get('options')),
            'schematics_defaults': project['schematics'], 'tags': project.get('tags', []),
        }
    return summary


def scan_sources(root):
    counts = {key: 0 for key in PATTERNS}
    compiled = {key: re.compile(value) for key, value in PATTERNS.items()}
    files = specs = 0
    truncated = False
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.'))
        for name in names:
            if not name.endswith(('.ts', '.html')):
                continue
            files += 1
            if files > MAX_SCANNED_FILES:
                truncated = True
                break
            if name.endswith('.spec.ts'):
                specs += 1
                continue
            try:
                text = Path(current, name).read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            for key, pattern in compiled.items():
                counts[key] += len(pattern.findall(text))
        if truncated:
            break
    return {'source_files': files, 'spec_files': specs, 'usage': counts, 'scan_truncated': truncated}


def discover(path):
    target = Path(path)
    if not target.exists():
        raise InputError('Path does not exist: ' + str(path))
    root = find_workspace(target)
    if root is None:
        return {'angular_workspace': False, 'path': str(target.resolve()),
                'note': 'No angular.json, nx.json or @angular/core dependency found; the Angular profile does not apply.'}
    package = read_json(root / 'package.json') if (root / 'package.json').is_file() else {}
    deps = {**package.get('dependencies', {}), **package.get('devDependencies', {})}
    declared = deps.get('@angular/core')
    installed = installed_version(root, '@angular/core')
    lockfile = next((n for n in ('package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'bun.lockb', 'bun.lock')
                     if (root / n).exists()), None)
    agent_files = [n for n in AGENT_FILES if (root / n).exists()]
    for directory in AGENT_DIRS:
        if (root / directory).is_dir():
            agent_files += sorted(p.relative_to(root).as_posix() for p in (root / directory).rglob('*') if p.is_file())
    nested = sorted(p.relative_to(root).as_posix() for p in root.glob('**/CLAUDE.md')
                    if not any(part in SKIP_DIRS for part in p.relative_to(root).parts) and p.parent != root)
    nested += sorted(p.relative_to(root).as_posix() for p in root.glob('**/AGENTS.md')
                     if not any(part in SKIP_DIRS for part in p.relative_to(root).parts) and p.parent != root)
    eslint = next((n for n in ('eslint.config.js', 'eslint.config.mjs', 'eslint.config.cjs', 'eslint.config.ts',
                               '.eslintrc.json', '.eslintrc.js', '.eslintrc') if (root / n).exists()), None)
    node = None
    for name in ('.nvmrc', '.node-version'):
        if (root / name).is_file():
            node = (root / name).read_text(encoding='utf-8').strip()
    return {
        'angular_workspace': True,
        'workspace_root': str(root),
        'workspace_kind': 'nx' if (root / 'nx.json').is_file() else 'angular-cli',
        'angular_declared': declared,
        'angular_installed': installed,
        'angular_version': major(installed or declared),
        'version_source': 'node_modules' if installed else ('package.json range' if declared else None),
        'typescript': installed_version(root, 'typescript') or deps.get('typescript'),
        'rxjs': installed_version(root, 'rxjs') or deps.get('rxjs'),
        'dependencies_installed': (root / 'node_modules').is_dir(),
        'package_manager': lockfile,
        'node_version_file': node,
        'node_engines': package.get('engines', {}).get('node'),
        'scripts': package.get('scripts', {}),
        'libraries': sorted(key for key, name in LIBS.items() if name in deps),
        'projects': projects_of(root),
        'eslint_config': eslint,
        'prettier': any((root / n).exists() for n in ('.prettierrc', '.prettierrc.json', 'prettier.config.js', '.prettierrc.mjs')),
        'agent_instruction_files': agent_files + nested,
        'angular_mcp_configured': any((root / n).exists() for n in ('.vscode/mcp.json', '.mcp.json', '.cursor/mcp.json', '.gemini/settings.json')),
        **scan_sources(root),
        'note': 'Static discovery only. Agent instruction files and lint rules are project conventions: read them before editing.',
    }


def declaration_files(node_modules, package):
    base = Path(node_modules) / package
    if not base.is_dir():
        return []
    types = base / 'types'
    if types.is_dir():
        return sorted(types.glob('*.d.ts'))
    return sorted(p for p in base.rglob('*.d.ts') if 'node_modules' not in p.relative_to(base).parts)


DECL = r'/\*\*((?:(?!\*/).)*?)\*/\s*(?:export\s+)?(?:declare\s+)?(?:abstract\s+)?(?:function|const|class|interface|type|enum|let|var)\s+{name}\b'


def api_status(node_modules, symbols, packages=None):
    packages = packages or ['@angular/core', '@angular/common', '@angular/forms', '@angular/router',
                            '@angular/platform-browser', '@angular/common/http']
    result = {}
    cache = {}
    for symbol in symbols:
        if not re.fullmatch(r'[A-Za-z_$][\w$]*', symbol):
            raise InputError('Invalid symbol: ' + symbol)
        found = []
        pattern = re.compile(DECL.format(name=re.escape(symbol)), re.S)
        for package in packages:
            root_package = '/'.join(package.split('/')[:2])
            for file in declaration_files(node_modules, root_package):
                text = cache.get(file)
                if text is None:
                    text = cache[file] = file.read_text(encoding='utf-8', errors='replace')
                for match in pattern.finditer(text):
                    doc = match.group(1)
                    tags = {tag: (value or '').strip() for tag, value in
                            re.findall(r'@(publicApi|experimental|developerPreview|deprecated)\b[ \t]*([\d.]*)', doc)}
                    found.append({'package': root_package, 'file': file.name, 'tags': tags})
            if found:
                break
        if found and not any(entry['tags'] for entry in found) or not found:
            # `declare const input: InputFunction;` documents the interface, not the const.
            for package in packages:
                root_package = '/'.join(package.split('/')[:2])
                for file in declaration_files(node_modules, root_package):
                    text = cache.get(file) or cache.setdefault(file, file.read_text(encoding='utf-8', errors='replace'))
                    alias = re.search(r'declare\s+const\s+' + re.escape(symbol) + r'\s*:\s*([A-Za-z_$][\w$]*)\s*;', text)
                    if alias and alias.group(1) != symbol:
                        inner = api_status(node_modules, [alias.group(1)], [package])[alias.group(1)]
                        found = [dict(d, via=alias.group(1)) for d in inner['declarations']] or found
                        break
                else:
                    continue
                break
        status = 'unknown'
        if found:
            tags = {k: v for entry in found for k, v in entry['tags'].items()}
            if 'experimental' in tags:
                status = 'experimental'
            elif 'developerPreview' in tags:
                status = 'developer-preview'
            elif 'publicApi' in tags:
                status = 'stable'
            if 'deprecated' in tags:
                status += '+deprecated'
        result[symbol] = {'status': status, 'declarations': found[:3]}
    return result


IMPORT = re.compile(r"import\s*(?:type\s*)?\{([^}]*)\}\s*from\s*['\"](@angular/[\w/-]+)['\"]")


def unstable_imports(root, node_modules=None, include_specs=False):
    root = Path(root)
    node_modules = Path(node_modules) if node_modules else root / 'node_modules'
    if not (node_modules / '@angular' / 'core').is_dir():
        raise InputError('Installed @angular/core not found under ' + str(node_modules))
    usages = {}
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.'))
        for name in names:
            if not name.endswith('.ts') or (name.endswith('.spec.ts') and not include_specs):
                continue
            text = Path(current, name).read_text(encoding='utf-8', errors='replace')
            for names_part, package in IMPORT.findall(text):
                for raw in names_part.split(','):
                    symbol = raw.strip().split(' as ')[0].replace('type ', '').strip()
                    if symbol:
                        usages.setdefault((package, symbol), []).append(Path(current, name).relative_to(root).as_posix())
    findings = []
    for (package, symbol), files in sorted(usages.items()):
        status = api_status(node_modules, [symbol], [package])[symbol]['status']
        if status.startswith(('experimental', 'developer-preview')):
            findings.append({'symbol': symbol, 'package': package, 'status': status, 'files': sorted(set(files))})
    return {'unstable': findings, 'checked_symbols': len(usages)}


def run(command, cwd, timeout, env=None):
    try:
        done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                              env={**os.environ, 'NG_CLI_ANALYTICS': 'false', 'CI': '1', **(env or {})})
    except FileNotFoundError:
        return None, 'Command not found: ' + command[0]
    except subprocess.TimeoutExpired:
        return 124, 'Timed out after %ss' % timeout
    return done.returncode, done.stdout + done.stderr


ANSI = re.compile(r'\x1b\[[0-9;]*m')


def row(check, command, result, summary, output=''):
    clean = ANSI.sub('', output or '').strip().splitlines()
    return {'check': check, 'command': ' '.join(command) if command else '', 'result': result,
            'summary': summary, 'output_tail': '\n'.join(clean[-40:])}


def validate(path, project=None, *, include=None, build=False, lint=True, timeout=900, runner=run):
    root = find_workspace(path) if Path(path).exists() else None
    if root is None:
        raise InputError('No Angular workspace found for: ' + str(path))
    if include and (include.startswith('-') or not re.fullmatch(r'[\w./*{},@-]+', include)):
        raise InputError('Unsupported --include glob')
    if project and not re.fullmatch(r'[\w@./-]+', project):
        raise InputError('Unsupported project name')
    projects = projects_of(root)
    if project is None and len(projects) == 1:
        project = next(iter(projects))
    info = projects.get(project) if project else None
    context = {'workspace_root': str(root), 'project': project,
               'angular_installed': installed_version(root, '@angular/core'),
               'test_runner': info['test_runner'] if info else None}
    checks = []
    bin_dir = root / 'node_modules' / '.bin'
    if not bin_dir.is_dir():
        for name in ('typecheck', 'lint', 'test', 'build'):
            checks.append(row(name, None, 'not_run',
                              'Dependencies not installed; Builder does not run npm install without a mandate'))
        return finish(context, checks)
    code, out = runner(['node', '--version'], root, 30)
    context['node_version'] = out.strip() if code == 0 else None
    tsc = bin_dir / 'tsc'
    project_root = root / (info['root'] if info else '')
    for label, config in (('typecheck-app', 'tsconfig.app.json'), ('typecheck-spec', 'tsconfig.spec.json')):
        tsconfig = project_root / config
        if not tsconfig.is_file():
            checks.append(row(label, None, 'not_run', config + ' not found'))
            continue
        command = [str(tsc), '-p', str(tsconfig), '--noEmit']
        code, out = runner(command, root, timeout)
        checks.append(row(label, command, 'passed' if code == 0 else 'failed',
                          'TypeScript clean (templates are checked by ng build/test)' if code == 0 else 'TypeScript errors', out))
    ng = bin_dir / 'ng'
    targets = info['targets'] if info else {}
    if lint:
        if 'lint' in targets:
            command = [str(ng), 'lint'] + ([project] if project else [])
            code, out = runner(command, root, timeout)
            checks.append(row('lint', command, 'passed' if code == 0 else 'failed',
                              'Lint clean' if code == 0 else 'Lint reported issues', out))
        else:
            checks.append(row('lint', None, 'not_run', 'No lint target configured; Builder does not add one'))
    if 'test' in targets:
        command = [str(ng), 'test'] + ([project] if project else []) + ['--watch=false']
        runner_name = info['test_runner'] if info else None
        if runner_name == 'karma':
            command += ['--browsers=ChromeHeadless']
        if include:
            command += ['--include', include]
        code, out = runner(command, root, timeout)
        if code and re.search(r'No binary for Chrome|CHROME_BIN|Cannot start Chrome', out):
            checks.append(row('test', command, 'not_run', 'Test browser unavailable', out))
        elif code == 0 and re.search(r'No (spec|test) files found|No test files found', out, re.I):
            checks.append(row('test', command, 'not_run', 'No test files matched', out))
        else:
            checks.append(row('test', command, 'passed' if code == 0 else 'failed',
                              'Tests passed' if code == 0 else 'Tests failed', out))
    else:
        checks.append(row('test', None, 'not_run', 'No test target configured'))
    if build:
        if 'build' in targets:
            with tempfile.TemporaryDirectory(prefix='builder-ng-build-') as scratch:
                command = [str(ng), 'build'] + ([project] if project else []) + ['--output-path', scratch]
                code, out = runner(command, root, timeout)
            budget = bool(re.search(r'budget', out, re.I)) and code != 0
            checks.append(row('build', command, 'passed' if code == 0 else 'failed',
                              'Production build succeeded (output discarded)' if code == 0 else
                              ('Bundle budget exceeded' if budget else 'Build failed'), out))
        else:
            checks.append(row('build', None, 'not_run', 'No build target configured'))
    return finish(context, checks)


def finish(context, checks):
    executed = [c for c in checks if c['result'] in ('passed', 'failed')]
    failed = [c for c in checks if c['result'] == 'failed']
    return {'context': context, 'checks': checks, 'passed': bool(executed) and not failed,
            'note': 'Evidence of executed commands only; behavioural acceptance still needs criteria-specific tests.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    discover_cmd = commands.add_parser('discover')
    discover_cmd.add_argument('path', nargs='?', default='.')
    status_cmd = commands.add_parser('api-status')
    status_cmd.add_argument('symbols', nargs='+')
    status_cmd.add_argument('--path', default='.')
    unstable_cmd = commands.add_parser('unstable')
    unstable_cmd.add_argument('path', nargs='?', default='.')
    unstable_cmd.add_argument('--include-specs', action='store_true')
    validate_cmd = commands.add_parser('validate')
    validate_cmd.add_argument('path', nargs='?', default='.')
    validate_cmd.add_argument('--project')
    validate_cmd.add_argument('--include', help='Spec glob passed to ng test --include')
    validate_cmd.add_argument('--build', action='store_true', help='Also run ng build into a temp dir')
    validate_cmd.add_argument('--no-lint', action='store_true')
    validate_cmd.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args(argv)
    try:
        if args.command == 'discover':
            result = discover(args.path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['angular_workspace'] else 1
        if args.command in ('api-status', 'unstable'):
            root = find_workspace(args.path)
            if root is None:
                raise InputError('No Angular workspace found for: ' + args.path)
            if args.command == 'api-status':
                if not (root / 'node_modules' / '@angular' / 'core').is_dir():
                    raise InputError('Installed @angular/core not found; api-status reads installed packages only')
                result = api_status(root / 'node_modules', args.symbols)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
            result = unstable_imports(root, include_specs=args.include_specs)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if result['unstable'] else 0
        result = validate(args.path, args.project, include=args.include, build=args.build,
                          lint=not args.no_lint, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['passed'] else 1
    except (InputError, OSError, ValueError) as exc:
        print(json.dumps({'error': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
