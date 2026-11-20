"""Check whether the chrF time trend persists after accounting for French-source structure.

Compare the unadjusted trend with a model including French sentence length,
sentence tree depth and document length. Resample authors with all their
motions to estimate uncertainty while accounting for repeated authors.

Save model estimates and the comparison in results/.
"""

# Import tools for loading measurements and fitting regression models.
from pathlib import Path
import csv
import json

import numpy as np

# Set input and output locations and the bootstrap settings.
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "results/data"
SEED, RESAMPLES = 50, 2000


# Load CSV rows indexed by document ID.
def read_index(path: Path) -> dict:
    with path.open(encoding="utf-8") as file_handle:
        return {
            int(record["document_id"]): record for record in csv.DictReader(file_handle)
        }


# Fit the regression and return the year coefficient from its second column.
def coefficient(design, outcome, indices) -> float:
    sample_design, sample_outcome = design[indices], outcome[indices]
    if np.linalg.matrix_rank(sample_design) != sample_design.shape[1]:
        raise ValueError("Rank-deficient regression design")
    return float(np.linalg.lstsq(sample_design, sample_outcome, rcond=None)[0][1])


# Join the saved measurements and check that they describe the same sample.
def load_records() -> list[dict]:
    syntax = json.loads((DATA / "source_tree_depth.json").read_text(encoding="utf-8"))[
        "records"
    ]
    counts = json.loads(
        (DATA / "source_sentence_counts.json").read_text(encoding="utf-8")
    )["analyses"]["punctuation_and_lines"]["records"]
    counts = {record["document_id"]: record for record in counts}
    scores = read_index(ROOT / "results/translation_similarity.csv")
    authors = read_index(DATA / "motion_author_language.csv")
    ids = [record["document_id"] for record in syntax]
    if len(set(ids)) != len(ids) or set(ids) != set(scores) or set(ids) != set(counts):
        raise ValueError("Samples do not match exactly")
    rows = []
    for record in syntax:
        document_id = record["document_id"]
        author_id = authors[document_id]["member_id"]
        if not author_id:
            raise ValueError(f"Missing author: {document_id}")
        if record["year"] != int(scores[document_id]["year"]):
            raise ValueError("Year mismatch")
        rows.append(
            {
                "document_id": document_id,
                "year": record["year"],
                "author": author_id,
                "chrf": float(scores[document_id]["chrf"]),
                "source_mean_sentence_words": record["source"]["mean_sentence_words"],
                "source_mean_sentence_tree_depth": record["source"][
                    "mean_sentence_tree_depth"
                ],
                "source_word_count": counts[document_id]["source"]["word_count"],
            }
        )
    return rows


