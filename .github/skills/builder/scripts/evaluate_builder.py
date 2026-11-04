"""Offline Builder evaluation harness. Run candidates only in a trusted sandbox."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

CAMPAIGN_VARIANTS = ('control', 'previous', 'candidate')
CAMPAIGN_REPETITIONS = 5

SKILL_ROOT = Path(__file__).resolve().parents[1]
ROOT = SKILL_ROOT / 'evaluations'


def workspace_path(value, *, must_exist=False):
    # Inspect the original spelling before resolve follows symlinks/junctions.
    raw = Path(value).absolute()
    for part in (raw, *raw.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode) or
                getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError('Workspace and its ancestors must not be links or junctions')
    resolved = raw.resolve(strict=must_exist)
    if resolved == SKILL_ROOT or resolved in SKILL_ROOT.parents or SKILL_ROOT in resolved.parents:
        raise ValueError('Workspace must not overlap the skill package')
    return resolved


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def prepare(case, workspace):
    cases = read(ROOT / 'cases.json')
    if case not in cases:
        raise ValueError('Unknown case')
    workspace = workspace_path(workspace)
    if workspace.exists():
        raise ValueError('Workspace must not exist; existing contents are never overwritten')
    shutil.copytree(ROOT / 'fixtures' / case, workspace)
    (workspace / 'TASK.md').write_text(cases[case]['prompt'] + '\n', encoding='utf-8')
    return {'case': case, 'workspace': str(workspace)}


def requirement_available(tool):
    if tool == 'junit-standalone':
        jar = Path(os.environ.get('BUILDER_JUNIT_STANDALONE', '/usr/share/java/junit-platform-console-standalone.jar'))
        return jar.is_file()
    if tool == 'angular-deps':
        deps = Path(os.environ.get('BUILDER_ANGULAR_DEPS', ''))
        return deps.name == 'node_modules' and (deps / '.bin' / 'ng').exists()
    return shutil.which(tool) is not None


def check(case, workspace):
    cases = read(ROOT / 'cases.json')
    if case not in cases:
        raise ValueError('Unknown case')
    workspace = workspace_path(workspace, must_exist=True)
    missing = [tool for tool in cases[case].get('requires', []) if not requirement_available(tool)]
    if missing:
        raise ValueError('Required toolchain not available for this case: ' + ', '.join(missing))
    failures = []
    for name in cases[case]['protected']:
        source = ROOT / 'fixtures' / case / name
        candidate = workspace / name
        if (not candidate.is_file() or candidate.is_symlink()
                or hashlib.sha256(source.read_bytes()).digest()
                != hashlib.sha256(candidate.read_bytes()).digest()):
            failures.append('Protected file changed or missing: ' + name)
    for name in cases[case].get('absent', []):
        if (workspace / name).exists():
            failures.append('Forbidden local artifact: ' + name)
    # Oracle source stays outside the candidate workspace. -I ignores PYTHONPATH.
    run = subprocess.run(
        [sys.executable, '-I', str(ROOT / 'oracle.py'), case, str(workspace)],
        cwd=ROOT, capture_output=True, text=True, timeout=cases[case].get('timeout', 20))
    if run.returncode:
        failures.append('External oracle failed: ' + (run.stderr or run.stdout).strip())
    return {'case': case, 'passed': not failures, 'failures': failures}


def prepare_routing(destination):
    destination = Path(destination)
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(read(ROOT / 'routing' / 'prompts.json'), stream, ensure_ascii=False, indent=2)
    return {'prompts': str(destination)}


def check_routing(observations):
    expected = read(ROOT / 'routing' / 'expected.json')
    data = read(observations)
    if not isinstance(data, list):
        raise ValueError('Observations must be an array')
    seen = set()
    results = []
    for row in data:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str):
            raise ValueError('Each observation needs a string id')
        ident = row['id']
        if ident not in expected or ident in seen:
            raise ValueError('Unknown or duplicate observation id: ' + ident)
        seen.add(ident)
        selected = row.get('selected_skills')
        if (not isinstance(selected, list) or any(not isinstance(s, str) for s in selected)
                or len(selected) != len(set(selected))):
            raise ValueError('selected_skills must be a unique list of strings')
        if any(not isinstance(row.get(key), str) or not row[key].strip()
               for key in ('runtime', 'evidence')):
            raise ValueError('Each observation needs runtime and external evidence reference')
        results.append({'id': ident, 'correct': ('builder' in selected) == expected[ident]})
    if seen != set(expected):
        raise ValueError('Missing observations: ' + ', '.join(sorted(set(expected) - seen)))
    return {'correct': sum(r['correct'] for r in results), 'total': len(results),
            'results': results, 'note': 'Routing accuracy only; evidence authenticity requires review.'}


def prepare_campaign(destination, cases, repetitions=CAMPAIGN_REPETITIONS):
    available = read(ROOT / 'cases.json')
    if repetitions < CAMPAIGN_REPETITIONS:
        raise ValueError('Campaigns require at least five repetitions per variant')
    if not cases or len(cases) != len(set(cases)) or any(case not in available for case in cases):
        raise ValueError('Campaign cases must be unique known case names')
    rows = []
    for case in cases:
        for variant in CAMPAIGN_VARIANTS:
            for repetition in range(1, repetitions + 1):
                rows.append({
                    'case': case, 'variant': variant, 'repetition': repetition,
                    'runtime': '', 'skill_revision': '' if variant == 'control' else '',
                    'passed': None, 'criteria_passed': None, 'criteria_total': None,
                    'regressions': None, 'out_of_scope_changes': None,
                    'human_interventions': None, 'tool_calls': None,
                    'duration_seconds': None, 'tokens': None, 'evidence': ''})
    destination = Path(destination)
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(rows, stream, ensure_ascii=False, indent=2)
    return {'campaign': str(destination), 'runs': len(rows), 'repetitions': repetitions}


def check_campaign(observations):
    data = read(observations)
    if not isinstance(data, list) or not data:
        raise ValueError('Campaign observations must be a non-empty array')
    required_ints = ('criteria_passed', 'criteria_total', 'regressions',
                     'out_of_scope_changes', 'human_interventions', 'tool_calls')
    known_cases = read(ROOT / 'cases.json')
    seen = set()
    groups = {}
    for row in data:
        if not isinstance(row, dict):
            raise ValueError('Each campaign observation must be an object')
        case, variant, repetition = row.get('case'), row.get('variant'), row.get('repetition')
        if case not in known_cases or variant not in CAMPAIGN_VARIANTS:
            raise ValueError('Unknown campaign case or variant')
        if not isinstance(repetition, int) or repetition < 1:
            raise ValueError('Repetition must be a positive integer')
        key = (case, variant, repetition)
        if key in seen:
            raise ValueError('Duplicate campaign observation: ' + repr(key))
        seen.add(key)
        if not isinstance(row.get('passed'), bool):
            raise ValueError('passed must be boolean')
        if any(not isinstance(row.get(name), int) or row[name] < 0 for name in required_ints):
            raise ValueError('Campaign counters must be non-negative integers')
        if row['criteria_passed'] > row['criteria_total']:
            raise ValueError('criteria_passed cannot exceed criteria_total')
        if (not isinstance(row.get('duration_seconds'), (int, float))
                or isinstance(row.get('duration_seconds'), bool) or row['duration_seconds'] < 0):
            raise ValueError('duration_seconds must be a non-negative number')
        if row.get('tokens') is not None and (not isinstance(row['tokens'], int) or row['tokens'] < 0):
            raise ValueError('tokens must be null or a non-negative integer')
        if any(not isinstance(row.get(name), str) or not row[name].strip()
               for name in ('runtime', 'evidence')):
            raise ValueError('runtime and evidence are required strings')
        if variant != 'control' and (not isinstance(row.get('skill_revision'), str)
                                     or not row['skill_revision'].strip()):
            raise ValueError('Skill variants require skill_revision')
        groups.setdefault((case, variant), []).append(row)
    cases = {case for case, _variant in groups}
    expected_groups = {(case, variant) for case in cases for variant in CAMPAIGN_VARIANTS}
    if set(groups) != expected_groups:
        raise ValueError('Every case requires control, previous and candidate variants')
    summary = []
    for key, rows in sorted(groups.items()):
        repetitions = sorted(row['repetition'] for row in rows)
        if len(rows) < CAMPAIGN_REPETITIONS or repetitions != list(range(1, len(rows) + 1)):
            raise ValueError('Each variant requires contiguous repetitions starting at 1')
        tokens = [row['tokens'] for row in rows if row['tokens'] is not None]
        summary.append({
            'case': key[0], 'variant': key[1], 'runs': len(rows),
            'pass_rate': sum(row['passed'] for row in rows) / len(rows),
            'criteria_rate': (sum(row['criteria_passed'] for row in rows)
                              / max(1, sum(row['criteria_total'] for row in rows))),
            'regressions': sum(row['regressions'] for row in rows),
            'out_of_scope_changes': sum(row['out_of_scope_changes'] for row in rows),
            'human_interventions': sum(row['human_interventions'] for row in rows),
            'mean_tool_calls': sum(row['tool_calls'] for row in rows) / len(rows),
            'mean_duration_seconds': sum(row['duration_seconds'] for row in rows) / len(rows),
            'mean_tokens': (sum(tokens) / len(tokens)) if tokens else None})
    return {'runs': len(data), 'cases': len(cases), 'summary': summary,
            'note': 'Metrics are descriptive; evidence and semantic scoring require external review.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('prepare', 'check'):
        command = commands.add_parser(name)
        command.add_argument('case')
        command.add_argument('workspace', type=Path)
    commands.add_parser('prepare-routing').add_argument('destination', type=Path)
    commands.add_parser('check-routing').add_argument('observations', type=Path)
    campaign = commands.add_parser('prepare-campaign')
    campaign.add_argument('destination', type=Path)
    campaign.add_argument('cases', nargs='+')
    campaign.add_argument('--repetitions', type=int, default=CAMPAIGN_REPETITIONS)
    commands.add_parser('check-campaign').add_argument('observations', type=Path)
    args = parser.parse_args()
    try:
        if args.command in ('prepare', 'check'):
            result = globals()[args.command](args.case, args.workspace)
        elif args.command == 'prepare-routing':
            result = prepare_routing(args.destination)
        elif args.command == 'check-routing':
            result = check_routing(args.observations)
        elif args.command == 'prepare-campaign':
            result = prepare_campaign(args.destination, args.cases, args.repetitions)
        else:
            result = check_campaign(args.observations)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get('passed') is False or result.get('correct', 0) < result.get('total', 0) else 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({'error': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
