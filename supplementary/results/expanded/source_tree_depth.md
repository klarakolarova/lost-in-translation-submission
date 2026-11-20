# Association between French and German sentence depth

This exploratory comparison uses 598 French sources and their two German versions to assess how closely sentence depth varies with the source. German measurements are reused from the complexity analysis.

French: fr_core_news_sm 3.8.0 (UD Sequoia). German: de_core_news_sm 3.8.0 (TIGER/Tiger2Dep). Different annotation schemes prevent interpreting raw cross-language depth gaps as structural preservation.

## Results

Pearson’s r measures how closely depth varies across documents: a higher positive value indicates a stronger association. The difference is the machine correlation minus the official correlation.

| Comparison | French–official correlation | French–machine correlation | Difference [95% confidence interval] |
|---|---:|---:|---|
| Unadjusted sentence depth | 0.500 | 0.659 | +0.159 [+0.103, +0.216] |
| Sentence depth adjusted for length | 0.143 | 0.400 | +0.257 [+0.080, +0.424] |

## Method and interpretation

Depth is the maximum word depth in each sentence, averaged within each text. This tests an association with the source, rather than directly comparing French and German depth levels.

- Correlations describe document-level covariation, not sentence-aligned syntactic equivalence or causality.
- Length adjustment removes a fitted linear association with mean sentence length separately in each version; it does not remove every confound.
- Exploratory intervals resample paired documents within year; repeated authors and multiple comparisons are not accounted for.
