"""This script compares linguistic complexity in machine and official German translations.

It checks the saved translation attempts against the fixed sample and uses
linguistic_measures.py to calculate measures for the 259 completed translation pairs.

It estimates 95% confidence intervals for the mean paired differences by
resampling motion pairs within each year, then saves the results and a summary.
"""

# Import tools for file handling, resampling and the shared measurement and input checks.
from pathlib import Path
import json
import numpy as np
from linguistic_measures import score_translations, REPORTED_MEASURES
from validate_sample import check_translation_inputs

# Set the input and output locations relative to the project.
ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "results/data"
RESULTS = ROOT / "results"
SCORES = PROC / "translation_complexity.json"
REPORT = RESULTS / "translation_complexity_details.md"


# Add confidence intervals for mean machine-minus-official differences to the results.
def add_bootstrap_intervals(results: dict, selected: list[dict]) -> None:
    expected = {row["document_id"]: row for row in selected}

    # Resample paired differences within each year, keeping its observed pair count.
    for metric, summary in results["summary"].items():
        # Reset the seed so adding or removing another measure cannot change this interval.
        rng = np.random.default_rng(47)
        available = [
            row
            for row in results["records"]
            if row["official"][metric] is not None
            and row["generated"][metric] is not None
        ]
        # Accumulate the yearly sums for each of the 2,000 resamples.
        bootstrap_sums = np.zeros(2000)
        for year in range(2000, 2026):
            differences = [
                row["generated"][metric] - row["official"][metric]
                for row in available
                if expected[row["document_id"]]["year"] == year
            ]
            if differences:
                bootstrap_sums += rng.choice(
                    differences, size=(2000, len(differences)), replace=True
                ).sum(axis=1)
        # Divide by the total pair count and take the central 95% of resampled means.
        summary["paired_bootstrap_ci95"] = np.quantile(
            bootstrap_sums / len(available), [0.025, 0.975]
        ).tolist()

    results["uncertainty"] = (
        "These intervals estimate sampling uncertainty in the average difference between machine and official German. We resample motion pairs within each year to preserve the sample’s yearly composition. We use 2,000 resamples with seed 47 reset for each measure for reproducibility and take the middle 95% of the resampled mean differences. Author dependence and multiple comparisons are examined separately in the robustness analysis."
    )


# Save the detailed comparison, interval interpretation and excluded failures.
def save_report(results: dict) -> None:
    labels = {key: label for key, label, _ in REPORTED_MEASURES}
    labels.update(
        {
            "mean_dependency_distance": "Mean dependency distance",
            "mean_covered_content_word_zipf": "Word frequency (Zipf; zero scores excluded)",
            "lexical_density_percent": "Lexical density (%)",
        }
    )
    lines = [
        "# Translation complexity: detailed results",
        "",
        f"Attempted: {results['attempted_count']}; normally stopped outputs analysed: {results['completed_count']}; flagged failures excluded: {len(results['excluded_failures'])}.",
        "",
        "This table provides the full measurements behind the [complexity summary](translation_complexity_summary.md). It compares completed translations of motions classified as French-authored. See [translation screening](translation_screening.md) for the quality checks.",
        "",
        "Differences are machine German minus official German. The 95% intervals indicate sampling uncertainty in these average differences, estimated using 2,000 bootstrap resamples of motion pairs within each year.",
        "",
        "## Results",
        "",
        "Higher / lower / tied counts compare the machine value with the official value in each pair. MATTR uses 50-word windows and is available for 257 pairs.",
        "",
        "| Measure | Pairs | Official mean | Machine mean | Difference | 95% confidence interval | Higher / lower / tied |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for metric, summary in results["summary"].items():
        low, high = summary["paired_bootstrap_ci95"]
        lines.append(
            f"| {labels[metric]} | {summary['paired_count']} | {summary['official_mean']:.4f} | {summary['generated_mean']:.4f} | {summary['mean_difference']:+.4f} | [{low:+.4f}, {high:+.4f}] | {summary['generated_higher']} / {summary['generated_lower']} / {summary['ties']} |"
        )
    lines.extend(
        [
            "",
            "## Excluded output",
            "",
            "The following generation reached its output limit. The full attempt remains in the input file.",
            "",
        ]
    )
    lines.extend(
        f"- {row['document_id']}: {row['finish_reason']}."
        for row in results["excluded_failures"]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


# Check the sample, calculate the measures and save the comparison.
def main() -> None:
    sample = json.loads((PROC / "validated_sample.json").read_text(encoding="utf-8"))
    selected = sample["records"]

    # Check the sample validity (defined in validate_sample.py).
    check_translation_inputs(selected)

    # Score completed translations while preserving the failed attempts in the input.
    print(
        "  Calculating measures for each completed translation pair...",
        flush=True,
    )
    results = score_translations(completed_cases_only=True)

    # Add bootstrapping intervals.
    add_bootstrap_intervals(results, selected)
    SCORES.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    save_report(results)

    # Print a short summary and output locations; keep the full table in the report.
    print(
        f"  Analysed: {results['completed_count']} of {results['attempted_count']} pairs; "
        f"excluded failures: {len(results['excluded_failures'])}."
    )
    print("  Report: results/translation_complexity_details.md")
    print("  Data: results/data/translation_complexity.json")


# Run the complexity comparison when this file is executed directly.
if __name__ == "__main__":
    main()
