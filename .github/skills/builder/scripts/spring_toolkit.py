"""Java / Spring Boot profile helper for Builder.

discover      Static discovery: build tool and wrapper, Java release, Spring Boot
              version, Bancolombia Scaffold, modules, imperative vs reactive stack,
              libraries, conventions and agent instruction files. Never runs builds.
class-status  Whether fully-qualified classes exist in the dependency jars already
              present in the local Maven/Gradle caches (or --jars), in which artifact
              versions, and whether `javap` reports them @Deprecated. Use it to check
              package moves between Spring Boot / Testcontainers / Jackson majors.
validate      Read-only ladder through the project wrapper only (gradlew / mvnw):
              compile, focused tests, configured static checks, optional full build
              and Scaffold validateStructure. Never installs or upgrades anything.

Exit codes: 0 no failures, 1 failures observed (or nothing could be run, or no
Java project found), 2 invalid input or harness error.
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
import zipfile

SKIP_DIRS = {'.git', 'build', 'target', '.gradle', 'node_modules', 'out', '.idea', 'bin'}
MAX_SCANNED_FILES = 12000
AGENT_FILES = ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', '.github/copilot-instructions.md', '.cursorrules',
               '.windsurfrules', '.junie/guidelines.md')
LIBS = {
    'webmvc': ('spring-boot-starter-web', 'spring-boot-starter-webmvc'),
    'webflux': ('spring-boot-starter-webflux',),
    'data-jpa': ('spring-boot-starter-data-jpa',),
    'data-jdbc': ('spring-boot-starter-data-jdbc', 'spring-boot-starter-jdbc'),
    'r2dbc': ('spring-boot-starter-data-r2dbc', 'r2dbc-'),
    'mongodb': ('spring-boot-starter-data-mongodb',),
    'security': ('spring-boot-starter-security',),
    'oauth2-resource-server': ('spring-boot-starter-oauth2-resource-server',),
    'validation': ('spring-boot-starter-validation',),
    'actuator': ('spring-boot-starter-actuator',),
    'kafka': ('spring-kafka',),
    'reactive-commons': ('reactive-commons', 'async-commons'),
    'resilience4j': ('resilience4j',),
    'flyway': ('flyway',),
    'liquibase': ('liquibase',),
    'lombok': ('lombok',),
    'mapstruct': ('mapstruct',),
    'springdoc': ('springdoc',),
    'micrometer-tracing': ('micrometer-tracing',),
    'testcontainers': ('testcontainers',),
    'reactor-test': ('reactor-test',),
    'blockhound': ('blockhound',),
    'archunit': ('archunit',),
    'mockito': ('mockito',),
    'assertj': ('assertj',),
    'wiremock': ('wiremock',),
    'jacoco': ('jacoco',),
    'pitest': ('pitest',),
    'spotless': ('spotless',),
    'checkstyle': ('checkstyle',),
    'pmd': ('pmd',),
    'spotbugs': ('spotbugs',),
    'sonar': ('sonar',),
    'jib': ('jib',),
}
PATTERNS = {
    'field_injection': r'@Autowired\s+(?:private|protected|public)?\s*[\w<>,\s]+\s+\w+\s*;',
    'jakarta_imports': r'import\s+jakarta\.',
    'javax_ee_imports': r'import\s+javax\.(persistence|validation|servlet|annotation\.PostConstruct|transaction)\b',
    'transactional': r'@Transactional\b',
    'block_calls_main': r'\.block(First|Last|Optional)?\s*\(',
    'mono_flux': r'\b(Mono|Flux)<',
    'record_types': r'\brecord\s+\w+\s*\(',
    'entity_classes': r'@Entity\b',
    'rest_controllers': r'@RestController\b',
    'router_functions': r'RouterFunction<',
    'mock_bean': r'@MockBean\b',
    'mockito_bean': r'@MockitoBean\b',
    'lombok_annotations': r'@(Data|Getter|Setter|Builder|RequiredArgsConstructor|AllArgsConstructor|Value)\b',
    'controller_advice': r'@(Rest)?ControllerAdvice\b',
    'problem_detail': r'\bProblemDetail\b',
    'rest_template': r'\bRestTemplate\b',
    'web_client': r'\bWebClient\b',
    'rest_client': r'\bRestClient\b',
}


class InputError(ValueError):
    """Invalid arguments or unreadable project."""


def read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def find_root(path):
    path = Path(path).resolve()
    if path.is_file():
        path = path.parent
    chain = (path, *path.parents)
    for candidate in chain:
        if any((candidate / n).is_file() for n in ('settings.gradle', 'settings.gradle.kts')):
            return candidate
    poms = [c for c in chain if (c / 'pom.xml').is_file()]
    if poms:
        top = poms[0]
        for candidate in poms[1:]:
            if candidate == top.parent:
                top = candidate
        return top
    return next((c for c in chain if any((c / n).is_file() for n in ('build.gradle', 'build.gradle.kts'))), None)


def java_release(root, build_text, props):
    for pattern in (r'languageVersion\s*(?:=|\.set\()\s*JavaLanguageVersion\.of\(\s*(\d+)',
                    r'sourceCompatibility\s*=\s*(?:JavaVersion\.VERSION_)?[\'"]?(\d+)',
                    r'options\.release\s*(?:=|\.set\()\s*(\d+)',
                    r'<maven\.compiler\.release>\s*(\d+)', r'<java\.version>\s*(\d+)',
                    r'<release>\s*(\d+)\s*</release>', r'<maven\.compiler\.source>\s*(\d+)'):
        match = re.search(pattern, build_text)
        if match:
            return int(match.group(1))
    match = re.search(r'javaVersion\s*=\s*VERSION_(\d+)', props)
    if match:
        return int(match.group(1))
    return None


def boot_version(build_text, props):
    for pattern in (r"id\s*\(?\s*['\"]org\.springframework\.boot['\"]\s*\)?\s*version\s*\(?\s*['\"]([\w.\-]+)",
                    r'<artifactId>spring-boot-starter-parent</artifactId>\s*<version>([\w.\-]+)</version>',
                    r'<artifactId>spring-boot-dependencies</artifactId>\s*<version>([\w.\-]+)</version>',
                    r'springBootVersion\s*=\s*[\'"]([\w.\-]+)', r'spring-boot-gradle-plugin:([\w.\-]+)'):
        match = re.search(pattern, build_text)
        if match:
            return match.group(1)
    match = re.search(r'springBootVersion\s*=\s*([\w.\-]+)', props)
    return match.group(1) if match else None


def modules(root):
    found = []
    for settings in ('settings.gradle', 'settings.gradle.kts'):
        text = read(root / settings)
        found += re.findall(r"include\s*\(?\s*['\"]:?([\w\-:]+)['\"]", text)
    pom = read(root / 'pom.xml')
    found += re.findall(r'<module>([^<]+)</module>', pom)
    return sorted(set(found))


def build_files(root):
    files = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.'))
        for name in names:
            if name in ('build.gradle', 'build.gradle.kts', 'pom.xml', 'main.gradle', 'libs.versions.toml',
                        'gradle.properties'):
                files.append(Path(current, name))
    for catalog in (root / 'gradle').glob('*.toml'):
        files.append(catalog)
    return files


def scan_sources(root):
    compiled = {k: re.compile(v) for k, v in PATTERNS.items()}
    counts = {k: 0 for k in PATTERNS}
    main_files = test_files = 0
    truncated = False
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.'))
        for name in names:
            if not name.endswith(('.java', '.kt')):
                continue
            path = Path(current, name)
            is_test = f'{os.sep}src{os.sep}test{os.sep}' in str(path) or f'{os.sep}src{os.sep}integrationTest' in str(path)
            if is_test:
                test_files += 1
            else:
                main_files += 1
            if main_files + test_files > MAX_SCANNED_FILES:
                truncated = True
                break
            text = read(path)
            for key, pattern in compiled.items():
                if key == 'block_calls_main' and is_test:
                    continue
                if key in ('mock_bean', 'mockito_bean') and not is_test:
                    continue
                counts[key] += len(pattern.findall(text))
        if truncated:
            break
    return {'main_sources': main_files, 'test_sources': test_files, 'usage': counts, 'scan_truncated': truncated}


def discover(path):
    target = Path(path)
    if not target.exists():
        raise InputError('Path does not exist: ' + str(path))
    root = find_root(target)
    if root is None:
        return {'java_project': False, 'path': str(target.resolve()),
                'note': 'No pom.xml, build.gradle or settings.gradle found; the Java/Spring profile does not apply.'}
    texts = {str(p.relative_to(root)): read(p) for p in build_files(root)}
    joined = '\n'.join(texts.values())
    props = read(root / 'gradle.properties')
    gradle = any(n.endswith(('.gradle', '.gradle.kts')) for n in texts)
    maven = (root / 'pom.xml').is_file()
    scaffold = bool(re.search(r'co\.com\.bancolombia\.cleanArchitecture', joined))
    reactive_flag = re.search(r'^\s*reactive\s*=\s*(true|false)', props, re.M)
    dependency_text = '\n'.join(t for n, t in texts.items() if not n.endswith('gradle.properties'))
    libs = {name for name, needles in LIBS.items() if any(n in dependency_text for n in needles)}
    if re.search(r'^\s*lombok\s*=\s*true', props, re.M):
        libs.add('lombok')
    libs = sorted(libs)
    if 'webflux' in libs or (reactive_flag and reactive_flag.group(1) == 'true'):
        stack = 'reactive'
    elif 'webmvc' in libs or (reactive_flag and reactive_flag.group(1) == 'false'):
        stack = 'imperative'
    else:
        stack = 'unknown'
    agent = [n for n in AGENT_FILES if (root / n).exists()]
    agent += sorted(p.relative_to(root).as_posix() for p in root.glob('**/CLAUDE.md')
                    if p.parent != root and not any(x in SKIP_DIRS for x in p.relative_to(root).parts))
    configs = sorted(p.relative_to(root).as_posix() for p in root.glob('**/src/main/resources/application*.*')
                     if not any(x in SKIP_DIRS for x in p.relative_to(root).parts))
    return {
        'java_project': True,
        'root': str(root),
        'build_tool': 'gradle' if gradle else ('maven' if maven else None),
        'wrapper': {'gradlew': (root / 'gradlew').is_file(), 'mvnw': (root / 'mvnw').is_file()},
        'java_release': java_release(root, joined, props),
        'spring_boot': boot_version(joined, props),
        'bancolombia_scaffold': scaffold,
        'scaffold_properties': {k: v for k, v in re.findall(r'^\s*(package|reactive|lombok|systemProp\.version|javaVersion)\s*=\s*(\S+)', props, re.M)},
        'stack': stack,
        'modules': modules(root),
        'libraries': libs,
        'build_files': sorted(texts),
        'config_files': configs,
        'agent_instruction_files': agent,
        'architecture_tests': bool(re.search(r'ArchitectureTest|archunit', joined + '\n'.join(
            read(p) for p in list(root.glob('**/src/test/**/*ArchitectureTest*.java'))[:5]))),
        **scan_sources(root),
        'note': 'Static discovery only. Read the reference module, its tests and the Scaffold reference before editing.',
    }


def cache_jars(extra=None):
    roots = [Path(p) for p in (extra or [])]
    if not extra:
        home = Path.home()
        roots = [home / '.m2' / 'repository', home / '.gradle' / 'caches' / 'modules-2' / 'files-2.1']
    for root in roots:
        if root.is_file() and root.suffix == '.jar':
            yield root
        elif root.is_dir():
            yield from root.rglob('*.jar')


def class_status(classes, jars=None, javap=shutil.which):
    entries = {}
    for fqn in classes:
        if not re.fullmatch(r'[A-Za-z_$][\w$]*(\.[A-Za-z_$][\w$]*)+', fqn):
            raise InputError('Invalid class name: ' + fqn)
        entries[fqn] = fqn.replace('.', '/') + '.class'
    found = {fqn: [] for fqn in classes}
    scanned = 0
    for jar in cache_jars(jars):
        if jar.name.endswith(('-sources.jar', '-javadoc.jar')):
            continue
        scanned += 1
        try:
            with zipfile.ZipFile(jar) as archive:
                names = set(archive.namelist())
        except (zipfile.BadZipFile, OSError):
            continue
        for fqn, entry in entries.items():
            if entry in names:
                found[fqn].append(str(jar))
    javap_bin = javap('javap')
    result = {}
    for fqn, locations in found.items():
        deprecated = None
        if locations and javap_bin:
            done = subprocess.run([javap_bin, '-v', '-cp', locations[0], fqn], capture_output=True, text=True, timeout=60)
            if done.returncode == 0:
                deprecated = bool(re.search(r'^\s*Deprecated: true|Ljava/lang/Deprecated;', done.stdout, re.M))
        result[fqn] = {'exists': bool(locations), 'jars': sorted(locations)[:5], 'deprecated': deprecated}
    return {'classes': result, 'jars_scanned': scanned,
            'note': 'Only jars already present locally are inspected; absence may mean the artifact was never downloaded.'}


ANSI = re.compile(r'\x1b\[[0-9;]*m')


def run(command, cwd, timeout):
    try:
        done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return None, 'Command not found: ' + command[0]
    except subprocess.TimeoutExpired:
        return 124, 'Timed out after %ss' % timeout
    return done.returncode, done.stdout + done.stderr


def row(check, command, result, summary, output=''):
    lines = ANSI.sub('', output or '').strip().splitlines()
    return {'check': check, 'command': ' '.join(command) if command else '', 'result': result,
            'summary': summary, 'output_tail': '\n'.join(lines[-40:])}


def validate(path, *, module=None, tests=None, full=False, offline=False, timeout=1800, runner=run):
    info = discover(path)
    if not info['java_project']:
        raise InputError('No Java project found for: ' + str(path))
    if module and not re.fullmatch(r':?[\w\-:]+', module):
        raise InputError('Unsupported module name')
    if tests and (tests.startswith('-') or not re.fullmatch(r'[\w.*#$,\-]+', tests)):
        raise InputError('Unsupported test filter')
    root = Path(info['root'])
    context = {k: info[k] for k in ('root', 'build_tool', 'java_release', 'spring_boot', 'stack', 'bancolombia_scaffold')}
    context.update({'module': module, 'tests': tests})
    code, out = runner(['java', '-version'], root, 60)
    context['jdk'] = (out.strip().splitlines() or [''])[0] if code == 0 else None
    checks = []
    if info['build_tool'] == 'gradle' and info['wrapper']['gradlew']:
        base = [str(root / 'gradlew'), '--no-daemon', '--console=plain'] + (['--offline'] if offline else [])
        prefix = (':' + module.lstrip(':') + ':') if module else ''
        steps = [('compile', base + [prefix + 'compileJava', prefix + 'compileTestJava']),
                 ('test', base + [prefix + 'test'] + (['--tests', tests] if tests else []))]
        configured = [t for t in ('checkstyleMain', 'pmdMain', 'spotlessCheck', 'spotbugsMain')
                      if any(k in info['libraries'] for k in (t.replace('Main', '').replace('Check', ''),))]
        for task in configured:
            steps.append(('static-' + task, base + [prefix + task]))
        if info['bancolombia_scaffold']:
            steps.append(('scaffold-validate-structure', base + ['validateStructure']))
        if full:
            steps.append(('build', base + ['build']))
    elif info['build_tool'] == 'maven' and info['wrapper']['mvnw']:
        base = [str(root / 'mvnw'), '-B', '-ntp'] + (['-o'] if offline else []) + (['-pl', module, '-am'] if module else [])
        steps = [('compile', base + ['-DskipTests', 'test-compile']),
                 ('test', base + ['test'] + (['-Dtest=' + tests, '-Dsurefire.failIfNoSpecifiedTests=false'] if tests else []))]
        for plugin, goal in (('checkstyle', 'checkstyle:check'), ('spotless', 'spotless:check'), ('pmd', 'pmd:check')):
            if plugin in info['libraries']:
                steps.append(('static-' + plugin, base + [goal]))
        if full:
            steps.append(('build', base + ['verify']))
    else:
        checks.append(row('build', None, 'not_run',
                          'No project wrapper (gradlew/mvnw); Builder does not use or install a global build tool'))
        return finish(context, checks)
    blocked = False
    for name, command in steps:
        if blocked:
            checks.append(row(name, command, 'blocked', 'Previous step failed'))
            continue
        code, out = runner(command, root, timeout)
        if code and re.search(r'Could not (resolve|GET|download)|UnknownHostException|offline mode', out):
            checks.append(row(name, command, 'not_run', 'Dependencies or wrapper distribution unavailable (network/offline)', out))
            blocked = True
            continue
        if name == 'test' and code == 0 and re.search(r'No tests found|NO-SOURCE', out) and tests:
            checks.append(row(name, command, 'failed', 'Test filter matched no tests', out))
            continue
        checks.append(row(name, command, 'passed' if code == 0 else 'failed',
                          'OK' if code == 0 else name + ' failed', out))
        if code and name == 'compile':
            blocked = True
    return finish(context, checks)


def finish(context, checks):
    executed = [c for c in checks if c['result'] in ('passed', 'failed')]
    failed = [c for c in checks if c['result'] in ('failed', 'blocked')]
    return {'context': context, 'checks': checks, 'passed': bool(executed) and not failed,
            'note': 'Evidence of executed commands only; behavioural acceptance still needs criteria-specific tests.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    d = commands.add_parser('discover')
    d.add_argument('path', nargs='?', default='.')
    c = commands.add_parser('class-status')
    c.add_argument('classes', nargs='+')
    c.add_argument('--jars', nargs='+', help='Jar files or directories to inspect instead of the local caches')
    v = commands.add_parser('validate')
    v.add_argument('path', nargs='?', default='.')
    v.add_argument('--module')
    v.add_argument('--tests', help='Gradle --tests / Surefire -Dtest filter')
    v.add_argument('--full', action='store_true', help='Also run build/verify')
    v.add_argument('--offline', action='store_true')
    v.add_argument('--timeout', type=int, default=1800)
    args = parser.parse_args(argv)
    try:
        if args.command == 'discover':
            result = discover(args.path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['java_project'] else 1
        if args.command == 'class-status':
            result = class_status(args.classes, args.jars)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        result = validate(args.path, module=args.module, tests=args.tests, full=args.full,
                          offline=args.offline, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['passed'] else 1
    except (InputError, OSError) as exc:
        print(json.dumps({'error': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
