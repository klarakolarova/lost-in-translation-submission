# Supplementary balanced complexity comparison

The expanded sample contains 598 pairs (23 per year, 2000–2025), retaining all 259 completed report pairs. The smallest eligible yearly pool (2002) limits the balanced total. Random additions use seed 51.

The new-only comparison uses 338 pairs (13 per year; seed 52) with no overlap with the original sample. It is a subset of the expanded sample.

Differences are machine minus official German. Intervals use the report’s 2,000 within-year paired bootstrap resamples. They do not adjust for repeated authors or multiple comparisons. Selection was made without inspecting the new linguistic scores.

| Measure | Original difference | Expanded difference [95% CI] | New-only difference [95% CI] | Expanded / new-only pairs |
|---|---:|---:|---:|---:|
| Words per sentence | +1.078 | +0.988 [+0.688, +1.326] | +0.918 [+0.487, +1.347] | 598 / 338 |
| Mean max. sentence depth | +0.277 | +0.343 [+0.275, +0.412] | +0.396 [+0.306, +0.490] | 598 / 338 |
| Subordinate markers / 100 words | +0.264 | +0.324 [+0.252, +0.395] | +0.371 [+0.276, +0.471] | 598 / 338 |
| Relative markers / 100 words | +0.355 | +0.391 [+0.326, +0.460] | +0.418 [+0.336, +0.500] | 598 / 338 |
| Word frequency (Zipf) | +0.118 | +0.125 [+0.112, +0.137] | +0.129 [+0.113, +0.146] | 598 / 338 |
| Lexical variety (MATTR) | -0.009 | -0.010 [-0.013, -0.008] | -0.011 [-0.015, -0.008] | 592 / 334 |
| Readability index (LIX) | +1.774 | +1.722 [+1.341, +2.104] | +1.692 [+1.199, +2.182] | 598 / 338 |

## Screening and scope

All 339 added outputs stopped normally. Automated French-word flags: 0; repetition flags: 14.

These new flags have not yet been manually reviewed; completed generation does not guarantee translation accuracy. No new human quality annotations are claimed. The original analyses and report sample remain unchanged.

This table reports all seven complexity measures. Conventions, terminology and similarity are analysed separately by compare_other_results.py.

Run from the repository root: `python supplementary/scripts/compare_balanced_sample.py`. Requires the analysis dependencies and both completed supplementary batches.
