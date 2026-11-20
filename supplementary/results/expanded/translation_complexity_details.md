# Translation complexity: detailed results

Attempted: 598; normally stopped outputs analysed: 598; flagged failures excluded: 0.

This table provides the full measurements behind the [complexity summary](translation_complexity_summary.md). It compares completed translations of motions classified as French-authored. See [translation screening](translation_screening.md) for the quality checks.

Differences are machine German minus official German. The 95% intervals indicate sampling uncertainty in these average differences, estimated using 2,000 bootstrap resamples of motion pairs within each year.

## Results

Higher / lower / tied counts compare the machine value with the official value in each pair. MATTR uses 50-word windows and is available for 592 pairs.

| Measure | Pairs | Official mean | Machine mean | Difference | 95% confidence interval | Higher / lower / tied |
|---|---:|---:|---:|---:|---|---|
| Words per sentence | 598 | 22.3866 | 23.3744 | +0.9878 | [+0.6876, +1.3261] | 341 / 252 / 5 |
| Mean max. sentence depth | 598 | 6.5600 | 6.9034 | +0.3434 | [+0.2754, +0.4118] | 387 / 196 / 15 |
| Mean dependency distance | 598 | 3.1508 | 3.1412 | -0.0097 | [-0.0341, +0.0153] | 273 / 325 / 0 |
| Word frequency (Zipf) | 598 | 4.1406 | 4.2654 | +0.1247 | [+0.1117, +0.1374] | 473 / 125 / 0 |
| Word frequency (Zipf; zero scores excluded) | 598 | 4.2768 | 4.3530 | +0.0762 | [+0.0659, +0.0866] | 434 / 164 / 0 |
| Lexical density (%) | 598 | 52.3107 | 52.1128 | -0.1979 | [-0.4084, +0.0134] | 290 / 306 / 2 |
| Lexical variety (MATTR) | 592 | 0.7704 | 0.7600 | -0.0103 | [-0.0126, -0.0080] | 212 / 380 / 0 |
| Subordinate markers / 100 words | 598 | 1.7543 | 2.0782 | +0.3238 | [+0.2521, +0.3945] | 376 / 203 / 19 |
| Relative markers / 100 words | 598 | 1.2930 | 1.6840 | +0.3910 | [+0.3263, +0.4597] | 402 / 176 / 20 |
| Readability index (LIX) | 598 | 60.5896 | 62.3120 | +1.7223 | [+1.3409, +2.1039] | 382 / 216 / 0 |

## Excluded output

No failed outputs are included in this completed-pair comparison.

