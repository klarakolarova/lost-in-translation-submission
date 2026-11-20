# Translation complexity: detailed results

Attempted: 338; normally stopped outputs analysed: 338; flagged failures excluded: 0.

This table provides the full measurements behind the [complexity summary](translation_complexity_summary.md). It compares completed translations of motions classified as French-authored. See [translation screening](translation_screening.md) for the quality checks.

Differences are machine German minus official German. The 95% intervals indicate sampling uncertainty in these average differences, estimated using 2,000 bootstrap resamples of motion pairs within each year.

## Results

Higher / lower / tied counts compare the machine value with the official value in each pair. MATTR uses 50-word windows and is available for 334 pairs.

| Measure | Pairs | Official mean | Machine mean | Difference | 95% confidence interval | Higher / lower / tied |
|---|---:|---:|---:|---:|---|---|
| Words per sentence | 338 | 22.6252 | 23.5434 | +0.9182 | [+0.4874, +1.3468] | 196 / 139 / 3 |
| Mean max. sentence depth | 338 | 6.5840 | 6.9803 | +0.3963 | [+0.3060, +0.4903] | 228 / 101 / 9 |
| Mean dependency distance | 338 | 3.1558 | 3.1373 | -0.0185 | [-0.0522, +0.0153] | 145 / 193 / 0 |
| Word frequency (Zipf) | 338 | 4.1305 | 4.2599 | +0.1294 | [+0.1131, +0.1457] | 272 / 66 / 0 |
| Word frequency (Zipf; zero scores excluded) | 338 | 4.2673 | 4.3462 | +0.0789 | [+0.0662, +0.0927] | 251 / 87 / 0 |
| Lexical density (%) | 338 | 52.4000 | 52.1430 | -0.2571 | [-0.5377, +0.0172] | 154 / 184 / 0 |
| Lexical variety (MATTR) | 334 | 0.7702 | 0.7589 | -0.0113 | [-0.0146, -0.0080] | 114 / 220 / 0 |
| Subordinate markers / 100 words | 338 | 1.7426 | 2.1141 | +0.3715 | [+0.2758, +0.4707] | 215 / 112 / 11 |
| Relative markers / 100 words | 338 | 1.2632 | 1.6808 | +0.4176 | [+0.3363, +0.5005] | 226 / 97 / 15 |
| Readability index (LIX) | 338 | 60.9637 | 62.6556 | +1.6919 | [+1.1989, +2.1816] | 221 / 117 / 0 |

## Excluded output

No failed outputs are included in this completed-pair comparison.

