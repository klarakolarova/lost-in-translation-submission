# Translation complexity: detailed results

Attempted: 260; normally stopped outputs analysed: 259; flagged failures excluded: 1.

This table provides the full measurements behind the [complexity summary](translation_complexity_summary.md). It compares completed translations of motions classified as French-authored. See [translation screening](translation_screening.md) for the quality checks.

Differences are machine German minus official German. The 95% intervals indicate sampling uncertainty in these average differences, estimated using 2,000 bootstrap resamples of motion pairs within each year.

## Results

Higher / lower / tied counts compare the machine value with the official value in each pair. MATTR uses 50-word windows and is available for 257 pairs.

| Measure | Pairs | Official mean | Machine mean | Difference | 95% confidence interval | Higher / lower / tied |
|---|---:|---:|---:|---:|---|---|
| Words per sentence | 259 | 22.0794 | 23.1575 | +1.0781 | [+0.6570, +1.5087] | 144 / 113 / 2 |
| Mean max. sentence depth | 259 | 6.5280 | 6.8049 | +0.2769 | [+0.1820, +0.3772] | 159 / 94 / 6 |
| Mean dependency distance | 259 | 3.1442 | 3.1464 | +0.0022 | [-0.0329, +0.0393] | 128 / 131 / 0 |
| Word frequency (Zipf) | 259 | 4.1554 | 4.2730 | +0.1175 | [+0.0997, +0.1358] | 200 / 59 / 0 |
| Word frequency (Zipf; zero scores excluded) | 259 | 4.2905 | 4.3626 | +0.0721 | [+0.0569, +0.0882] | 182 / 77 / 0 |
| Lexical density (%) | 259 | 52.1963 | 52.0790 | -0.1173 | [-0.4180, +0.1934] | 136 / 121 / 2 |
| Lexical variety (MATTR) | 257 | 0.7707 | 0.7615 | -0.0092 | [-0.0122, -0.0060] | 97 / 160 / 0 |
| Subordinate markers / 100 words | 259 | 1.7657 | 2.0295 | +0.2637 | [+0.1579, +0.3606] | 161 / 90 / 8 |
| Relative markers / 100 words | 259 | 1.3369 | 1.6921 | +0.3552 | [+0.2498, +0.4567] | 175 / 79 / 5 |
| Readability index (LIX) | 259 | 60.0930 | 61.8670 | +1.7740 | [+1.1991, +2.3866] | 161 / 98 / 0 |

## Excluded output

The following generation reached its output limit. The full attempt remains in the input file.

- 20003342: length.
