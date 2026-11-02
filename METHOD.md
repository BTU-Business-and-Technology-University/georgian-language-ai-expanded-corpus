> **Independent audit revision 2.0.3-full-checked:** All original data and export behavior are preserved. No reduced training selection is applied. See [current independent findings and limitations](INDEPENDENT_AUDIT_ka.md). Original claims below are not independently verified unless the audit explicitly confirms them.

# Method and measurement

The authorized source processing retained 70,312,697 Georgian word occurrences in 302,499 processing documents. Only pooled features are distributed. Original document inventories, authors, page positions and source-to-feature mappings are excluded. The aggregate thresholds were twenty document supports and three collections, with a three-occurrence contribution cap. Selected synthetic predicate/noun slots have separately reported cooccurrence support at five documents and two collections; authored compatibility is explicit for fallback slots.

Authored paradigms supply nominative, ergative and dative actor forms, singular/plural noun forms, adjective variants, registered verbs and typed contexts. Separate rules cover active agreement, inanimate passive agreement, dative experience/possession, modal complements, motion, relative clauses, temporal coreference and conditional futures. General feature conventions follow [UD Georgian](https://universaldependencies.org/ka/index.html) and its [case documentation](https://universaldependencies.org/ka/feat/Case.html). Release annotations are authored rule outputs, not UD gold labels.

Repeated lexical-core keys and repeated normalized sentences or utterances are rejected. A core key includes construction and lexical/grammatical choices. The normalized unit is a Georgian word sequence between full stops or question boundaries; it is not a complete syntactic-clause analysis. A conditional curriculum block and fixed seeds appear in [the build recipe](reports/build_recipe.json).

A private Bloom membership index contains normalized eight-word windows from the processed source corpus. Every accepted candidate was checked, and the final corpus was rescanned. Positive Bloom matches are conservatively rejected. The scope is exact windows from the processed input, not every external publication or paraphrase. The index is not distributed. Repeating the test requires authorized private inputs.

## Token measurement

tiktoken 0.14.0 with `o200k_base` counts Georgian words after punctuation removal and sentence/utterance deduplication. The headline is **150,080,748 token occurrences**, not distinct vocabulary token types. The displayed positive text with punctuation contains 158,055,340 tokens. The smaller lexical-only count is used publicly. IDs, role annotations, prompts, answers, negative examples, source statistics and documentation are excluded.

The previous supplied structured core measures 3,906,838 primary Georgian tokens or 10,578,193 tokens across selected linguistic values including translations, using the same encoding. Its earlier public estimate was 15 million. The new primary lexical payload is 10.01 times that estimate. This compares sizes of different resource types, without a model-quality or information multiplier.

## Transport and reproducibility

Zstandard 0.25.0 uses frame checksums. Repacked shards were decoded and uncompressed SHA-256 checked; the final audit then verified decoded content, token counts, registered forms, uniqueness and overlap. The manifest records compressed and uncompressed hashes. IDs and core hashes identify synthetic examples, not original documents.

Use Python 3.12 and the pinned requirements. Generation additionally uses the supplied C++17/zlib overlap guard on Linux and authorized private normalized input. Keep source text, work directories and indexes outside the public repository. The build recipe records seeds and synthetic enrichment ranges. The private known-name suppression configuration is withheld. Exact regeneration requires the same private normalized input and versions.

## Pre-publication corrections in 2.0.1

The positive corpus is byte-for-byte identical to 2.0.0 across all 243 compressed shards. Role-task questions were regenerated with a neutral span-extraction policy. All 1,730,310 questions changed; their answers, context references and IDs did not. The final audit checks every task payload against its linked positive record, and every deliberately incorrect correction against the single permitted actor-case mutation. Audits refuse optimized Python rather than silently bypassing assertion checks. Export overwrite protection uses exclusive file creation and remains active under optimization.

The source guard was independently rebuilt from supplied C++ code and tested with 100 known source windows and 100 accepted synthetic examples before the full rescan. None of those private source excerpts is distributed. This checks operation of the configured guard; it is not a formal reidentification proof.

[Target-head partitions](SPLITS.md) are deterministic lexical challenge groups, with actual split sizes reported after the full scan. They do not partition every vocabulary item or independent grammar templates. No new expert or trained-model certification is implied.
