> **Independent audit revision 2.0.3-full-checked:** All original data and export behavior are preserved. No reduced training selection is applied. See [current independent findings and limitations](INDEPENDENT_AUDIT_ka.md). Original claims below are not independently verified unless the audit explicitly confirms them.

# BTU Georgian Language AI Expanded Corpus

Version 2.0.1 · Business and Technology University · 26 October 2026

**150,080,748 Georgian lexical token occurrences** in 6,056,086 controlled synthetic examples. The headline counts Georgian words in distinct normalized primary sentences or dialogue utterances, using `o200k_base`. IDs, JSON syntax, annotations, repeated role strings, task prompts, auxiliary statistics and documentation are excluded.

The primary corpus is rule-based synthetic language material. An authentic-source aggregate component and separate derived exercises accompany it. The resource supports targeted experiments in case, agreement, person, tense, negation, modality, temporal reference and coreference. It is a computed research candidate, with no external gold annotation or measured model-quality gain.

ქართული აღწერა: [README_ka.md](README_ka.md).

| Component | Records |
| --- | ---: |
| `corpus` | 6,056,086 |
| `role_tasks` | 1,730,310 |
| `case_corrections` | 42,368 |
| `source_statistics/wordforms` | 128,182 |
| `source_statistics/adjacent_pairs` | 261,931 |
| `source_statistics/context_pairs` | 1,264,393 |
| `source_statistics/character_fragments` | 19,781 |
| `source_statistics/affix_statistics` | 6,322 |
| `orthography_tasks` | 180,627 |

## Read and export

```bash
python -m pip install -r requirements.txt
python scripts/export_training.py . --mode text --output preview.txt --limit 1000
python scripts/export_training.py . --mode role_qa --output qa.jsonl --limit 1000
python scripts/export_training.py . --mode case_correction --output corrections.jsonl --limit 1000
python scripts/audit_release.py .
python scripts/audit_support.py .
```

Primary and linked grammar tasks are UTF-8 JSONL compressed with Zstandard. Aggregate and orthographic shards use gzip. `scripts/io_utils.py` reads both. Deliberately wrong correction inputs are kept separate from positive language text. The default text exporter reads only the positive primary corpus.

## Origin and scope

Palitra Group is a project partner and supplied Georgian-language material to BTU. Authentic-source data is distributed as pooled linguistic statistics, without raw books, pages or document-level mappings. Synthetic scenarios use generic human roles and do not describe real events.

The synthetic seed lexicon is compact: 54 human-role lemmas, 167 noun lemmas and 50 active verb paradigms. Scale comes from typed lexical, grammatical and contextual combinations. The statistical component supplies a broader observed wordform inventory. Family IDs combine feature settings; they are not independently discovered or externally validated grammar rules.

Every primary sentence or dialogue utterance is unique after Georgian-word normalization. A controlled lexical-core key is used at most once. These properties do not establish statistical independence, broad free-form language coverage or a proportional increase in linguistic information. Evaluate downstream utility separately.

## Checks and limitations

The complete primary corpus was re-tokenized and checked against registered paradigms, role surfaces, case, agreement, uniqueness, transport hashes and an eight-word overlap filter over the processed private corpus. Auxiliary answers were checked computationally. Public audits can run without private sources; repeating the source-overlap check requires the authorized private index. Reports are in [reports](reports).

Five oversized source ZIPs were unavailable, so complete source-folder coverage is not claimed. Selected known literary and personal names were suppressed from aggregates. This is not a formal anonymity or copyright-clearance proof. External linguistic review, peer review and model-utility testing have not been completed.

See [METHOD.md](METHOD.md), [DATA_CARD.md](DATA_CARD.md), [USAGE.md](USAGE.md) and [dataset_summary.json](dataset_summary.json). Licence: CC BY-NC 4.0 for rights BTU can license; commercial use requires separate permission.

## Pre-publication revision 2.0.1

All 1,730,310 role-extraction prompts now use neutral span extraction, including negative, past and future statements. Answers, IDs, context links and every positive primary shard are unchanged. Added target-head challenge splits, stricter audits, 13 adversarial/functional regression checks, complete layer schemas and a fast distribution verifier. Detailed findings are in [PUBLICATION_QA_ka.md](PUBLICATION_QA_ka.md).

```bash
python scripts/verify_distribution.py .
python scripts/test_release_checks.py .
python scripts/export_training.py . --mode text --split train --output train_preview.txt --limit 1000
```

Use [SPLITS.md](SPLITS.md) before training/evaluation. This is a controlled augmentation resource with a compact seed lexicon; combining more generated permutations does not supply the same diversity as equally large independently written prose. Package hashes prove file integrity, not linguistic perfection or downstream quality gain.
