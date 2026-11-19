# Exploratory source-structure comparison

259 completed French-source / official-German / generated-German triples. No new translations.

Counts use language-specific spaCy tokenizers, .!? sentence boundaries, preserved Art./art. and digit-letter references. The primary analysis also starts sentences at nonempty lines, as in the existing German analysis.

Negative paired gap differences mean the generated sentence count is closer to the source.

## punctuation_and_lines

| Measure | French | Official German | Generated German |
|---|---:|---:|---:|
| mean_sentence_count | 10.830 | 11.436 | 10.625 |
| mean_word_count | 289.541 | 245.892 | 237.185 |
| mean_sentence_words | 27.943 | 22.079 | 23.157 |
| exact_source_count_matches | — | 86.000 | 166.000 |
| mean_absolute_sentence_count_gap | — | 1.417 | 0.614 |
| mean_target_source_word_ratio | — | 0.856 | 0.823 |

Generated closer: 137; official closer: 32; tied: 90.
Paired mean absolute count-gap difference: -0.803; exploratory 95% bootstrap CI: [-0.9885135135135136, -0.6332046332046332].

## Validation and limits

German count differences against saved results: 0.

- Sentence-count equality does not establish matching boundaries, alignment, syntax or meaning.
- Language-specific tokenization and German compounding limit direct word-length comparisons.
- Rule-based segmentation can mishandle abbreviations and numbered lists.
- Bootstrap is exploratory, stratified by year, not adjusted for repeated authors or multiple testing.