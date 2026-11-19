# Exploratory source–target syntax associations

259 completed triples. Existing German depth/length results reproduced exactly (numeric tolerance).

French: fr_core_news_sm 3.8.0 (UD Sequoia). German: de_core_news_sm 3.8.0 (TIGER/Tiger2Dep). Different annotation schemes prevent interpreting raw cross-language depth gaps as structural preservation.

| Measure | Source–official r | Source–model r | Difference [95% exploratory CI] |
|---|---:|---:|---|
| mean_sentence_tree_depth (raw) | 0.529 | 0.694 | +0.165 [+0.086, +0.251] |
| mean_sentence_tree_depth (length_adjusted) | 0.264 | 0.435 | +0.171 [+0.039, +0.300] |

## Interpretation limits

- Correlations describe document-level covariation, not sentence-aligned syntactic equivalence or causality.
- Length adjustment removes a fitted linear association with mean sentence length separately in each version; it does not remove every confound.
- Exploratory intervals resample paired documents within year; repeated authors and multiple comparisons are not accounted for.
