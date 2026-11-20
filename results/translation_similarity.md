# Similarity of official translations to machine output

French-authored sample, 259 completed pairs. chrF/BLEU: machine vs official German (sacreBLEU, scored separately for each complete document). 95% intervals: 2000 document bootstrap resamples, seed 47.

chrF compares overlapping character sequences; BLEU compares overlapping word sequences. Both are reported on a 0–100 scale, with higher scores indicating greater similarity to the official German wording, not necessarily a better translation.

## Similarity by period

| Period | Texts | Mean chrF | 95% confidence interval | Mean BLEU |
|---|---:|---:|---|---:|
| 2000-2004 | 49 | 57.3 | [55.8, 58.6] | 16.2 |
| 2005-2009 | 50 | 56.4 | [54.9, 57.9] | 17.4 |
| 2010-2014 | 50 | 55.9 | [54.6, 57.3] | 17.2 |
| 2015-2019 | 50 | 57.8 | [56.6, 59.0] | 18.6 |
| 2020-2022 | 30 | 59.1 | [57.4, 61.0] | 20.1 |
| 2023-2025 | 30 | 61.4 | [59.3, 63.4] | 24.2 |

## Trend over time

Linear trend: +1.63 chrF per decade, 95% CI [+0.81, +2.45].

## Interpretation

Increasing similarity is consistent with official translations increasingly being produced from MT output. However, the same pattern could arise if the model had seen recent official translations during training; our data cannot separate these explanations.

See the [source-adjusted analysis](source_adjusted_similarity.md) for a check accounting for changes in the French inputs. Document scores are in [translation_similarity.csv](translation_similarity.csv).

![Translation similarity over time](figures/translation_similarity.png)
