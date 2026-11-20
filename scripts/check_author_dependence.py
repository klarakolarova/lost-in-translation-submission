"""Check whether the complexity findings hold when accounting for repeated authors.

Several motions were submitted by the same parliamentarian and may share
writing characteristics. Treating every motion as independent could therefore
underestimate uncertainty in the machine–official comparison.

For the seven measures in Figure 2, this script uses two checks:
- A mixed-effects model that allows the average difference to vary by author.
- A bootstrap that resamples authors, keeping each author's motions together
  (2,000 resamples, seed 47).

It also calculates Bonferroni-adjusted model intervals to account for testing
seven measures. The estimates and intervals are saved alongside the original
comparison in results/complexity_author_dependence.md.
"""

# Import tools for grouping motions, fitting models and resampling authors.
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
import csv
import json
import random
import warnings

import numpy as np

import statsmodels.formula.api as smf

from linguistic_measures import REPORTED_MEASURES

# Set input and output locations relative to the project.
ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PROC = RESULTS / "data"
REPORT = RESULTS / "complexity_author_dependence.md"

SEED, RESAMPLES = 47, 2000


# Estimate an author random-intercept model and ordinary and corrected intervals.
def fit_author_model(rows: list[tuple]) -> tuple:
    data = {
        "diff": [difference for _, difference in rows],
        "author": [author_id for author_id, _ in rows],
    }
    # Record known variance warnings once in the report instead of repeating them.
    known_messages = {
        "Random effects covariance is singular": "Singular author covariance during fitting",
        "The random effects covariance matrix is singular.": "Singular author covariance during fitting",
        "The MLE may be on the boundary of the parameter space.": "Variance near the boundary",
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fit = smf.mixedlm("diff ~ 1", data, groups=data["author"]).fit(reml=True)
    notes = []
    for warning in caught:
        message = str(warning.message)
        if message in known_messages:
            if known_messages[message] not in notes:
                notes.append(known_messages[message])
        else:
            warnings.warn_explicit(
                warning.message, warning.category, warning.filename, warning.lineno
            )
    if not fit.converged:
        raise RuntimeError("Author mixed-effects model did not converge.")
    estimate = fit.params["Intercept"]
    model_lower, model_upper = fit.conf_int().loc["Intercept"]
    corrected_lower, corrected_upper = fit.conf_int(
        alpha=0.05 / len(REPORTED_MEASURES)
    ).loc["Intercept"]
    estimates = (estimate, model_lower, model_upper, corrected_lower, corrected_upper)
    if not np.all(np.isfinite(estimates)):
        raise RuntimeError(
            "Author mixed-effects model returned non-finite estimates or intervals."
        )
    author_variance = float(np.asarray(fit.cov_re)[0, 0])
    variance_share = author_variance / (author_variance + fit.scale)
    return estimates, variance_share, "; ".join(notes) or "No variance warnings"


# Resample whole authors so motions by the same person stay together.
def bootstrap_authors(rows: list[tuple]) -> tuple[float, float]:
    by_author = defaultdict(list)
    for author_id, difference in rows:
        by_author[author_id].append(difference)
    clusters = list(by_author.values())
    rng = random.Random(SEED)
    bootstrap_means = sorted(
        mean(
            difference
            for cluster in rng.choices(clusters, k=len(clusters))
            for difference in cluster
        )
        for _ in range(RESAMPLES)
    )
    cluster_lower, cluster_upper = (
        bootstrap_means[int(0.025 * RESAMPLES) - 1],
        bootstrap_means[int(0.975 * RESAMPLES)],
    )
    return cluster_lower, cluster_upper


# Save the comparison of document-based and author-aware estimates.
def save_report(results: dict, records: list[tuple], author_by_motion: dict) -> None:
    authors = Counter(author_by_motion[document_id] for document_id, _, _ in records)

    lines = [
        "# Translation complexity: accounting for repeated authors",
        "",
        f"Pairs: {len(records)}; distinct authors: {len(authors)}; authors with more than one text: "
        f"{sum(motion_count > 1 for motion_count in authors.values())}; most texts by one author: {max(authors.values())}.",
        "",
        "These checks assess whether the comparison changes when motions by the same "
        "author are treated as related observations. The mixed model allows an "
        "author-specific intercept, and the bootstrap resamples whole authors. "
        "Bonferroni intervals account for testing seven measures.",
        "",
        "Differences are machine minus official German. Values in brackets are confidence intervals; the final column adjusts for testing seven measures together.",
        "",
        "## Results",
        "",
        "| Measure | Original estimate [95% interval] | Author-adjusted estimate [95% interval] | Author bootstrap estimate [95% interval] | Adjusted interval for seven measures |",
        "|---|---|---|---|---|",
    ]
    diagnostics = []
    for key, label, _ in REPORTED_MEASURES:
        rows = [
            (author_by_motion[document_id], generated[key] - official[key])
            for document_id, official, generated in records
            if official.get(key) is not None and generated.get(key) is not None
        ]
        document_lower, document_upper = results["summary"][key][
            "paired_bootstrap_ci95"
        ]
        estimates, variance_share, fit_note = fit_author_model(rows)
        estimate, model_lower, model_upper, corrected_lower, corrected_upper = estimates
        diagnostics.append(
            f"| {label} | Yes | {100 * variance_share:.3f}% | {fit_note} |"
        )
        cluster_lower, cluster_upper = bootstrap_authors(rows)
        lines.append(
            f"| {label} | {mean(difference for _, difference in rows):+.3f} [{document_lower:+.3f}, {document_upper:+.3f}] | "
            f"{estimate:+.3f} [{model_lower:+.3f}, {model_upper:+.3f}] | {mean(difference for _, difference in rows):+.3f} [{cluster_lower:+.3f}, {cluster_upper:+.3f}] | "
            f"[{corrected_lower:+.3f}, {corrected_upper:+.3f}] |"
        )
    lines += [
        "",
        "## How to read this check",
        "",
        "An interval entirely above or below zero supports a difference after the corresponding adjustment. Compare these estimates with the [main complexity results](translation_complexity_summary.md).",
    ]
    lines += [
        "",
        "## Model fitting",
        "",
        "The table records variance warnings once per measure. A singular author covariance means the author-variance component was effectively zero during fitting; a boundary warning indicates a small estimated variance in the measure’s own units. This threshold depends on scale and need not imply a negligible share of total variance. These warnings do not by themselves mean that fitting failed. The final share below is the estimated proportion of variation in paired differences attributable to authors, not a measure of translation quality.",
        "",
        "All reported models converged and returned finite estimates and intervals. Estimates near zero can make model-based uncertainty less reliable, so the author bootstrap provides a separate check without fitting an author-variance component.",
        "",
        "| Measure | Converged | Author share of variance | Fitting note |",
        "|---|---|---:|---|",
        *diagnostics,
    ]
    RESULTS.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


# Load the paired measurements and author IDs, then run the robustness checks.
def main() -> None:
    with open(PROC / "motion_author_language.csv", encoding="utf-8") as file_handle:
        author_by_motion = {
            int(record["document_id"]): record["member_id"]
            for record in csv.DictReader(file_handle)
        }
    results = json.loads(
        (PROC / "translation_complexity.json").read_text(encoding="utf-8")
    )
    records = [
        (int(record["document_id"]), record["official"], record["generated"])
        for record in results["records"]
    ]
    save_report(results, records, author_by_motion)
    print(
        f"  {len(records)} completed translation pairs; authors: {len({author_by_motion[document_id] for document_id, _, _ in records})}."
    )
    print(
        "  All seven models converged with finite estimates and intervals; fitting notes are in the report."
    )
    print("  Report: results/complexity_author_dependence.md")


# Run the robustness checks when this file is executed directly.
if __name__ == "__main__":
    main()
