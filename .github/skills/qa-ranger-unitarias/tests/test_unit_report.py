"""Pruebas del conversor de reportes unitarios a datos del contrato QA.

Usa reportes sintéticos en carpetas temporales. No ejecuta runners.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/unit_report.py'
sys.path.insert(0, str(SCRIPT.parent))
import unit_report

LCOV = """TN:
SF:src/descuentos.mjs
FNF:7
FNH:7
BRF:20
BRH:12
LF:58
LH:45
end_of_record
SF:src/descuentos.test.mjs
FNF:3
FNH:3
BRF:4
BRH:4
LF:19
LH:19
end_of_record
"""


class UnitReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)

    def example(self, name, skill):
        file = SCRIPT.parents[2] / skill / 'contracts/examples' / f'{skill}-{name}.json'
        return json.loads(file.read_text(encoding='utf-8'))

    def metrics(self, value):
        # El conversor permanece Python; la aceptación contractual solo vive en Node.
        file = self.write('result.json', json.dumps(value))
        validator = SCRIPT.parents[3] / 'contracts/output/validate.mjs'
        run = subprocess.run(['node', str(validator), str(file), '--project-root', str(self.project)],
                             capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return {m['id']: m['value'] for m in json.loads(run.stdout)['result']['metrics']}

    def write(self, name, text):
        path = self.project / name
        path.write_text(text, encoding='utf-8')
        return path

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8')

    def test_lcov_excludes_test_files_and_leaves_statements_unsupported(self):
        totals = unit_report.read_coverage(self.write('lcov.info', LCOV), exclude=['*.test.mjs'])
        self.assertEqual(totals, {'functions': {'covered': 7, 'total': 7},
                                  'branches': {'covered': 12, 'total': 20},
                                  'lines': {'covered': 45, 'total': 58}})
        everything = unit_report.read_coverage(self.write('all.info', LCOV))
        self.assertEqual(everything['lines'], {'covered': 64, 'total': 77})
        with self.assertRaises(unit_report.ReportError):
            unit_report.read_coverage(self.write('none.info', LCOV), include=['otro/*'])

    def test_istanbul_summary_keeps_the_four_metrics(self):
        counts = {m: {'total': 10, 'covered': 9, 'pct': 90} for m in unit_report.METRICS}
        report = {'total': counts, 'src/a.js': counts, 'src/a.test.js': counts}
        path = self.write('coverage-summary.json', json.dumps(report))
        self.assertEqual(set(unit_report.read_coverage(path)), set(unit_report.METRICS))
        filtered = unit_report.read_coverage(path, exclude=['*.test.js'])
        self.assertEqual(filtered['lines'], {'covered': 9, 'total': 10})

    def test_cobertura_without_branch_mode_is_unknown_not_success(self):
        path = self.write('coverage.xml', '<?xml version="1.0" ?><coverage lines-valid="40" lines-covered="39" '
                          'branches-valid="0" branches-covered="0" line-rate="0.975"><packages/></coverage>')
        totals = unit_report.read_coverage(path)
        self.assertEqual(totals['branches'], {'covered': 0, 'total': 0})
        block = unit_report.coverage_block(totals, scope='pkg', command='pytest', revision='r', source_artifact='coverage')
        value = self.example('implementacion', 'qa-ranger-unitarias')
        value['data']['coverage'] = block
        self.assertIsNone(self.metrics(value | {'status': 'partial', 'pending': [
            {'description': 'Medir ramas con --cov-branch.', 'owner': 'QA', 'blocksCompletion': True}]})['qa.unitCoverageTargetMet'])

    def test_jacoco_reads_only_report_level_counters(self):
        path = self.write('jacoco.xml', '<?xml version="1.0"?><!DOCTYPE report PUBLIC "-//JACOCO//DTD Report 1.1//EN" "report.dtd">'
                          '<report name="demo"><package name="p"><counter type="LINE" missed="99" covered="1"/></package>'
                          '<counter type="INSTRUCTION" missed="5" covered="95"/><counter type="BRANCH" missed="1" covered="19"/>'
                          '<counter type="LINE" missed="2" covered="38"/><counter type="METHOD" missed="0" covered="12"/></report>')
        self.assertEqual(unit_report.read_coverage(path), {'branches': {'covered': 19, 'total': 20},
                                                           'lines': {'covered': 38, 'total': 40},
                                                           'functions': {'covered': 12, 'total': 12}})

    def test_junit_sums_files_and_classifies_failures_errors_and_skips(self):
        first = self.write('TEST-a.xml', '<testsuite><testcase name="ok"/><testcase name="f"><failure/></testcase>'
                           '<testcase name="e"><error/></testcase></testsuite>')
        second = self.write('TEST-b.xml', '<testsuites><testsuite><testcase name="s"><skipped/></testcase>'
                            '<testcase name="ok2"/></testsuite></testsuites>')
        self.assertEqual(unit_report.read_junit([first, second]), {'passed': 2, 'failed': 2, 'skipped': 1})
        with self.assertRaises(unit_report.ReportError):
            unit_report.read_junit([self.write('otro.xml', '<report/>')])

    def test_cli_output_is_accepted_by_the_contract(self):
        lcov = self.write('lcov.info', LCOV.replace('LH:45', 'LH:58').replace('BRH:12', 'BRH:19'))
        junit = self.write('junit.xml', '<testsuites><testcase name="UT-01"/><testcase name="UT-02"/></testsuites>')
        coverage = self.run_cli('coverage', lcov, '--scope', 'src', '--command', 'node --test', '--revision', 'abc',
                                '--exclude', '*.test.mjs')
        verification = self.run_cli('junit', junit, '--command', 'node --test', '--exit-code', '0')
        self.assertEqual(coverage.returncode, 0, coverage.stdout + coverage.stderr)
        self.assertEqual(verification.returncode, 0, verification.stdout + verification.stderr)
        value = self.example('implementacion', 'qa-ranger-unitarias')
        value['data'].update(coverage=json.loads(coverage.stdout), verification=json.loads(verification.stdout))
        metrics = self.metrics(value)
        self.assertTrue(metrics['qa.unitCoverageTargetMet'])
        self.assertEqual(metrics['qa.testVerification'], 'passed')

    def test_cli_reports_invalid_input_without_inventing_data(self):
        bad = self.write('bad.info', LCOV.replace('LH:45', 'LH:99'))
        run = self.run_cli('coverage', bad, '--scope', 's', '--command', 'c', '--revision', 'r', '--exclude', '*.test.mjs')
        self.assertEqual(run.returncode, 1)
        self.assertFalse(json.loads(run.stdout)['valid'])
        xml = self.write('c.xml', '<coverage lines-valid="1" lines-covered="1"/>')
        run = self.run_cli('coverage', xml, '--scope', 's', '--command', 'c', '--revision', 'r', '--include', '*.py')
        self.assertEqual(run.returncode, 1)

    def test_coverage_rejects_negative_fractional_and_boolean_counts(self):
        for value in (-1, 1.5, True, '1.5'):
            with self.subTest(value=value):
                path = self.write('invalid.json', json.dumps({'total': {'lines': {'covered': value, 'total': 10}}}))
                with self.assertRaises(unit_report.ReportError):
                    unit_report.read_coverage(path)

    def test_lcov_rejects_incomplete_duplicate_and_truncated_records(self):
        for report in (LCOV.replace('LH:45\n', ''), LCOV.replace('LF:58', 'LF:58\nLF:58'),
                       LCOV.removesuffix('end_of_record\n'), LCOV + LCOV,
                       'SF:src/a.js\nend_of_record\n'):
            with self.subTest(report=report):
                with self.assertRaises(unit_report.ReportError):
                    unit_report.read_coverage(self.write('bad.info', report))

    def test_invalid_file_cannot_be_hidden_by_aggregating_istanbul(self):
        path = self.write('bad.json', json.dumps({
            'src/a.js': {'lines': {'covered': 2, 'total': 1}},
            'src/b.js': {'lines': {'covered': 0, 'total': 10}}}))
        with self.assertRaises(unit_report.ReportError):
            unit_report.read_coverage(path, include=['src/*'])

    def test_junit_rejects_duplicate_files_and_contradictory_summaries(self):
        good = self.write('good.xml', '<testsuite tests="1" failures="0"><testcase name="ok"/></testsuite>')
        with self.assertRaises(unit_report.ReportError):
            unit_report.read_junit([good, good])
        for xml in ('<testsuite tests="2"><testcase name="ok"/></testsuite>',
                    '<testsuite errors="1"><testcase name="ok"/></testsuite>',
                    '<testsuite><error message="setup"/><testcase name="ok"/></testsuite>'):
            with self.subTest(xml=xml):
                with self.assertRaises(unit_report.ReportError):
                    unit_report.read_junit([self.write('bad.xml', xml)])

    def test_malformed_istanbul_cli_returns_json_error(self):
        path = self.write('bad.json', '{"total": {"lines": null}}')
        run = self.run_cli('coverage', path, '--scope', 's', '--command', 'c', '--revision', 'r')
        self.assertEqual(run.returncode, 1)
        self.assertFalse(json.loads(run.stdout)['valid'])


if __name__ == '__main__':
    unittest.main()
