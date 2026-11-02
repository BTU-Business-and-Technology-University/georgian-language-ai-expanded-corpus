#!/usr/bin/env python3
"""Stream positive text or linked tasks; optionally select target-head splits."""
import argparse
import gzip
import json
from pathlib import Path
from io_utils import open_text
from split_policy import SPLITS, row_split


def rows(root, spec):
    for shard in spec['shards']:
        with open_text(root / shard['path']) as stream:
            for line in stream:
                yield json.loads(line)


def examples(root, manifest, mode, split='all'):
    corpus = rows(root, manifest['layers']['corpus'])
    if mode == 'text':
        for row in corpus:
            if split == 'all' or row_split(row) == split:
                yield row['text_ka'] + '\n\n'
        return
    layer = 'role_tasks' if mode == 'role_qa' else 'case_corrections'
    current = next(corpus, None)
    previous_context = ''
    for task in rows(root, manifest['layers'][layer]):
        context_id = task['context_id']
        if context_id < previous_context:
            raise ValueError('Tasks must be ordered by context_id')
        previous_context = context_id
        while current is not None and current['id'] < context_id:
            current = next(corpus, None)
        if current is None or current['id'] != context_id:
            raise ValueError('Missing positive context: ' + context_id)
        if split != 'all' and row_split(current) != split:
            continue
        if mode == 'role_qa':
            prompt = current['text_ka'] + '\n\n' + task['question_ka']
            answer = task['answer_ka']
        else:
            if task['include_in_plain_language_training'] is not False:
                raise ValueError('Correction input lacks its negative-example marker')
            prompt = task['question_ka'] + '\n' + task['incorrect_text_ka']
            answer = current['text_ka']
        yield json.dumps({'messages': [
            {'role': 'user', 'content': prompt},
            {'role': 'assistant', 'content': answer},
        ]}, ensure_ascii=False) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--mode', choices=('text', 'role_qa', 'case_correction'), default='text')
    parser.add_argument('--split', choices=('all',) + SPLITS, default='all')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.limit is not None and args.limit < 0:
        parser.error('--limit must be zero or greater')
    manifest = json.loads((args.root / 'data_manifest.json').read_text(encoding='utf-8'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if args.output.suffix == '.gz' else open
    created = False
    written = 0
    try:
        with opener(args.output, 'xt', encoding='utf-8') as output:
            created = True
            if args.limit != 0:
                for example in examples(args.root, manifest, args.mode, args.split):
                    output.write(example)
                    written += 1
                    if args.limit is not None and written >= args.limit:
                        break
    except BaseException:
        if created:
            args.output.unlink(missing_ok=True)
        raise
    print(json.dumps({'records_exported': written, 'mode': args.mode, 'split': args.split}))


if __name__ == '__main__':
    main()
