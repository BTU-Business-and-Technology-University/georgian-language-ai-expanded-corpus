#!/usr/bin/env python3
"""Regression checks using a small fixture read from the delivered data."""
import collections
import contextlib
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from audit_release import audit, normalized
from export_training import examples, rows
from generate_corpus import tasks_for
from lexicon import ACTORS
from split_policy import row_split, target_group

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]


STRUCTURAL_ONLY = '--structural-only' in sys.argv

class ReleaseChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ROOT / 'data_manifest.json').read_text(encoding='utf-8'))
        from itertools import islice
        cls.positive = list(islice(rows(ROOT, manifest['layers']['corpus']), 1000))
        cls.qa = []
        cls.corrections = []
        nom = {a.erg: a.nom for a in ACTORS}
        nom.update({a.plural_erg: a.plural for a in ACTORS})
        for index, row in enumerate(cls.positive, 1):
            if index % 7 == 0:
                for task in tasks_for(row):
                    cls.qa.append({'id': f'qa{len(cls.qa)+1:08}', **task, 'origin': 'derived_from_synthetic'})
            if index % 13 == 0 and row['construction'] == 'active' and row['features']['tense'] == 'past':
                agent = row['roles']['agent']
                cls.corrections.append({'id': f'fix{len(cls.corrections)+1:07}', 'context_id': row['id'],
                    'task': 'correct_agent_case', 'question_ka': 'გაასწორე მოქმედი პირის ბრუნვა.',
                    'incorrect_text_ka': row['text_ka'].replace(agent, nom[agent], 1),
                    'correct_agent_ka': agent, 'origin': 'deliberate_negative_from_synthetic',
                    'include_in_plain_language_training': False})
        if not cls.corrections:
            raise RuntimeError('Regression fixture lacks a case-correction example')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.material = {'corpus': copy.deepcopy(self.positive), 'role_tasks': copy.deepcopy(self.qa),
                         'case_corrections': copy.deepcopy(self.corrections)}
        self.write_fixture()

    def write_fixture(self):
        manifest = {'layers': {}}
        for layer, material in self.material.items():
            raw = ''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n' for row in material).encode()
            data = gzip.compress(raw, mtime=0)
            rel = f'data/{layer}/part-00001.jsonl.gz'
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            manifest['layers'][layer] = {'records': len(material), 'shards': [{'path': rel,
                'records': len(material), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                'uncompressed_sha256': hashlib.sha256(raw).hexdigest()}]}
        summary = {'canonical_records': len(self.positive),
            'primary_georgian_lexical_tokens': sum(r['lexical_tokens'] for r in self.positive),
            'target_primary_georgian_lexical_tokens': 1,
            'full_primary_text_tokens': sum(r['text_tokens'] for r in self.positive),
            'georgian_word_occurrences': sum(len(normalized(r['text_ka']).split()) for r in self.positive),
            'construction_counts': dict(collections.Counter(r['construction'] for r in self.positive)),
            'role_task_records': len(self.qa), 'intentional_error_correction_records': len(self.corrections)}
        (self.root / 'data_manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        (self.root / 'generation_report.json').write_text(json.dumps(summary), encoding='utf-8')
        self.manifest = manifest

    def run_audit(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return audit(self.root,recount_tokens=not STRUCTURAL_ONLY)[0]

    def test_valid_fixture_and_split_coverage(self):
        result = self.run_audit()
        self.assertEqual(result['status'], 'PASS_STRUCTURAL_TOKEN_RECOUNT_SKIPPED' if STRUCTURAL_ONLY else 'PASS')
        self.assertEqual(sum(result['split_primary_records'].values()), 1000)
        self.assertEqual(result['target_groups_shared_between_splits'], 0)

    def test_incorrect_answer_is_rejected(self):
        self.material['role_tasks'][0]['answer_ka'] = 'უცნობი'
        self.write_fixture()
        with self.assertRaises(AssertionError): self.run_audit()

    def test_presupposing_question_is_rejected(self):
        self.material['role_tasks'][0]['question_ka'] = 'დაასახელე საგანი, რომელიც მოცემულ პირს აქვს.'
        self.write_fixture()
        with self.assertRaises(AssertionError): self.run_audit()

    def test_extra_provenance_field_is_rejected(self):
        self.material['corpus'][0]['source_document_id'] = 'not-permitted'
        self.write_fixture()
        with self.assertRaises(AssertionError): self.run_audit()

    def test_repeated_sentence_is_rejected(self):
        self.material['corpus'][1]['text_ka'] = self.material['corpus'][0]['text_ka']
        self.write_fixture()
        with self.assertRaises(AssertionError): self.run_audit()

    @unittest.skipIf(STRUCTURAL_ONLY, 'Requires real tokenizer; never substitute stored counts')
    def test_incorrect_token_count_is_rejected(self):
        self.material['corpus'][0]['lexical_tokens'] += 1
        self.write_fixture()
        with self.assertRaises(AssertionError): self.run_audit()

    def test_correction_may_change_only_actor_case(self):
        task = self.material['case_corrections'][0]
        task['incorrect_text_ka'] = 'უცნობი ' + task['incorrect_text_ka'].split(' ', 1)[1]
        self.write_fixture()
        with self.assertRaises(AssertionError): self.run_audit()

    def test_manifest_layer_count_is_checked(self):
        self.manifest['layers']['corpus']['records'] += 1
        (self.root / 'data_manifest.json').write_text(json.dumps(self.manifest), encoding='utf-8')
        with self.assertRaises(AssertionError): self.run_audit()

    def test_transport_corruption_is_rejected(self):
        path = self.root / self.manifest['layers']['corpus']['shards'][0]['path']
        data = bytearray(path.read_bytes()); data[-1] ^= 1; path.write_bytes(data)
        with self.assertRaises(AssertionError): self.run_audit()

    def test_target_head_groups_inflections_and_constructions(self):
        a = {'id': 'a', 'construction': 'active', 'roles': {'patient': 'ახალ წიგნს'}}
        b = {'id': 'b', 'construction': 'genitive', 'roles': {'possessor': 'მასწავლებლის',
             'located': 'მასწავლებლის ძველი წიგნები'}}
        self.assertEqual(target_group(a), 'noun:წიგნი')
        self.assertEqual(target_group(a), target_group(b))
        self.assertEqual(row_split(a), row_split(b))

    def test_export_split_and_negative_layer_isolation(self):
        contexts = {r['text_ka']: r for r in self.positive}
        for split in ('train', 'validation', 'test'):
            texts = list(examples(self.root, self.manifest, 'text', split))
            self.assertTrue(texts)
            for value in texts: self.assertEqual(row_split(contexts[value.strip()]), split)
            for value in examples(self.root, self.manifest, 'role_qa', split):
                row = json.loads(value)
                context = row['messages'][0]['content'].rsplit('\n\n', 1)[0]
                self.assertEqual(row_split(contexts[context]), split)
            for value in examples(self.root, self.manifest, 'case_correction', split):
                row = json.loads(value)
                self.assertEqual(row_split(contexts[row['messages'][1]['content']]), split)
        positives = {x.strip() for x in examples(self.root, self.manifest, 'text')}
        self.assertTrue(all(t['incorrect_text_ka'] not in positives for t in self.corrections))

    def test_audit_refuses_optimized_python(self):
        command = [sys.executable, '-O', str(ROOT / 'scripts/audit_release.py'), str(self.root)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('without -O', result.stderr)

    def test_export_zero_limit_and_no_overwrite_under_optimization(self):
        output = self.root / 'empty.txt'
        command = [sys.executable, '-O', str(ROOT / 'scripts/export_training.py'), str(self.root),
                   '--mode', 'role_qa', '--output', str(output), '--limit', '0']
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), b'')
        output.write_bytes(b'preserve-me\n')
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), b'preserve-me\n')


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]], verbosity=2)