# Build unadjusted and source-adjusted models with year measured in decades.
def build_designs(rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    document_count = len(rows)
    years = np.array([record["year"] for record in rows])
    decade = (years - 2000) / 10
    unadjusted_design = np.column_stack([np.ones(document_count), decade])
    # Source-only covariates avoid conditioning on the official translation outcome.
    source_features = np.column_stack(
        [
            [record["source_mean_sentence_words"] for record in rows],
            [record["source_mean_sentence_tree_depth"] for record in rows],
            np.log([record["source_word_count"] for record in rows]),
        ]
    )
    source_features = (
        source_features - source_features.mean(axis=0)
    ) / source_features.std(axis=0)
    adjusted_design = np.column_stack([unadjusted_design, source_features])
    return unadjusted_design, adjusted_design


# Resample authors, keeping all motions from each selected author together.
def author_draws(rows: list[dict]) -> tuple[list[np.ndarray], int]:
    author_ids = np.array([record["author"] for record in rows])
    groups = [
        np.flatnonzero(author_ids == author_id) for author_id in sorted(set(author_ids))
    ]
    rng = np.random.default_rng(SEED)
    draws = [
        np.concatenate(
            [
                groups[group_index]
                for group_index in rng.integers(0, len(groups), len(groups))
            ]
        )
        for _ in range(RESAMPLES)
    ]
    return draws, len(groups)


# Estimate a trend and its percentile interval using the shared author draws.
def estimate(design, outcome, draws) -> tuple[dict, np.ndarray]:
    bootstrap_slopes = np.array(
        [coefficient(design, outcome, indices) for indices in draws]
    )
    return {
        "slope_per_decade": coefficient(design, outcome, np.arange(len(outcome))),
        "author_bootstrap_95_ci": np.quantile(
            bootstrap_slopes, [0.025, 0.975]
        ).tolist(),
    }, bootstrap_slopes


# Compare both trends using identical draws so their difference remains paired.
def compare_trends(rows: list[dict]) -> dict:
    unadjusted_design, adjusted_design = build_designs(rows)
    draws, author_count = author_draws(rows)
    chrf_scores = np.array([record["chrf"] for record in rows])
    unadjusted_result, unadjusted_bootstrap_slopes = estimate(
        unadjusted_design, chrf_scores, draws
    )
    adjusted_result, adjusted_bootstrap_slopes = estimate(
        adjusted_design, chrf_scores, draws
    )
    difference = {
        "slope_difference_adjusted_minus_unadjusted": adjusted_result[
            "slope_per_decade"
        ]
        - unadjusted_result["slope_per_decade"],
        "paired_author_bootstrap_95_ci": np.quantile(
            adjusted_bootstrap_slopes - unadjusted_bootstrap_slopes, [0.025, 0.975]
        ).tolist(),
    }
    return {
        "n": len(rows),
        "authors": author_count,
        "seed": SEED,
        "bootstrap_draws": RESAMPLES,
        "population": f"Existing {len(rows)} completed French-author translation pairs, 2000–2025; not the full corpus.",
        "models": {
            "unadjusted": "chrF ~ intercept + (year-2000)/10",
            "adjusted": "chrF ~ intercept + (year-2000)/10 + French mean sentence words + French mean tree depth + log French document word count",
        },
        "uncertainty": "Percentile author-cluster bootstrap; authors sampled with replacement, all their documents retained. No multiplicity correction.",
        "unadjusted": unadjusted_result,
        "adjusted": adjusted_result,
        "change_in_year_coefficient": difference,
        "interpretation": (
            "This comparison checks whether the similarity trend persists after accounting for "
            "the measured French-source properties. It cannot separate MT use from other explanations, "
            "such as changing topics or overlap with the model’s training data."
        ),
        "records": rows,
    }


# Save the model results and a readable comparison of the two trends.
def save_report(output: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    unadjusted_result, adjusted_result = output["unadjusted"], output["adjusted"]
    difference = output["change_in_year_coefficient"]
    (DATA / "source_adjusted_similarity.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Source-adjusted similarity trend",
        "",
        output["population"],
        "",
        "This check asks whether the rise in similarity remains after accounting for changes in the French texts’ length and sentence structure.",
        "",
        "## Method",
        "",
        "Linear regression estimates the change in chrF points per decade. The adjusted model accounts for French mean sentence length, mean maximum sentence depth and log word count, with these three measures standardized. The 95% confidence intervals use 2,000 resamples of whole authors (seed 50). These exploratory intervals are not adjusted for multiple comparisons.",
        "",
        "## Results",
        "",
        "| Model | chrF points per decade | 95% confidence interval |",
        "|---|---:|---|",
    ]
    for label, model_result in [
        ("Unadjusted", unadjusted_result),
        ("Adjusted for French source", adjusted_result),
    ]:
        lower_bound, upper_bound = model_result["author_bootstrap_95_ci"]
        lines.append(
            f"| {label} | {model_result['slope_per_decade']:+.3f} | [{lower_bound:+.3f}, {upper_bound:+.3f}] |"
        )
    lower_bound, upper_bound = difference["paired_author_bootstrap_95_ci"]
    change = difference["slope_difference_adjusted_minus_unadjusted"]
    lines += [
        "",
        f"Adjusted minus unadjusted trend: {change:+.3f} chrF points per decade "
        f"(95% paired author-bootstrap interval [{lower_bound:+.3f}, {upper_bound:+.3f}]).",
    ]
    lines += [
        "",
        "## Interpretation",
        "",
        output["interpretation"],
        "",
        "See [translation similarity](translation_similarity.md) for the period averages and [source_adjusted_similarity.json](data/source_adjusted_similarity.json) for the saved estimates.",
    ]
    (ROOT / "results/source_adjusted_similarity.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


# Load measurements, compare the trends and print the main results.
def main() -> None:
    rows = load_records()
    output = compare_trends(rows)
    save_report(output)

    print(f"  {output['n']} completed translation pairs; authors: {output['authors']}.")
    for label, key in [("Unadjusted", "unadjusted"), ("Source-adjusted", "adjusted")]:
        result = output[key]
        lower_bound, upper_bound = result["author_bootstrap_95_ci"]
        print(
            f"  {label}: {result['slope_per_decade']:+.3f} chrF points per decade "
            f"(95% CI {lower_bound:+.3f} to {upper_bound:+.3f})."
        )
    print("  Report: results/source_adjusted_similarity.md")
    print("  Data: results/data/source_adjusted_similarity.json")


# Run the source adjustment when this file is executed directly.
if __name__ == "__main__":
    main()
