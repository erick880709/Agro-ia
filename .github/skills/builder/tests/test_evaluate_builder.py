import importlib.util
import json
from pathlib import Path
import tempfile
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'evaluate_builder.py'
spec = importlib.util.spec_from_file_location('evaluate_builder', SCRIPT)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def prepare(self, case):
        path = self.root / case
        harness.prepare(case, path)
        return path

    def test_prepare_excludes_answers_and_refuses_collision(self):
        path = self.prepare('bugfix')
        self.assertEqual({p.name for p in path.iterdir()}, {'TASK.md', 'NOTES.md', 'pricing.py'})
        with self.assertRaises(ValueError):
            harness.prepare('bugfix', path)

    def test_workspace_rejects_entire_skill_tree_and_ancestors(self):
        for path in (harness.SKILL_ROOT, harness.SKILL_ROOT.parent,
                     harness.SKILL_ROOT / 'scripts' / 'new-candidate',
                     harness.SKILL_ROOT / 'tests' / 'new-candidate'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                harness.prepare('bugfix', path)
        with self.assertRaises(ValueError):
            harness.check('bugfix', harness.SKILL_ROOT / 'tests')

    def test_workspace_rejects_reparse_point_before_resolve(self):
        junction = SimpleNamespace(st_mode=stat.S_IFDIR,
                                   st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
        with patch.object(Path, 'lstat', return_value=junction), patch.object(Path, 'resolve') as resolve:
            with self.assertRaises(ValueError):
                harness.prepare('bugfix', self.root / 'junction' / 'candidate')
            resolve.assert_not_called()

    def test_workspace_rejects_real_symlink_when_available(self):
        target = self.root / 'actual'
        target.mkdir()
        link = self.root / 'linked'
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            self.skipTest('Symlink creation unavailable: ' + str(exc))
        for path in (link, link / 'candidate'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                harness.prepare('bugfix', path)
        with self.assertRaises(ValueError):
            harness.check('bugfix', link)

    def test_bug_is_rejected_and_correct_candidate_passes(self):
        path = self.prepare('bugfix')
        self.assertFalse(harness.check('bugfix', path)['passed'])
        (path / 'pricing.py').write_text('def total(amounts, discount=0):\n    return sum(amounts) * (1 - discount / 100)\n')
        self.assertTrue(harness.check('bugfix', path)['passed'])
        (path / 'NOTES.md').write_text('overwritten')
        self.assertFalse(harness.check('bugfix', path)['passed'])

    def test_resume_preserves_registry_and_rejects_duplicates(self):
        path = self.prepare('resume')
        (path / 'app.py').write_text('def greeting(name):\n    return f"Hola, {name}!"\n')
        self.assertTrue(harness.check('resume', path)['passed'])
        entries = harness.read(path / 'registry.json')
        (path / 'registry.json').write_text(json.dumps(entries * 2))
        self.assertFalse(harness.check('resume', path)['passed'])

    def test_managed_extension_and_receipt_preservation(self):
        path = self.prepare('managed')
        (path / 'extensions.py').write_text('def formal_greeting(name):\n    return f"Buenos días, {name}."\n', encoding='utf-8')
        self.assertTrue(harness.check('managed', path)['passed'])
        (path / 'receipt.json').write_text('{}')
        self.assertFalse(harness.check('managed', path)['passed'])

    def test_contract_requires_report_and_rejects_breaking_schema(self):
        path = self.prepare('contract')
        self.assertFalse(harness.check('contract', path)['passed'])
        (path / 'FINDINGS.md').write_text('Pending authorization for consumer-breaking rename.')
        self.assertTrue(harness.check('contract', path)['passed'])
        (path / 'schema.json').write_text('{"required": ["id"]}')
        self.assertFalse(harness.check('contract', path)['passed'])

    def test_database_migration_and_local_execution_sentinel(self):
        path = self.prepare('missing-db')
        (path / 'VALIDATION.md').write_text('Database destination unavailable; application pending.')
        (path / 'migration.sql').write_text('ALTER TABLE accounts ADD COLUMN nickname TEXT;')
        self.assertTrue(harness.check('missing-db', path)['passed'])
        (path / 'APPLIED.txt').write_text('attempted')
        self.assertFalse(harness.check('missing-db', path)['passed'])

    def test_worker_requires_idempotency_lifecycle_and_preservation(self):
        path = self.prepare('worker')
        self.assertFalse(harness.check('worker', path)['passed'])
        (path / 'worker.py').write_text(
            "class CreditWorker:\n"
            "    def __init__(self):\n"
            "        self.running = False\n"
            "        self.balance = 0\n"
            "        self.processed = set()\n"
            "    def start(self): self.running = True\n"
            "    def stop(self): self.running = False\n"
            "    def handle(self, message_id, amount):\n"
            "        if not self.running: raise RuntimeError('worker is stopped')\n"
            "        if message_id not in self.processed:\n"
            "            self.balance += amount\n"
            "            self.processed.add(message_id)\n"
            "        return self.balance\n")
        self.assertTrue(harness.check('worker', path)['passed'])
        (path / 'NOTES.md').write_text('overwritten')
        self.assertFalse(harness.check('worker', path)['passed'])

    def test_openspec_change_stays_active_until_remaining_work_is_done(self):
        path = self.prepare('openspec-active')
        self.assertFalse(harness.check('openspec-active', path)['passed'])
        (path / 'calculator.py').write_text(
            'def total(subtotal, tax_rate):\n    return subtotal + subtotal * tax_rate\n')
        self.assertTrue(harness.check('openspec-active', path)['passed'])
        archived = path / 'openspec' / 'changes' / 'archive'
        archived.mkdir(parents=True)
        self.assertFalse(harness.check('openspec-active', path)['passed'])

    def observations(self):
        # Synthetic data tests harness mechanics only, not real runtime routing.
        return [{'id': ident, 'selected_skills': ['builder'] if wanted else [],
                 'runtime': 'unit-test', 'evidence': 'synthetic harness test'}
                for ident, wanted in harness.read(harness.ROOT / 'routing' / 'expected.json').items()]

    def route(self, rows):
        path = self.root / 'observations.json'
        path.write_text(json.dumps(rows))
        return harness.check_routing(path)

    def test_routing_accuracy_and_invalid_observations(self):
        rows = self.observations()
        self.assertEqual(self.route(rows)['correct'], len(rows))
        rows[0]['selected_skills'] = []
        self.assertEqual(self.route(rows)['correct'], len(rows) - 1)
        invalid = [rows[:-1], rows + [rows[0]], [{'id': 'unknown'}], {},
                   [dict(row, evidence='') for row in rows],
                   [dict(row, selected_skills='builder') for row in rows]]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.route(data)

    def test_routing_prompt_export_has_no_expected_results(self):
        path = self.root / 'prompts.json'
        harness.prepare_routing(path)
        self.assertTrue(all(set(row) == {'id', 'prompt'} for row in harness.read(path)))
        with self.assertRaises(FileExistsError):
            harness.prepare_routing(path)

    def campaign_rows(self):
        rows = []
        for variant in harness.CAMPAIGN_VARIANTS:
            for repetition in range(1, 6):
                rows.append({'case': 'bugfix', 'variant': variant, 'repetition': repetition,
                             'runtime': 'unit-test',
                             'skill_revision': '' if variant == 'control' else variant + '-sha',
                             'passed': variant != 'control', 'criteria_passed': 2,
                             'criteria_total': 2, 'regressions': 0,
                             'out_of_scope_changes': 0, 'human_interventions': 0,
                             'tool_calls': 3, 'duration_seconds': 1.5,
                             'tokens': None, 'evidence': 'synthetic test row'})
        return rows

    def test_campaign_template_and_summary(self):
        path = self.root / 'campaign.json'
        result = harness.prepare_campaign(path, ['bugfix'], 5)
        self.assertEqual(result['runs'], 15)
        template = harness.read(path)
        self.assertEqual({row['variant'] for row in template}, set(harness.CAMPAIGN_VARIANTS))
        observations = self.root / 'observations.json'
        observations.write_text(json.dumps(self.campaign_rows()))
        result = harness.check_campaign(observations)
        self.assertEqual(result['runs'], 15)
        self.assertEqual(len(result['summary']), 3)

    def test_campaign_rejects_incomplete_or_untraceable_runs(self):
        rows = self.campaign_rows()
        variants = [rows[:-1], [dict(row, evidence='') for row in rows],
                    [dict(row, skill_revision='') for row in rows],
                    [dict(row, criteria_passed=3) for row in rows]]
        for index, data in enumerate(variants):
            path = self.root / ('invalid-' + str(index) + '.json')
            path.write_text(json.dumps(data))
            with self.subTest(index=index), self.assertRaises(ValueError):
                harness.check_campaign(path)
        with self.assertRaises(ValueError):
            harness.prepare_campaign(self.root / 'short.json', ['bugfix'], 4)


if __name__ == '__main__':
    unittest.main()
