# Additional robustness analysis

This supplement checks whether the report's findings recur in additional translations, using the same model settings and measurement functions. The report and its reproduction workflow use the original 259 completed pairs.

## Samples

| Sample | Pairs | Per year, 2000–2025 | Relationship to the report |
|---|---:|---:|---|
| Report | 259 | 10 selected; one generation failed | Original analysis |
| Expanded | 598 | 23 | All 259 report pairs plus 339 new pairs |
| New only | 338 | 13 | No overlap with the report; subset of the expanded sample |

The smallest eligible yearly pool, 2002, contains 23 motions after excluding development documents. This sets the maximum equally sized sample across years. Two additional random batches produced 508 translations. We selected additions from these completed batches using seed 51, before inspecting their linguistic scores, and selected the balanced new-only subset using seed 52. The saved design records every selected ID. One additional translation from 2000 is in the expanded sample but not the new-only subset.

The new-only comparison is especially useful: it checks whether the patterns recur beyond the observations already analysed in the report.

## Findings

Differences below are machine minus official German. Counts of terms and conventions refer to texts, not individual occurrences.

| Comparison | Expanded: 598 pairs | New only: 338 pairs |
|---|---|---|
| Seven complexity measures | All retain the original direction; all paired bootstrap intervals exclude zero | Same pattern for all seven |
| Machine use of ß; official use | 434; 0 | 240; 0 |
| Motion retained, official vs machine | 88/94 vs 44/94 | 47/51 vs 22/51 |
| Interpellation retained, official vs machine | 38/39 vs 8/39 | 24/24 vs 7/24 |
| French abbreviation retained without German equivalent, machine vs official | 93/119 vs 0/119 | 52/65 vs 0/65 |
| French sentence count matched, machine vs official | 65.4% vs 36.6% | 66.3% vs 39.1% |
| Length-adjusted source–target depth correlation, machine vs official | 0.400 vs 0.143 | 0.369 vs 0.090 |
| Source-adjusted chrF trend per decade [95% interval] | +1.74 [1.24, 2.28] | +1.76 [1.15, 2.43] |

The broad patterns persist, but differences vary across terms: both versions retain *Conseil national* as *Nationalrat* in every matched text, and both retain *Ständerat* in all four new-only cases. Full results include every checked term and convention, not just the examples above.

## Read the detailed results

| Analysis | Expanded sample | New-only sample |
|---|---|---|
| Complexity | [Complexity comparison](results/expanded/translation_complexity_summary.md) | [Complexity comparison](results/new_only/translation_complexity_summary.md) |
| Spelling and formatting | [Conventions](results/expanded/swiss_writing_conventions.md) | [Conventions](results/new_only/swiss_writing_conventions.md) |
| Institutional terms and abbreviations | [Terminology](results/expanded/swiss_terminology.md) | [Terminology](results/new_only/swiss_terminology.md) |
| Historical similarity and source structure | [Results guide](results/expanded/README.md) | [Results guide](results/new_only/README.md) |

Each sample has the same report filenames, table layouts and figures as the main results. The [combined complexity table](results/balanced_complexity_summary.md) also compares both samples directly with the original.

Complexity intervals use 2,000 paired resamples within year; this supplementary analysis does not repeat the author-adjusted mixed models or multiple-comparison correction. MATTR requires sufficient text length and covers 592 expanded and 334 new-only pairs. Similarity-trend intervals use 2,000 author-cluster resamples. Their adjustment includes French sentence length, tree depth and log word count. Increasing similarity does not identify whether official translators used MT.

## Review status

All 339 added outputs completed normally. Automatic screening found no French-word flags and 14 repetition flags; these flags still need manual inspection. Their IDs are saved in `results/balanced_complexity.json`. New terminology results are automated applications of the original rules, not manually confirmed translation errors. Each sample's `terminology_matches.csv` and `terminology_examples.csv` support inspection. Term presence anywhere in a text does not establish correct translation of every occurrence.

## Reproduce

First run the main reproduction command from the repository README. It creates the author classifications and original measurements reused here. With the same analysis environment activated, run from the repository root:

```bash
bash supplementary/reproduce.sh
```

This uses saved translations; no model download or generation is required. It regenerates the selection, measurements and detailed summaries, without changing the report results. The overview above describes the saved analysis.

| Location | Contents |
|---|---|
| `scripts/` | Balanced comparison, additional analyses and optional translation generation |
| `data/` | Two saved translation batches, their sampling records and the balanced selection |
| `results/` | Measurements, detailed summaries and terminology excerpts |

To regenerate or resume an existing translation batch, install the translation dependencies and model described in the main README, then run `python supplementary/scripts/translate_additional.py --batch 1` (or `--batch 2`). Existing completed outputs are reused. Additional batches are not needed for the balanced comparison.
