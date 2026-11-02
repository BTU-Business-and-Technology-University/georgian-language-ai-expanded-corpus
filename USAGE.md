> **Independent audit revision 2.0.3-full-checked:** All original data and export behavior are preserved. No reduced training selection is applied. See [current independent findings and limitations](INDEPENDENT_AUDIT_ka.md). Original claims below are not independently verified unless the audit explicitly confirms them.

# Reading the release

Python 3.12 was used for release validation. Install the pinned requirements. Zstandard and gzip shards are streamed; decoding the entire dataset to disk is unnecessary. The full audit also retains uniqueness/reference sets in memory and therefore needs more memory than export.

```bash
python -m pip install -r requirements.txt
python scripts/verify_distribution.py .
python scripts/test_release_checks.py .
python scripts/export_training.py . --mode text --output text_preview.txt --limit 1000
python scripts/export_training.py . --mode role_qa --split test --output qa_preview.jsonl --limit 1000
python scripts/export_training.py . --mode case_correction --split test --output correction_preview.jsonl --limit 1000
```

Text mode exports positive primary text only. It never adds deliberately incorrect inputs, role questions, aggregate statistics or documentation. Task modes join every `context_id` to its positive record. Role answers are literal Georgian spans, preserving the case in the context. Correction inputs are intentionally wrong; the assistant target is the positive text. Empty previews are supported with `--limit 0`. Negative limits are rejected. Existing output files are never overwritten, including with optimized Python.

```python
from pathlib import Path
import json
from scripts.io_utils import open_text
root = Path('.')
manifest = json.loads((root / 'data_manifest.json').read_text(encoding='utf-8'))
part = manifest['layers']['corpus']['shards'][0]
with open_text(root / part['path']) as stream:
    row = json.loads(next(stream))
    print(row['text_ka'], row['origin'])
```

See [SPLITS.md](SPLITS.md) for group assignments and limitations. Preview files in `examples/` copy real release records or derived tasks and are excluded from the headline count.
