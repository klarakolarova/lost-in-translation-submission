# Translation complexity: accounting for repeated authors

Pairs: 259; distinct authors: 102; authors with more than one text: 60; most texts by one author: 11.

These checks assess whether the comparison changes when motions by the same author are treated as related observations. The mixed model allows an author-specific intercept, and the bootstrap resamples whole authors. Bonferroni intervals account for testing seven measures.

Differences are machine minus official German. Values in brackets are confidence intervals; the final column adjusts for testing seven measures together.

## Results

| Measure | Original estimate [95% interval] | Author-adjusted estimate [95% interval] | Author bootstrap estimate [95% interval] | Adjusted interval for seven measures |
|---|---|---|---|---|
| Words per sentence | +1.078 [+0.657, +1.509] | +1.078 [+0.616, +1.540] | +1.078 [+0.681, +1.506] | [+0.444, +1.712] |
| Mean max. sentence depth | +0.277 [+0.182, +0.377] | +0.277 [+0.172, +0.382] | +0.277 [+0.177, +0.382] | [+0.133, +0.421] |
| Subordinate markers / 100 words | +0.264 [+0.158, +0.361] | +0.264 [+0.155, +0.373] | +0.264 [+0.156, +0.369] | [+0.114, +0.413] |
| Relative markers / 100 words | +0.355 [+0.250, +0.457] | +0.355 [+0.245, +0.466] | +0.355 [+0.255, +0.459] | [+0.203, +0.507] |
| Word frequency (Zipf) | +0.118 [+0.100, +0.136] | +0.119 [+0.097, +0.141] | +0.118 [+0.095, +0.143] | [+0.089, +0.149] |
| Lexical variety (MATTR) | -0.009 [-0.012, -0.006] | -0.009 [-0.012, -0.006] | -0.009 [-0.013, -0.006] | [-0.014, -0.005] |
| Readability index (LIX) | +1.774 [+1.199, +2.387] | +1.774 [+1.155, +2.393] | +1.774 [+1.194, +2.342] | [+0.924, +2.624] |

## How to read this check

An interval entirely above or below zero supports a difference after the corresponding adjustment. Compare these estimates with the [main complexity results](translation_complexity_summary.md).

## Model fitting

The table records variance warnings once per measure. A singular author covariance means the author-variance component was effectively zero during fitting; a boundary warning indicates a small estimated variance in the measure’s own units. This threshold depends on scale and need not imply a negligible share of total variance. These warnings do not by themselves mean that fitting failed. The final share below is the estimated proportion of variation in paired differences attributable to authors, not a measure of translation quality.

All reported models converged and returned finite estimates and intervals. Estimates near zero can make model-based uncertainty less reliable, so the author bootstrap provides a separate check without fitting an author-variance component.

| Measure | Converged | Author share of variance | Fitting note |
|---|---|---:|---|
| Words per sentence | Yes | 0.000% | Singular author covariance during fitting; Variance near the boundary |
| Mean max. sentence depth | Yes | 0.058% | Variance near the boundary |
| Subordinate markers / 100 words | Yes | 0.000% | Variance near the boundary |
| Relative markers / 100 words | Yes | 0.000% | Singular author covariance during fitting; Variance near the boundary |
| Word frequency (Zipf) | Yes | 10.243% | Variance near the boundary |
| Lexical variety (MATTR) | Yes | 0.465% | Variance near the boundary |
| Readability index (LIX) | Yes | 0.000% | Variance near the boundary |
