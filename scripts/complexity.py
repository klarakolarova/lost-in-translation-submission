from pathlib import Path
import json

import numpy as np

from metrics import score_translations

INPUTS = Path(__file__).resolve().parents[1] / "data"


def complexity(
    project_dir: Path,
    pairs_name: str = "sample.json",
    translations_name: str = "complexity_fr_author_translations.json",
    results_name: str = "complexity_fr_author_results.json",
    report_name: str = "complexity_details.md",
    title: str = "Machine versus official German",
) -> None:
    """Compare completed translations and report failures and paired uncertainty.

    Args:
        project_dir: Project directory containing the fixed sample and outputs.
        pairs_name, translations_name, results_name: files in results/data.
        report_name: Markdown table written to results/.
        title: Heading of the Markdown table.
        The fixed sample contains 260 motions, with 259 completed translations.
    """
    # Check that every selected document has exactly one preserved attempt
    processed = project_dir / "results/data"
    sample = json.loads((processed / pairs_name).read_text(encoding="utf-8"))
    translations = json.loads((INPUTS / translations_name).read_text(encoding="utf-8"))
    expected = {row["document_id"]: row for row in sample["records"]}
    attempts = translations["records"] + translations["failed_records"]
    ids = [row["document_id"] for row in attempts]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError("Translation attempts do not match the complete fixed sample.")
    for row in attempts:
        if any(
            row[key] != value for key, value in expected[row["document_id"]].items()
        ):
            raise ValueError(
                f"Input differs from the fixed sample: {row['document_id']}"
            )

    # Keep the original failed attempts while explicitly analysing completed cases
    score_translations(
        project_dir,
        input_name=translations_name,
        output_name=results_name,
        completed_cases_only=True,
    )
    path = processed / results_name
    results = json.loads(path.read_text(encoding="utf-8"))
    rng = np.random.default_rng(47)

    # Resample document pairs within submission year to retain the sampling design
    for metric, summary in results["summary"].items():
        available = [
            row
            for row in results["records"]
            if row["official"][metric] is not None
            and row["generated"][metric] is not None
        ]
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
        summary["paired_bootstrap_ci95"] = np.quantile(
            bootstrap_sums / len(available), [0.025, 0.975]
        ).tolist()

    results["uncertainty"] = (
        "2000 paired-document bootstrap resamples within submission year, seed 47; observed complete-pair counts retained per year/metric. Percentile intervals are exploratory, without multiplicity correction; they do not capture generation-failure selection, author dependence, semantic errors or parser validity."
    )
    path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        f"# {title}",
        "",
        f"Attempted: {results['attempted_count']}; normally stopped outputs analysed: {results['completed_count']}; flagged failures excluded: {len(results['excluded_failures'])}.",
        "",
        "This is a completed-case analysis. Normal stopping is not evidence of semantic quality. See screening.md for the output-quality review.",
        "",
        "Differences are generated German minus official German. Intervals resample document pairs within submission year (2,000 resamples, seed 47); they are exploratory, not adjusted for testing multiple measures.",
        "",
        "| Measure | Pairs | Official mean | Generated mean | Difference | 95% paired interval | Higher / lower / tied |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for metric, summary in results["summary"].items():
        low, high = summary["paired_bootstrap_ci95"]
        lines.append(
            f"| {metric} | {summary['paired_count']} | {summary['official_mean']:.4f} | {summary['generated_mean']:.4f} | {summary['mean_difference']:+.4f} | [{low:+.4f}, {high:+.4f}] | {summary['generated_higher']} / {summary['generated_lower']} / {summary['ties']} |"
        )
    lines.extend(
        ["", "Excluded generation failures (full attempts remain in the input file):"]
    )
    lines.extend(
        f"- {row['document_id']}: {row['finish_reason']}."
        for row in results["excluded_failures"]
    )
    (project_dir / "results" / report_name).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"Saved completed-case results ({results_name}) and results/{report_name}")


if __name__ == "__main__":
    complexity(Path(__file__).resolve().parents[1])
