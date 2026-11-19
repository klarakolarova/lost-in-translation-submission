# Source-adjusted similarity trend

Existing 259 completed French-author translation pairs, 2000–2025; not the full corpus.

OLS slopes per decade; 2,000 author-cluster bootstrap samples, seed 50. Source controls: mean sentence length, mean tree depth, log document word count. Source controls standardized; year in decades. Intervals are exploratory and not multiplicity-corrected.

| chrF model | Year slope per decade | 95% author-bootstrap interval |
|---|---:|---|
| Unadjusted | +1.628 | [+0.697, +2.570] |
| Adjusted for French source | +1.711 | [+0.949, +2.506] |

Paired change in coefficient: {'slope_difference_adjusted_minus_unadjusted': 0.08259774633142736, 'paired_author_bootstrap_95_ci': [-0.5448452836992247, 0.6776364094954155]}

## Limits

- Linear descriptive trends can conceal nonlinear changes.
- Changes describe this text sample, not French/German language evolution generally.
- Adjustment does not address topics, guidelines, parser errors, unmeasured source properties or model training overlap.
- Remaining year association does not identify MT use; source changes could themselves reflect changing writing tools.
