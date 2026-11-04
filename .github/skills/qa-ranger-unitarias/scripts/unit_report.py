"""Convierte reportes nativos de pruebas unitarias en datos del contrato QA.

coverage lee LCOV, Istanbul json-summary, Cobertura XML o JaCoCo XML y produce
el bloque data.coverage. junit lee uno o varios JUnit XML de una corrida y produce data.verification.
Solo traduce los reportes recibidos: no ejecuta pruebas ni completa métricas
que el runner no reporta.
"""
import argparse
from fnmatch import fnmatch
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

METRICS = ('lines', 'branches', 'functions', 'statements')
LCOV = {'LF': ('lines', 'total'), 'LH': ('lines', 'covered'),
        'BRF': ('branches', 'total'), 'BRH': ('branches', 'covered'),
        'FNF': ('functions', 'total'), 'FNH': ('functions', 'covered')}
JACOCO = {'LINE': 'lines', 'BRANCH': 'branches', 'METHOD': 'functions'}


class ReportError(ValueError):
    pass


def count(value):
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        return int(value)
    if type(value) is int and value >= 0:
        return value
    raise ReportError(f'Conteo inválido: {value!r}')


def checked_totals(totals):
    if not totals:
        raise ReportError('El reporte no contiene métricas de cobertura')
    for metric, counts in totals.items():
        if set(counts) != {'covered', 'total'}:
            raise ReportError(f'Contadores incompletos para {metric}')
        covered, total = count(counts['covered']), count(counts['total'])
        if covered > total:
            raise ReportError(f'Cobertura de {metric} mayor al denominador')
    return totals


def selected(name, include, exclude):
    name = name.replace('\\', '/')
    return (not include or any(fnmatch(name, p) for p in include)) and not any(fnmatch(name, p) for p in exclude)


def parse_lcov(text, include, exclude):
    totals, current, files, record, names = {}, None, 0, {}, set()
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('SF:'):
            if current is not None:
                raise ReportError('Registro LCOV sin end_of_record')
            name = line[3:].replace('\\', '/')
            if not name or name in names:
                raise ReportError('Archivo LCOV vacío o duplicado')
            names.add(name)
            current = selected(line[3:], include, exclude)
            files += current
            record = {}
        elif line == 'end_of_record':
            if current:
                checked_totals(record)
                for metric, counts in record.items():
                    target = totals.setdefault(metric, {'covered': 0, 'total': 0})
                    for field, value in counts.items():
                        target[field] += value
            current = None
        elif current and ':' in line:
            key, value = line.split(':', 1)
            if key in LCOV:
                metric, field = LCOV[key]
                counts = record.setdefault(metric, {})
                if field in counts:
                    raise ReportError(f'Contador LCOV duplicado: {key}')
                counts[field] = count(value)
    if current is not None:
        raise ReportError('Registro LCOV sin end_of_record')
    if not files:
        raise ReportError('El reporte LCOV no contiene archivos dentro del alcance')
    return checked_totals(totals)


def parse_istanbul(data, include, exclude):
    if not isinstance(data, dict):
        raise ReportError('El resumen Istanbul debe ser un objeto')
    if include or exclude:
        entries = [v for k, v in data.items() if k != 'total' and selected(k, include, exclude)]
        if not entries:
            raise ReportError('El resumen Istanbul no contiene archivos dentro del alcance')
    else:
        if 'total' not in data:
            raise ReportError('El resumen Istanbul no tiene la entrada total')
        entries = [data['total']]
    totals = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ReportError('Entrada Istanbul inválida')
        record = {}
        for metric in METRICS:
            if metric in entry:
                record[metric] = {field: count(entry[metric][field]) for field in ('covered', 'total')}
        checked_totals(record)
        for metric, values in record.items():
            counts = totals.setdefault(metric, {'covered': 0, 'total': 0})
            counts['covered'] += values['covered']
            counts['total'] += values['total']
    return checked_totals(totals)


def parse_xml(root):
    if root.tag == 'coverage':
        # Escenario: coverage.py sin --branch escribe branches-valid="0".
        # El denominador cero queda como métrica desconocida, no como éxito.
        totals = {}
        for metric, prefix in (('lines', 'lines'), ('branches', 'branches')):
            if f'{prefix}-valid' in root.attrib:
                totals[metric] = {'covered': count(root.attrib[f'{prefix}-covered']),
                                  'total': count(root.attrib[f'{prefix}-valid'])}
        if not totals:
            raise ReportError('El reporte Cobertura no declara lines-valid ni branches-valid')
        return checked_totals(totals)
    if root.tag == 'report':
        totals = {}
        # Solo los contadores directos de <report> resumen todo el reporte.
        for counter in root.findall('counter'):
            metric = JACOCO.get(counter.get('type'))
            if metric:
                if metric in totals:
                    raise ReportError(f'Contador JaCoCo duplicado: {metric}')
                covered, missed = count(counter.get('covered')), count(counter.get('missed'))
                totals[metric] = {'covered': covered, 'total': covered + missed}
        if not totals:
            raise ReportError('El reporte JaCoCo no tiene contadores de nivel report')
        return checked_totals(totals)
    raise ReportError(f'Formato XML no reconocido: <{root.tag}>')


