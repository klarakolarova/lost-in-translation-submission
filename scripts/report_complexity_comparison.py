"""Present the German complexity comparison as a table and Figure 2.

Read the measurements and bootstrap intervals saved by
compare_translation_complexity.py.
It shows raw differences, differences relative to the official German mean,
and average differences within three periods. It also reports the two measures
whose intervals include zero and explains the Zipf frequency difference.

Outputs are saved to results/translation_complexity_summary.md and
results/figures/complexity_differences.png.
"""

# Import tools for reading results, calculating averages and plotting.
from pathlib import Path
from statistics import mean
import json
import matplotlib

matplotlib.use("Agg")  # Save figures without opening a plot window.
import matplotlib.pyplot as plt

from linguistic_measures import REPORTED_MEASURES

# Set the input and output locations relative to the project.
ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PROC = RESULTS / "data"
REPORT = RESULTS / "translation_complexity_summary.md"
FIGURE = RESULTS / "figures/complexity_differences.png"

# Include two additional comparisons alongside the seven figure measures.
ADDITIONAL_MEASURES = [
    ("mean_dependency_distance", "Mean dependency distance"),
    ("lexical_density_percent", "Lexical density"),
]
PERIODS = [(2000, 2008), (2009, 2016), (2017, 2025)]
COLOURS = {"Syntax": "#2a6f97", "Vocabulary": "#c26a1b", "Readability": "#444444"}


# Retrieve valid machine-minus-official differences, optionally for a subset.
def paired_differences(
    paired_records: list[tuple], key: str, document_ids: set | None = None
) -> list[float]:
    return [
        generated[key] - official[key]
        for document_id, official, generated in paired_records
        if official.get(key) is not None
        and generated.get(key) is not None
        and (document_ids is None or document_id in document_ids)
    ]


# Save the comparison table and return the values needed for the figure.
def save_report(
    results: dict, paired_records: list[tuple], year_by_motion: dict, report_path: Path | None = None, author_check: bool = True
) -> list[tuple]:
    lines = [
        "# Translation complexity: main results",
        "",
        f"Comparison of {len(paired_records)} translation pairs from motions classified as "
        "French-authored. Differences are calculated as machine minus official German.",
        "",
        "This comparison asks whether the machine translations use simpler vocabulary and sentence structures than the official translations.",
        "",
        "## Overall differences",
        "",
        "| Measure | Pairs | Difference | 95% confidence interval | Machine higher |",
        "|---|---:|---:|---|---:|",
    ]
    rows = []
    period_rows = []
    relative_rows = []
    for key, label, group in REPORTED_MEASURES:
        differences = paired_differences(paired_records, key)
        summary = results["summary"][key]
        mean_difference = summary["mean_difference"]
        official_mean = summary["official_mean"]
        lower_bound, upper_bound = results["summary"][key]["paired_bootstrap_ci95"]
        higher = sum(difference > 0 for difference in differences)
        period_differences = []
        for start_year, end_year in PERIODS:
            period_ids = {
                document_id
                for document_id, submission_year in year_by_motion.items()
                if start_year <= submission_year <= end_year
            }
            period_differences.append(
                mean(paired_differences(paired_records, key, period_ids))
            )
        rows.append(
            (
                label,
                group,
                mean_difference,
                100 * mean_difference / official_mean,
                100 * lower_bound / official_mean,
                100 * upper_bound / official_mean,
            )
        )
        lines.append(
            f"| {label} | {len(differences)} | {mean_difference:+.3f} | [{lower_bound:+.3f}, {upper_bound:+.3f}] | {higher} of {len(differences)} |"
        )
        period_rows.append(
            f"| {label} | "
            + " | ".join(f"{value:+.3f}" for value in period_differences)
            + " |"
        )
        relative_rows.append(
            f"| {label} | {100 * mean_difference / official_mean:+.1f}% | [{100 * lower_bound / official_mean:+.1f}%, {100 * upper_bound / official_mean:+.1f}%] |"
        )
    lines += [
        "",
        "## Reading the measures",
        "",
        "Tree depth is the maximum word depth in each sentence, averaged across "
        "sentences within each text. Clause-marker rates count grammatical markers "
        "per 100 alphabetic words, rather than complete clauses.",
        "",
        f"MATTR measures lexical variety in 50-word windows; {len(paired_records) - results['summary']['mattr_50']['paired_count']} pairs are too short for this measure. Higher LIX indicates harder-to-read text.",
        "",
        "## Differences by period",
        "",
        "The three period columns show mean paired differences within each period; "
        "they do not test whether the periods differ.",
        "",
        "| Measure | " + " | ".join(f"{start}-{end}" for start, end in PERIODS) + " |",
        "|---|" + "---:|" * len(PERIODS),
        *period_rows,
        "",
        "## Relative differences used in the figure",
        "",
        "Percentage differences in Zipf scores provide a common plotting scale, "
        "not percentage changes in word frequency. Zipf is logarithmic; the ratio "
        "below expresses the difference on the frequency scale.",
    ]
    zipf_difference = results["summary"]["mean_content_word_zipf"]["mean_difference"]
    lines += [
        "",
        f"A Zipf difference of {zipf_difference:+.3f} corresponds to a {10 ** zipf_difference:.2f}-fold geometric mean frequency ratio on the scored scale.",
        "",
        "| Measure | % of official mean | 95% confidence interval |",
        "|---|---:|---|",
        *relative_rows,
        "",
        "## Additional measures",
        "",
        "Additional comparisons; an interval including zero indicates no clear evidence of a difference:",
        "",
    ]
    for key, label in ADDITIONAL_MEASURES:
        lower_bound, upper_bound = results["summary"][key]["paired_bootstrap_ci95"]
        lines.append(
            f"- {label}: {results['summary'][key]['mean_difference']:+.3f} [{lower_bound:+.3f}, {upper_bound:+.3f}]"
        )
    lines += [
        "",
        "## Method and related results",
        "",
        results["uncertainty"],
        "",
        ("See the [detailed results](translation_complexity_details.md) for both versions’ means and the [author-dependence check](complexity_author_dependence.md) for repeated authors." if author_check else "See the [detailed results](translation_complexity_details.md) for both versions’ means. Author-adjusted mixed models and multiple-comparison correction have not been repeated for this sample."),
        "",
        "![Differences in linguistic complexity](figures/complexity_differences.png)",
    ]
    RESULTS.mkdir(exist_ok=True)
    (report_path or REPORT).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows


