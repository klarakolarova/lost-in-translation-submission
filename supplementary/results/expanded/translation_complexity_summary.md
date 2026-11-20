# Translation complexity: main results

Comparison of 598 translation pairs from motions classified as French-authored. Differences are calculated as machine minus official German.

This comparison asks whether the machine translations use simpler vocabulary and sentence structures than the official translations.

## Overall differences

| Measure | Pairs | Difference | 95% confidence interval | Machine higher |
|---|---:|---:|---|---:|
| Words per sentence | 598 | +0.988 | [+0.688, +1.326] | 341 of 598 |
| Mean max. sentence depth | 598 | +0.343 | [+0.275, +0.412] | 387 of 598 |
| Subordinate markers / 100 words | 598 | +0.324 | [+0.252, +0.395] | 376 of 598 |
| Relative markers / 100 words | 598 | +0.391 | [+0.326, +0.460] | 402 of 598 |
| Word frequency (Zipf) | 598 | +0.125 | [+0.112, +0.137] | 473 of 598 |
| Lexical variety (MATTR) | 592 | -0.010 | [-0.013, -0.008] | 212 of 592 |
| Readability index (LIX) | 598 | +1.722 | [+1.341, +2.104] | 382 of 598 |

## Reading the measures

Tree depth is the maximum word depth in each sentence, averaged across sentences within each text. Clause-marker rates count grammatical markers per 100 alphabetic words, rather than complete clauses.

MATTR measures lexical variety in 50-word windows; 6 pairs are too short for this measure. Higher LIX indicates harder-to-read text.

## Differences by period

The three period columns show mean paired differences within each period; they do not test whether the periods differ.

| Measure | 2000-2008 | 2009-2016 | 2017-2025 |
|---|---:|---:|---:|
| Words per sentence | +1.102 | +1.323 | +0.576 |
| Mean max. sentence depth | +0.374 | +0.393 | +0.269 |
| Subordinate markers / 100 words | +0.402 | +0.398 | +0.180 |
| Relative markers / 100 words | +0.478 | +0.395 | +0.300 |
| Word frequency (Zipf) | +0.145 | +0.121 | +0.108 |
| Lexical variety (MATTR) | -0.014 | -0.007 | -0.010 |
| Readability index (LIX) | +1.785 | +1.888 | +1.513 |

## Relative differences used in the figure

Percentage differences in Zipf scores provide a common plotting scale, not percentage changes in word frequency. Zipf is logarithmic; the ratio below expresses the difference on the frequency scale.

A Zipf difference of +0.125 corresponds to a 1.33-fold geometric mean frequency ratio on the scored scale.

| Measure | % of official mean | 95% confidence interval |
|---|---:|---|
| Words per sentence | +4.4% | [+3.1%, +5.9%] |
| Mean max. sentence depth | +5.2% | [+4.2%, +6.3%] |
| Subordinate markers / 100 words | +18.5% | [+14.4%, +22.5%] |
| Relative markers / 100 words | +30.2% | [+25.2%, +35.6%] |
| Word frequency (Zipf) | +3.0% | [+2.7%, +3.3%] |
| Lexical variety (MATTR) | -1.3% | [-1.6%, -1.0%] |
| Readability index (LIX) | +2.8% | [+2.2%, +3.5%] |

## Additional measures

Additional comparisons; an interval including zero indicates no clear evidence of a difference:

- Mean dependency distance: -0.010 [-0.034, +0.015]
- Lexical density: -0.198 [-0.408, +0.013]

## Method and related results

These intervals estimate sampling uncertainty in the average difference between machine and official German. We resample motion pairs within each year to preserve the sample’s yearly composition. We use 2,000 resamples with seed 47 reset for each measure for reproducibility and take the middle 95% of the resampled mean differences. Author-adjusted mixed models and multiple-comparison correction have not been repeated for this sample.

See the [detailed results](translation_complexity_details.md) for both versions’ means. Author-adjusted mixed models and multiple-comparison correction have not been repeated for this sample.

![Differences in linguistic complexity](figures/complexity_differences.png)
