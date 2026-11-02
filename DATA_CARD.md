> **Independent audit revision 2.0.3-full-checked:** All original data and export behavior are preserved. No reduced training selection is applied. See [current independent findings and limitations](INDEPENDENT_AUDIT_ka.md). Original claims below are not independently verified unless the audit explicitly confirms them.

# Data card

Institution: Business and Technology University, Georgia. Partner: Palitra Group. Version: 2.0.1. Date: 2026-10-26. Language: Georgian. Licence: CC BY-NC 4.0 for rights BTU can license.

Primary material: 6,056,086 controlled synthetic records and 150,080,748 lexical token occurrences. Scale comes from typed combinations, not an equally large new extraction of authentic prose. Source aggregate data and derived exercises are separately labeled.

Intended uses include targeted case/agreement augmentation, role extraction, temporal/coreference practice and character handling. The compact seed lexicon and formal or neutral style constrain coverage. The corpus is not representative of Georgian population language use or unrestricted literary/conversational prose.

Every positive record passed registered-paradigm consistency, normalized uniqueness, source-window and transport checks. These checks do not prove expert linguistic correctness or downstream model improvement. Independent human-linguist review, external peer review, a gold benchmark and model-utility testing are not claimed.

Deliberately wrong case forms occur only in the marked correction layer, with positive linked targets. Orthographic targets are computed string transformations and do not certify normative spelling of every observed source wordform. Source aggregates may retain errors or common proper names; selected known names were suppressed.

Raw source pages, individual bibliographic mappings and the private source index are absent. This is not differential privacy or complete non-reidentification. Five source archives were unavailable. Default text export includes only positive synthetic text. Evaluate components separately and document mixing or further filtering.

Revision 2.0.1 preserves every positive primary byte and changes only linked role-task question wording in the data payload. Neutral prompts avoid factual presuppositions in negated or non-present examples. A deterministic target-head partition is available for corpus and linked tasks. It is a lexical challenge split with shared templates/context vocabulary, not a gold evaluation set; source aggregate and orthography layers have no split assignment. See SPLITS.md and the publication QA report.