# Plot the relative differences with raw differences beside each interval.
def save_figure(rows: list[tuple], figure_path: Path | None = None) -> None:
    figure, axis = plt.subplots(figsize=(6.3, 2.6))
    for position, (
        label,
        group,
        mean_difference,
        percent_difference,
        percent_lower,
        percent_upper,
    ) in enumerate(reversed(rows)):
        colour = COLOURS[group]
        axis.errorbar(
            percent_difference,
            position,
            xerr=[
                [percent_difference - percent_lower],
                [percent_upper - percent_difference],
            ],
            fmt="o",
            color=colour,
            capsize=3,
            ms=6,
        )
        unit = {
            "Words per sentence": " words",
            "Mean max. sentence depth": " levels",
            "Word frequency (Zipf)": " Zipf",
            "Readability index (LIX)": " points",
        }.get(label, "")
        annotation = (
            f"{mean_difference:+.2f}{unit} ({percent_difference:+.1f}%)"
            if abs(mean_difference) >= 0.01
            else f"{mean_difference:+.3f} ({percent_difference:+.1f}%)"
        )
        axis.annotate(
            annotation,
            (percent_upper, position),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            ha="left",
            fontsize=8,
            color=colour,
            bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"),
        )
    axis.set_yticks(
        range(len(rows)), [record[0] for record in reversed(rows)], fontsize=8.5
    )
    axis.axvline(0, color="#999999", lw=0.8)
    axis.set_xlim(-12, 46)
    axis.set_xlabel(
        "Machine minus official German (% of official mean), 95% CI", fontsize=8.5
    )
    for group_name, colour in COLOURS.items():
        axis.plot([], [], "o-", color=colour, label=group_name)
    axis.legend(loc="lower right", fontsize=8, frameon=False)
    for spine in ("top", "right"):
        axis.spines[spine].set_visible(False)
    figure.tight_layout()
    figure_path = figure_path or FIGURE
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(figure_path, dpi=300, bbox_inches="tight")
    plt.close(figure)


# Load the saved results and create the table and figure.
def main() -> None:
    results = json.loads(
        (PROC / "translation_complexity.json").read_text(encoding="utf-8")
    )
    year_by_motion = {
        record["document_id"]: int(record["year"])
        for record in json.loads(
            (PROC / "validated_sample.json").read_text(encoding="utf-8")
        )["records"]
    }
    paired_records = [
        (record["document_id"], record["official"], record["generated"])
        for record in results["records"]
    ]

    rows = save_report(results, paired_records, year_by_motion)
    save_figure(rows)

    # Print a short summary and output locations.
    print(
        f"  {len(paired_records)} completed pairs; {len(REPORTED_MEASURES)} measures shown in the figure."
    )
    print("  Report: results/translation_complexity_summary.md")
    print("  Figure: results/figures/complexity_differences.png")


# Create the table and figure when this file is executed directly.
if __name__ == "__main__":
    main()
