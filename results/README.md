# Results guide

The results compare machine and official German translations of Swiss parliamentary motions classified as French-authored. The fixed sample contains 260 motions from 2000–2025; 259 translations completed and one reached its output limit.

Start with the summaries below. The reproduction script regenerates the reports, figures and supporting data from the saved inputs. This guide explains where to find each result.

## Sample and quality checks

| Report | What it explains |
|---|---|
| [Author language](author_language_summary.md) | How author language was estimated and how the French-authored sampling pool was formed. |
| [Translation screening](translation_screening.md) | Generation checks, automatic flags and the saved manual review of 20 texts. |

## Linguistic complexity

| Report | What it explains |
|---|---|
| [Main comparison](translation_complexity_summary.md) | The seven measures shown in the report figure, differences by period and additional checks. |
| [Detailed comparison](translation_complexity_details.md) | Both German versions’ means, uncertainty intervals and text-level direction counts for all retained measures. |
| [Repeated authors](complexity_author_dependence.md) | Whether the differences persist when multiple motions by one author are treated as related. |
| [Sentence counts](source_sentence_counts.md) | How often each German version matches the French source’s sentence count. |
| [Sentence depth](source_tree_depth.md) | How closely German sentence depth varies with French source depth, before and after adjusting for sentence length. |

## Swiss terminology and conventions

| Report | What it explains |
|---|---|
| [Parliamentary terminology](swiss_terminology.md) | Retention of institutional terms and translation of French abbreviations. |
| [Spelling and formatting](swiss_writing_conventions.md) | Presence of ß, quotation marks and number-formatting patterns in the paired sample. |
| [Wider-corpus context](character_conventions.md) | Character storage over time and conventions in recent official texts grouped by estimated author language. |

## Similarity over time

| Report | What it explains |
|---|---|
| [Translation similarity](translation_similarity.md) | chrF and BLEU similarity by period and the overall chrF trend. |
| [Adjustment for French inputs](source_adjusted_similarity.md) | Whether the trend persists after accounting for source length and sentence depth. |

## How to read the comparisons

- **Official** means the published German text; **machine** means the saved model output for the same French source.
- Complexity differences are **machine minus official**. A positive difference means the machine value is higher; it does not automatically mean better or worse.
- A **95% confidence interval** shows uncertainty around an estimate under the stated resampling or modelling method. For a difference, an interval spanning zero does not clearly distinguish an increase from a decrease.
- Counts generally refer to **texts**, not every occurrence of a word or character. Each report states its population and counting rule.
- Author language is an estimate from canton and biography information, not verified source-language metadata.

## Supporting files

CSV files are tables that can be opened in a spreadsheet. JSON files retain structured measurements for the scripts; their field names stay stable so downstream analyses can read them.

| File | Contents |
|---|---|
| [Validated sample](data/validated_sample.json) | The fixed selection checked against the saved corpus and translation attempts. |
| [Author classifications](data/motion_author_language.csv) | Estimated author language and classification information for each motion. |
| [French-authored pool](data/french_authored_motions.csv) | Eligible motions classified as French-authored. |
| [Complexity measurements](data/translation_complexity.json) | Paired German measurements, summary estimates and generation exclusions. |
| [Sentence counts](data/source_sentence_counts.json) | French and German counts and their comparison. |
| [Sentence depth](data/source_tree_depth.json) | Document measurements and source–target correlation estimates. |
| [Terminology decisions](terminology_matches.csv) | One row per text and checked term. |
| [Terminology excerpts](terminology_examples.csv) | Source and translation excerpts supporting inspection of those decisions. |
| [Similarity scores](translation_similarity.csv) | Document-level chrF and BLEU scores. |
| [Adjusted similarity estimates](data/source_adjusted_similarity.json) | Source measurements and regression results for the adjustment check. |

The `figures/` folder contains the complexity and similarity plots, plus `design_tikz.tex`, the LaTeX source for the study-design figure.