def read_coverage(path, include=(), exclude=()):
    text = Path(path).read_text(encoding='utf-8')
    stripped = text.lstrip()
    if stripped.startswith('{'):
        return parse_istanbul(json.loads(text), include, exclude)
    if stripped.startswith('<'):
        if include or exclude:
            raise ReportError('--include/--exclude solo aplican a LCOV e Istanbul; ajusta el alcance en el runner')
        return parse_xml(ET.fromstring(text))
    return parse_lcov(text, include, exclude)


def coverage_block(totals, *, scope, command, revision, source_artifact):
    checked_totals(totals)
    return {'level': 'unit', 'scope': scope, 'command': command, 'revision': revision,
            'sourceArtifact': source_artifact, 'supportedMetrics': [m for m in METRICS if m in totals],
            'metrics': {m: totals.get(m) for m in METRICS}}


def read_junit(paths):
    # Escenario: Surefire y Gradle escriben un TEST-*.xml por clase de prueba.
    # Se suman todos los archivos de la misma corrida.
    counts = {'passed': 0, 'failed': 0, 'skipped': 0}
    seen = set()
    for path in paths:
        resolved = Path(path).resolve()
        if resolved in seen:
            raise ReportError(f'Reporte JUnit duplicado: {path}')
        seen.add(resolved)
        root = ET.parse(path).getroot()
        if root.tag not in ('testsuites', 'testsuite'):
            raise ReportError(f'Formato JUnit no reconocido en {path}: <{root.tag}>')
        for suite in root.iter():
            if suite.tag not in ('testsuites', 'testsuite'):
                continue
            cases = list(suite.iter('testcase'))
            observed = {'tests': len(cases),
                        'failures': sum(c.find('failure') is not None for c in cases),
                        'errors': sum(c.find('error') is not None for c in cases),
                        'skipped': sum(c.find('skipped') is not None for c in cases)}
            for key, actual in observed.items():
                if key in suite.attrib and count(suite.attrib[key]) != actual:
                    raise ReportError(f'Resumen JUnit inconsistente: {key} en {path}')
            if suite.find('error') is not None or suite.find('failure') is not None:
                raise ReportError(f'Error de suite fuera de un testcase en {path}')
        for case in root.iter('testcase'):
            if case.find('failure') is not None or case.find('error') is not None:
                counts['failed'] += 1
            elif case.find('skipped') is not None:
                counts['skipped'] += 1
            else:
                counts['passed'] += 1
    return counts


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='action', required=True)
    c = sub.add_parser('coverage', help='Produce data.coverage desde un reporte de cobertura')
    c.add_argument('report', type=Path)
    c.add_argument('--scope', required=True, help='Unidad o carpeta medida, p. ej. src/pricing')
    c.add_argument('--command', required=True, help='Comando exacto que generó el reporte')
    c.add_argument('--revision', required=True, help='Commit o versión medida')
    c.add_argument('--source-artifact', default='coverage', help='ID del artefacto coverage_report')
    c.add_argument('--include', action='append', default=[], help='Patrón de archivos medidos (LCOV/Istanbul)')
    c.add_argument('--exclude', action='append', default=[], help='Patrón de archivos excluidos (LCOV/Istanbul)')
    j = sub.add_parser('junit', help='Produce data.verification desde JUnit XML')
    j.add_argument('reports', type=Path, nargs='+')
    j.add_argument('--command', required=True, help='Comando exacto que ejecutó las pruebas')
    j.add_argument('--exit-code', type=int, required=True, help='Código de salida real del runner')
    j.add_argument('--source-artifact', default='raw', help='ID del artefacto raw_results')
    args = parser.parse_args()
    try:
        if args.action == 'coverage':
            output = coverage_block(read_coverage(args.report, args.include, args.exclude), scope=args.scope,
                                    command=args.command, revision=args.revision,
                                    source_artifact=args.source_artifact)
        else:
            output = {'command': args.command, 'exitCode': args.exit_code,
                      'sourceArtifact': args.source_artifact, **read_junit(args.reports)}
    except (ReportError, OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        print(json.dumps({'valid': False, 'errors': [str(error)]}, ensure_ascii=False))
        return 1
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
