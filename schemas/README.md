# Layer schemas

| Manifest layer | JSON Schema |
| --- | --- |
| `corpus` | `primary_record.schema.json` |
| `role_tasks` | `role_task.schema.json` |
| `case_corrections` | `case_correction.schema.json` |
| `orthography_tasks` | `orthography_task.schema.json` |
| `source_statistics/wordforms` | `wordform.schema.json` |
| `source_statistics/adjacent_pairs` | `adjacent_pair.schema.json` |
| `source_statistics/context_pairs` | `context_pair.schema.json` |
| `source_statistics/character_fragments` | `character_fragment.schema.json` |
| `source_statistics/affix_statistics` | `affix_statistic.schema.json` |

Schemas forbid unexpected fields. The streaming audits additionally check registered paradigms, token totals, uniqueness, context joins, exact task payloads, permitted correction mutations, split groups and frequency-band relations. `source` in a motion role means a departure location; it is not a source-document identifier. Example IDs and hashes identify synthetic data, not individual books.
