# Preservation of French sentence counts

Comparison of 338 completed French–German translation triples. Both German versions use the same counting rules as the French source, with language-specific tokenizers and sentence boundaries at punctuation and nonempty lines.

This comparison checks whether the machine output follows the French source’s sentence count more closely than the official translation does.

## Results

| German version | Matches French sentence count | Percentage |
|---|---:|---:|
| Official | 132/338 | 39.1% |
| Machine | 224/338 | 66.3% |

## Interpretation

Equal sentence counts suggest count preservation, but do not establish matching boundaries or preservation of meaning. Abbreviations and numbered lists can affect rule-based sentence counts.

## Consistency check and data

German count mismatches against the complexity results: 0.
Sentence and word counts are saved in [source_sentence_counts.json](data/source_sentence_counts.json). Word counts also support the [source-adjusted similarity analysis](source_adjusted_similarity.md).
