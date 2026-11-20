# Source-adjusted similarity trend

Existing 598 completed French-author translation pairs, 2000–2025; not the full corpus.

This check asks whether the rise in similarity remains after accounting for changes in the French texts’ length and sentence structure.

## Method

Linear regression estimates the change in chrF points per decade. The adjusted model accounts for French mean sentence length, mean maximum sentence depth and log word count, with these three measures standardized. The 95% confidence intervals use 2,000 resamples of whole authors (seed 50). These exploratory intervals are not adjusted for multiple comparisons.

## Results

| Model | chrF points per decade | 95% confidence interval |
|---|---:|---|
| Unadjusted | +1.598 | [+0.915, +2.334] |
| Adjusted for French source | +1.737 | [+1.238, +2.283] |

Adjusted minus unadjusted trend: +0.139 chrF points per decade (95% paired author-bootstrap interval [-0.317, +0.599]).

## Interpretation

This comparison checks whether the similarity trend persists after accounting for the measured French-source properties. It cannot separate MT use from other explanations, such as changing topics or overlap with the model’s training data.

See [translation similarity](translation_similarity.md) for the period averages and [source_adjusted_similarity.json](data/source_adjusted_similarity.json) for the saved estimates.
