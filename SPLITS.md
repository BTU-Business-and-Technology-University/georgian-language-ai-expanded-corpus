> **Independent audit revision 2.0.3-full-checked:** All original data and export behavior are preserved. No reduced training selection is applied. See [current independent findings and limitations](INDEPENDENT_AUDIT_ka.md). Original claims below are not independently verified unless the audit explicitly confirms them.

# Target-head lexical challenge partitions

`export_training.py --split train|validation|test` groups the primary corpus by its target noun lemma. Case, number, adjective, actor and construction changes cannot move the same target head to another split. Linked role tasks and intentionally incorrect case inputs always inherit their positive context's split. Motion-only examples use destination groups instead. No per-record data duplication is added to the corpus.

The deterministic policy is `target-head-v1`. SHA-256 of `target-head-v1|GROUP` selects nominal 90/5/5 hash buckets. These are probabilities over groups; actual record percentages differ because group sizes differ. Measured counts and every group assignment appear in `reports/split_summary.json`.

```bash
python scripts/export_training.py . --mode text --split train --output train.txt.gz
python scripts/export_training.py . --mode text --split validation --output validation.txt.gz
python scripts/export_training.py . --mode role_qa --split test --output role_test.jsonl.gz
python scripts/export_training.py . --mode case_correction --split test --output correction_test.jsonl.gz
```

This is a controlled lexical challenge, not an independent benchmark. Grammar templates, other sentence vocabulary and context words still overlap. The split separates the main target head; it does not assert that every held-out word is absent from every training context. Source statistics and orthographic exercises are not partitioned and may include held-out wordforms; keep them out of a target-lexicon hold-out experiment. All labels still come from the same authored rules. For evidence of general Georgian improvement, use independently authored, human-reviewed evaluation material and an actual model comparison.
