"""Compare machine and official German translations across submission years.

Calculate chrF and BLEU for each complete translation pair, summarise scores
by period and estimate the chrF trend over time. Use document bootstrap
resamples to estimate uncertainty in period means and the trend.

Save per-document scores, a summary table and a figure in results/.
"""

# Import tools for scoring translations, resampling and saving results.
from pathlib import Path
import csv
import json
import random
import statistics as st

import sacrebleu

# Set input and output locations relative to the project.
ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "data/complexity_fr_author_translations.json"
OUT = ROOT / "results"

# Group years for the figure and use a fixed seed for bootstrap intervals.
PERIODS = [
    (2000, 2004),
    (2005, 2009),
    (2010, 2014),
    (2015, 2019),
    (2020, 2022),
    (2023, 2025),
]
N_BOOT, SEED = 2000, 47


# Estimate a 95% interval by resampling documents with replacement.
def bootstrap_ci(values: list, stat=st.mean) -> tuple[float, float]:
    rng = random.Random(SEED)
    bootstrap_estimates = sorted(
        stat(rng.choices(values, k=len(values))) for _ in range(N_BOOT)
    )
    return (
        bootstrap_estimates[int(0.025 * N_BOOT)],
        bootstrap_estimates[int(0.975 * N_BOOT) - 1],
    )


# Calculate the linear change in similarity per year.
def slope(points: list[tuple[int, float]]) -> float:
    mean_year = st.mean(year for year, _ in points)
    mean_score = st.mean(score for _, score in points)
    return sum(
        (year - mean_year) * (score - mean_score) for year, score in points
    ) / sum((year - mean_year) ** 2 for year, _ in points)


# Score each complete document using machine German against official German.
def score_pairs(records: list[dict]) -> list[dict]:
    rows = []
    for record in records:
        rows.append(
            {
                "document_id": record["document_id"],
                "year": int(record["year"]),
                "chrf": sacrebleu.sentence_chrf(
                    record["translation_de"], [record["reference_de"]]
                ).score,
                "bleu": sacrebleu.sentence_bleu(
                    record["translation_de"], [record["reference_de"]]
                ).score,
            }
        )
    return rows


# Calculate period means and bootstrap intervals for chrF.
def summarise_periods(rows: list[dict]) -> list[dict]:
    table = []
    for start_year, end_year in PERIODS:
        period_rows = [
            record for record in rows if start_year <= record["year"] <= end_year
        ]
        chrf_scores = [record["chrf"] for record in period_rows]
        lower_bound, upper_bound = bootstrap_ci(chrf_scores)
        table.append(
            {
                "period": f"{start_year}-{end_year}",
                "n": len(period_rows),
                "chrf": st.mean(chrf_scores),
                "lo": lower_bound,
                "hi": upper_bound,
                "bleu": st.mean(record["bleu"] for record in period_rows),
            }
        )

    return table


# Estimate the chrF trend and its bootstrap interval in points per decade.
def estimate_trend(rows: list[dict]) -> tuple[float, float, float]:
    points = [(record["year"], record["chrf"]) for record in rows]
    lower_bound, upper_bound = bootstrap_ci(points, stat=slope)
    return 10 * slope(points), 10 * lower_bound, 10 * upper_bound


