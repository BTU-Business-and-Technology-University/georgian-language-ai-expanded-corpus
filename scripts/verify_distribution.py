#!/usr/bin/env python3
"""Fast, read-only integrity check for the complete extracted release."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(root):
    root = root.resolve()
    checks = {}
    for line in (root / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, rel = line.split('  ', 1)
        path = root / rel
        require(path.resolve().is_relative_to(root), 'Unsafe checksum path: ' + rel)
        require(rel not in checks, 'Repeated checksum path: ' + rel)
        require(re.fullmatch('[0-9a-f]{64}', digest) is not None, 'Invalid checksum: ' + rel)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'Checksum mismatch: ' + rel)
        checks[rel] = digest
    manifest = json.loads((root / 'data_manifest.json').read_text(encoding='utf-8'))
    summary = json.loads((root / 'dataset_summary.json').read_text(encoding='utf-8'))
    declared = set()
    data_bytes = records = shards = 0
    for name, layer in manifest['layers'].items():
        require(layer['records'] == sum(s['records'] for s in layer['shards']), 'Layer count mismatch: ' + name)
        records += layer['records']
        for shard in layer['shards']:
            rel = shard['path']; path = root / rel
            require(rel.startswith('data/') and path.resolve().is_relative_to(root), 'Unsafe data path: ' + rel)
            require(rel not in declared, 'Repeated data path: ' + rel)
            require(checks.get(rel) == shard['sha256'], 'Manifest hash mismatch: ' + rel)
            require(path.stat().st_size == shard['bytes'], 'Manifest size mismatch: ' + rel)
            require(0 < shard['bytes'] < 25 * 1024**2, 'Shard exceeds browser upload size: ' + rel)
            declared.add(rel); data_bytes += shard['bytes']; shards += 1
    actual = {p.relative_to(root).as_posix() for p in (root / 'data').rglob('*') if p.is_file()}
    require(actual == declared, 'Missing or undeclared data files')
    require(records == summary['all_component_records'], 'Summary record count mismatch')
    require(shards == summary['data_shards'], 'Summary shard count mismatch')
    require(data_bytes == summary['compressed_data_bytes'], 'Summary size mismatch')
    for path in (root / 'scripts').glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    generation = json.loads((root / 'generation_report.json').read_text(encoding='utf-8'))
    require(generation['version'] == summary['version'], 'Version mismatch')
    require(generation['canonical_records'] == summary['primary_synthetic_records'], 'Primary count mismatch')
    require(generation['primary_georgian_lexical_tokens'] == summary['primary_georgian_lexical_token_occurrences'], 'Token summary mismatch')
    return {'status': 'PASS', 'version': summary['version'], 'files_sha256_verified': len(checks),
            'data_shards': shards, 'component_records': records, 'compressed_data_bytes': data_bytes,
            'scope': 'Distribution hashes, manifest consistency and syntax only. Legacy PASS reports are not treated as independent proof. No model or human-linguist evaluation.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.root), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
