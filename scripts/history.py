"""Reproduce the historical appendix from saved scores; --rescore reparses the corpus."""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path
from statistics import mean, median
import gzip
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import spacy

from metrics import load_parser, measure_text

INPUTS = Path(__file__).resolve().parents[1] / "data"

PROC = Path("results/data")
PERIODS = [
    (2000, 2004),
    (2005, 2009),
    (2010, 2014),
    (2015, 2019),
    (2020, 2024),
    (2025, 2025),
]
METRICS = [
    ("mean_sentence_words", "Words per sentence"),
    ("mean_content_word_zipf", "Content-word Zipf"),
    ("mattr_50", "MATTR50"),
    ("lix", "LIX"),
]


def main() -> None:
    hist = load_scores()
    recs = hist["records"]
    lines = [
        "# Appendix A: official German justifications 2000-2025",
        "",
        f"Documents scored: {len(recs):,}",
        "",
        "| Period | Documents | " + " | ".join(l for _, l in METRICS) + " |",
        "|---|---:|" + "---:|" * len(METRICS),
    ]
    for a, b in PERIODS:
        rows = [r["official"] for r in recs if a <= r["year"] <= b]
        cells = [
            f"{mean(v for r in rows if (v := r.get(k)) is not None):.2f}"
            for k, _ in METRICS
        ]
        lines.append(f"| {a}-{b} | {len(rows):,} | " + " | ".join(cells) + " |")

    by_year = {y["year"]: y["metrics"] for y in hist["years"]}
    lines += [
        "",
        "2025 vs 2024 (yearly mean, 95% bootstrap interval from history.py):",
        "",
    ]
    for k, label in METRICS:
        m24, m25 = by_year[2024][k], by_year[2025][k]
        overlap = not (
            m25["bootstrap_mean_ci95"][0] > m24["bootstrap_mean_ci95"][1]
            or m25["bootstrap_mean_ci95"][1] < m24["bootstrap_mean_ci95"][0]
        )
        lines.append(
            f"- {label}: 2024 {m24['mean']:.2f} {[round(x, 2) for x in m24['bootstrap_mean_ci95']]}, "
            f"2025 {m25['mean']:.2f} {[round(x, 2) for x in m25['bootstrap_mean_ci95']]}; "
            f"intervals overlap: {overlap}"
        )

    cov = {
        y["year"]: y
        for y in json.loads(
            (INPUTS / "motion_coverage.json").read_text(encoding="utf-8")
        )["years"]
    }
    lines += ["", "Motions without a German justification:", ""]
    for y in (2000, 2025):
        c = cov[y]
        lines.append(
            f"- {y}: {c['de_records'] - c['de_with_justification']} of {c['de_records']} "
            f"({100 * (1 - c['de_with_justification'] / c['de_records']):.0f}%)"
        )
    Path("results").mkdir(exist_ok=True)
    Path("results/historical_summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))


def score_history(project_dir: Path) -> None:
    """Measure official German justifications and summarise each year.

    Args:
        project_dir: Project directory containing the audited motion corpus.
    """
    # Load eligible texts and the same parser used for paired comparisons
    processed = project_dir / "results/data"
    corpus = json.load(
        gzip.open(INPUTS / "motion_corpus.json.gz", "rt", encoding="utf-8")
    )
    if corpus["completed_through"] != 2025:
        raise ValueError("Complete the coverage audit before scoring history.")
    source = [row for row in corpus["records"] if not row["exclusion_de"]]
    nlp = load_parser([row["reference_de"] for row in source])
    records = []
    yearly = []
    rng = np.random.default_rng(46)

    # Parse full documents and retain year-level checkpoints
    for year in range(2000, 2026):
        rows = [row for row in source if row["year"] == year]
        measurements = []
        unique_measurements = []
        seen_texts = set()
        for row, doc in zip(
            rows, nlp.pipe([row["reference_de"] for row in rows], batch_size=16)
        ):
            measures = measure_text(doc)
            measurements.append(measures)
            if row["reference_de"] not in seen_texts:
                unique_measurements.append(measures)
                seen_texts.add(row["reference_de"])
            records.append(
                {"document_id": row["document_id"], "year": year, "official": measures}
            )

        # Report distributions and document-level uncertainty for fixed measures
        summary = {}
        for metric, value in measurements[0].items():
            if value is not None and not isinstance(value, (int, float)):
                continue
            values = [row[metric] for row in measurements if row[metric] is not None]
            unique_values = [
                row[metric] for row in unique_measurements if row[metric] is not None
            ]
            if not values:
                continue
            bootstrap_means = rng.choice(
                values, size=(2000, len(values)), replace=True
            ).mean(axis=1)
            summary[metric] = {
                "available_documents": len(values),
                "mean": mean(values),
                "median": median(values),
                "q25": float(np.quantile(values, 0.25)),
                "q75": float(np.quantile(values, 0.75)),
                "bootstrap_mean_ci95": np.quantile(
                    bootstrap_means, [0.025, 0.975]
                ).tolist(),
                "deduplicated_documents": len(unique_values),
                "deduplicated_mean": mean(unique_values),
            }
        yearly.append({"year": year, "documents": len(rows), "metrics": summary})
        output = {
            "input_file": "motion_corpus.json",
            "completed_through": year,
            "spacy_version": spacy.__version__,
            "parser": "de_core_news_sm",
            "parser_version": nlp.meta["version"],
            "wordfreq_version": version("wordfreq"),
            "method": "Same load_parser and measure_text functions as metrics.py; full official German ReasonText; flagged administrative entries excluded; each document weighted equally.",
            "uncertainty": "2000 document bootstrap resamples per metric/year, seed 46. Descriptive corpus means are exact for included records; intervals describe hypothetical document resampling, not missing-archive or measurement uncertainty. Author/topic dependence is not modelled. Exact-text deduplicated means within each year are a separate sensitivity check.",
            "years": yearly,
            "records": records,
        }
        path = processed / "historical_complexity.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(path)
        print(f"Saved {year}: {len(rows)} documents", flush=True)


def plot_history(project_dir: Path) -> None:
    """Plot yearly means and exact-text deduplication sensitivity.

    Args:
        project_dir: Project directory containing completed historical scores.
    """
    # Show distinct dimensions without a composite complexity score
    data = load_scores()
    if data["completed_through"] != 2025:
        raise ValueError("Complete all historical years before plotting.")
    metrics = {
        "mean_content_word_zipf": "Content-word frequency (Zipf)",
        "mattr_50": "Lexical diversity (MATTR, 50 words)",
        "subordinators_per_100_words": "Subordinators per 100 words",
        "relative_markers_per_100_words": "Relative markers per 100 words",
        "mean_sentence_words": "Words per sentence",
        "lix": "LIX readability proxy",
    }
    figure, axes = plt.subplots(3, 2, figsize=(11, 9))
    years = [row["year"] for row in data["years"]]
    for axis, (metric, label) in zip(axes.flat, metrics.items()):
        values = [row["metrics"][metric] for row in data["years"]]
        axis.plot(
            years,
            [row["mean"] for row in values],
            color="#21618c",
            label="All eligible motions",
        )
        axis.plot(
            years,
            [row["deduplicated_mean"] for row in values],
            color="#bf6516",
            linestyle="--",
            label="Unique texts within year",
        )
        axis.fill_between(
            years,
            [row["bootstrap_mean_ci95"][0] for row in values],
            [row["bootstrap_mean_ci95"][1] for row in values],
            color="#21618c",
            alpha=0.12,
        )
        axis.set_title(label, fontsize=11)
        axis.set_xticks([2000, 2005, 2010, 2015, 2020, 2025])
        axis.grid(alpha=0.2)
    axes[0, 0].legend(fontsize=8)
    figure.suptitle("Official German motion justifications, 2000-2025", fontsize=15)
    figure.text(
        0.5,
        0.015,
        "Each document has equal weight. Shading: 95% document-bootstrap intervals; author/topic dependence is not modelled.\nDescriptive corpus comparison, not an estimate of an AI effect. Original submission languages are unverified.",
        ha="center",
        fontsize=9,
    )
    figure.tight_layout(rect=(0, 0.06, 1, 0.96))
    output_dir = project_dir / "results/figures"
    output_dir.mkdir(exist_ok=True)
    figure.savefig(output_dir / "historical_complexity.png", dpi=180)
    plt.close(figure)


def load_scores():
    path = Path("results/data/historical_complexity.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    with gzip.open(INPUTS / "historical_scores.json.gz", "rt", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reproduce the historical appendix.")
    parser.add_argument(
        "--rescore",
        action="store_true",
        help="Reparse all 10,581 texts instead of using the saved scores",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.rescore:
        score_history(root)
    main()
    plot_history(root)