# Save per-document scores and the summary of period means and the trend.
def save_report(rows: list[dict], table: list[dict], trend: tuple) -> None:
    OUT.mkdir(exist_ok=True)
    with open(
        OUT / "translation_similarity.csv", "w", newline="", encoding="utf-8"
    ) as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Similarity of official translations to machine output",
        "",
        f"French-authored sample, {len(rows)} completed pairs. chrF/BLEU: machine vs official German "
        f"(sacreBLEU, scored separately for each complete document). 95% intervals: {N_BOOT} document bootstrap resamples, seed {SEED}.",
        "",
        "chrF compares overlapping character sequences; BLEU compares overlapping word sequences. Both are reported on a 0–100 scale, with higher scores indicating greater similarity to the official German wording, not necessarily a better translation.",
        "",
        "## Similarity by period",
        "",
        "| Period | Texts | Mean chrF | 95% confidence interval | Mean BLEU |",
        "|---|---:|---:|---|---:|",
    ]
    lines += [
        f"| {period['period']} | {period['n']} | {period['chrf']:.1f} | [{period['lo']:.1f}, {period['hi']:.1f}] | {period['bleu']:.1f} |"
        for period in table
    ]
    lines += [
        "",
        "## Trend over time",
        "",
        f"Linear trend: {trend[0]:+.2f} chrF per decade, 95% CI [{trend[1]:+.2f}, {trend[2]:+.2f}].",
        "",
        "## Interpretation",
        "",
        "Increasing similarity is consistent with official translations increasingly being produced "
        "from MT output. However, the same pattern could arise if the model had seen recent official "
        "translations during training; our data cannot separate these explanations.",
        "",
        "See the [source-adjusted analysis](source_adjusted_similarity.md) for a check accounting for changes in the French inputs. Document scores are in [translation_similarity.csv](translation_similarity.csv).",
        "",
        "![Translation similarity over time](figures/translation_similarity.png)",
    ]
    (OUT / "translation_similarity.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


# Plot chrF period means with intervals and BLEU on a separate axis.
def save_figure(table: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, chrf_axis = plt.subplots(figsize=(6.4, 2.9))
    period_positions = list(range(len(table)))
    chrf_axis.errorbar(
        period_positions,
        [period["chrf"] for period in table],
        yerr=[
            [period["chrf"] - period["lo"] for period in table],
            [period["hi"] - period["chrf"] for period in table],
        ],
        fmt="o-",
        color="#1f5f8b",
        capsize=3,
        lw=1.5,
        ms=5,
        label="chrF (left axis)",
    )
    chrf_axis.set_xticks(
        period_positions,
        [f"{period['period']}\n(n={period['n']})" for period in table],
        fontsize=8,
    )
    chrf_axis.set_ylabel("chrF, official vs machine", fontsize=8.5)
    chrf_axis.tick_params(axis="y", labelsize=8)
    bleu_axis = chrf_axis.twinx()
    bleu_axis.plot(
        period_positions,
        [period["bleu"] for period in table],
        "s--",
        color="#b0b0b0",
        ms=4,
        lw=1,
        label="BLEU (right axis)",
    )
    bleu_axis.set_ylabel("BLEU", fontsize=8.5, color="#777777")
    bleu_axis.tick_params(axis="y", labelsize=8, colors="#777777")
    for axis in (chrf_axis, bleu_axis):
        axis.spines["top"].set_visible(False)
    chrf_handles, chrf_labels = chrf_axis.get_legend_handles_labels()
    bleu_handles, bleu_labels = bleu_axis.get_legend_handles_labels()
    chrf_axis.legend(
        chrf_handles + bleu_handles,
        chrf_labels + bleu_labels,
        fontsize=7.5,
        loc="upper left",
        frameon=False,
    )
    figure.tight_layout()
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    figure.savefig(OUT / "figures/translation_similarity.png", dpi=220)
    plt.close(figure)


# Load translations, calculate similarity and save the table and figure.
def main() -> None:
    records = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))["records"]
    rows = score_pairs(records)
    table = summarise_periods(rows)
    trend = estimate_trend(rows)
    save_report(rows, table, trend)
    save_figure(table)

    print(f"  {len(rows)} completed pairs, summarised in {len(table)} periods.")
    print(
        f"  Similarity trend: {trend[0]:+.2f} chrF points per decade (95% CI {trend[1]:+.2f} to {trend[2]:+.2f})."
    )
    print("  Report: results/translation_similarity.md")
    print(
        "  Data: results/translation_similarity.csv (scores for each translation pair)"
    )
    print("  Figure: results/figures/translation_similarity.png")


# Run the similarity analysis when this file is executed directly.
if __name__ == "__main__":
    main()
