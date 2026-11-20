"""Compare French tree depth with tree depth in both German translations.

This script calculates source–translation correlations in mean maximum sentence
depth, then repeats the comparison after adjusting each version for its own
mean sentence length. This checks whether the association extends beyond the
relationship between longer sentences and deeper trees.

It saves the measurements for later analyses and a readable comparison. French
and German use different parser annotation schemes, so correlations describe
text-level associations rather than matching grammatical constructions.
"""

# Import tools for parsing, correlations, linear adjustment and saved data.
from pathlib import Path
import json

import numpy as np
import spacy

from linguistic_measures import load_parser, measure_sentences

# Set the input and output folders relative to the project.
ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "data"
RESULTS = ROOT / "results"
DATA = RESULTS / "data"
VERSIONS = ("source", "official", "generated")
DEPTH = "mean_sentence_tree_depth"


# Reuse the shared sentence measures and retain the three fields needed here.
def measure(doc) -> dict:
    measures = measure_sentences(doc)
    return {
        key: measures[key]
        for key in ("sentence_count", "mean_sentence_words", "mean_sentence_tree_depth")
    }


# Calculate Pearson correlation between two sets of document measurements.
def corr(source_values, target_values) -> float:
    return float(np.corrcoef(source_values, target_values)[0, 1])


# Remove the fitted linear relationship with sentence length, including an intercept.
def residual(values, length):
    design = np.column_stack([np.ones(len(length)), length])
    return values - design @ np.linalg.lstsq(design, values, rcond=None)[0]


# Compare the correlations, keeping all three versions together in each bootstrap draw.
def associations(records: list[dict], adjusted: bool = False) -> dict:
    depths_by_version = {
        version: np.array([record[version][DEPTH] for record in records])
        for version in VERSIONS
    }
    lengths = {
        version: np.array(
            [record[version]["mean_sentence_words"] for record in records]
        )
        for version in VERSIONS
    }

    # Refit the length adjustment within each draw when requested.
    def calculate(indices):
        values = {
            version: (
                residual(depths_by_version[version][indices], lengths[version][indices])
                if adjusted
                else depths_by_version[version][indices]
            )
            for version in VERSIONS
        }
        official_correlation = corr(values["source"], values["official"])
        generated_correlation = corr(values["source"], values["generated"])
        return (
            official_correlation,
            generated_correlation,
            generated_correlation - official_correlation,
        )

    years = np.array([record["year"] for record in records])
    groups = [np.flatnonzero(years == year) for year in np.unique(years)]
    rng = np.random.default_rng(49)
    bootstrap_correlations = np.array(
        [
            calculate(
                np.concatenate(
                    [
                        rng.choice(year_indices, len(year_indices))
                        for year_indices in groups
                    ]
                )
            )
            for _ in range(2000)
        ]
    )
    official_correlation, generated_correlation, correlation_difference = calculate(
        np.arange(len(records))
    )
    return {
        "source_official_r": official_correlation,
        "source_generated_r": generated_correlation,
        "difference_generated_minus_official": correlation_difference,
        "difference_bootstrap_95_ci": np.quantile(
            bootstrap_correlations[:, 2], [0.025, 0.975]
        ).tolist(),
    }


# Parse French sources and join the German measurements by document ID.
def measure_versions(
    rows: list[dict], french_parser, german_results: dict
) -> list[dict]:
    saved_records = german_results["records"]
    german_by_id = {record["document_id"]: record for record in saved_records}
    expected_ids = {row["document_id"] for row in rows}
    if len(german_by_id) != len(saved_records) or set(german_by_id) != expected_ids:
        raise ValueError("Saved German measurements do not match the completed sample")

    records = []
    for row, doc in zip(
        rows, french_parser.pipe((row["input_fr"] for row in rows), batch_size=16)
    ):
        source_measures = measure(doc)
        saved = german_by_id[row["document_id"]]
        records.append(
            {
                "document_id": row["document_id"],
                "year": row["year"],
                "source": source_measures,
                **{
                    version: {
                        metric: saved[version][metric] for metric in source_measures
                    }
                    for version in ("official", "generated")
                },
            }
        )
    print(
        "  French sources parsed; saved German measurements reused.",
        flush=True,
    )
    return records


# Save the raw and length-adjusted correlations with their interpretation.
def save_report(summaries: dict, sample_count: int = 259, output_dir: Path | None = None) -> None:
    output_dir = output_dir or ROOT / "results"
    report = [
        "# Association between French and German sentence depth",
        "",
        f"This exploratory comparison uses {sample_count} French sources and their two German versions to assess how closely sentence depth varies with the source. German measurements are reused from the complexity analysis.",
        "",
        "French: fr_core_news_sm 3.8.0 (UD Sequoia). German: de_core_news_sm 3.8.0 (TIGER/Tiger2Dep). Different annotation schemes prevent interpreting raw cross-language depth gaps as structural preservation.",
        "",
        "## Results",
        "",
        "Pearson’s r measures how closely depth varies across documents: a higher positive value indicates a stronger association. The difference is the machine correlation minus the official correlation.",
        "",
        "| Comparison | French–official correlation | French–machine correlation | Difference [95% confidence interval] |",
        "|---|---:|---:|---|",
    ]
    for metric, metric_summary in summaries.items():
        for label in ["raw", "length_adjusted"]:
            association = metric_summary[label]
            lower_bound, upper_bound = association["difference_bootstrap_95_ci"]
            report.append(
                f"| {'Unadjusted sentence depth' if label == 'raw' else 'Sentence depth adjusted for length'} | {association['source_official_r']:.3f} | {association['source_generated_r']:.3f} | {association['difference_generated_minus_official']:+.3f} [{lower_bound:+.3f}, {upper_bound:+.3f}] |"
            )
    report += [
        "",
        "## Method and interpretation",
        "",
        "Depth is the maximum word depth in each sentence, averaged within each text. This tests an association with the source, rather than directly comparing French and German depth levels.",
        "",
        "- Correlations describe document-level covariation, not sentence-aligned syntactic equivalence or causality.",
        "- Length adjustment removes a fitted linear association with mean sentence length separately in each version; it does not remove every confound.",
        "- Exploratory intervals resample paired documents within year; repeated authors and multiple comparisons are not accounted for.",
        "",
    ]
    (output_dir / "source_tree_depth.md").write_text(
        "\n".join(report), encoding="utf-8"
    )


# Load the completed triples, compare tree depth and save the outputs.
def main() -> None:
    rows = json.loads(
        (INPUTS / "complexity_fr_author_translations.json").read_text(encoding="utf-8")
    )["records"]
    if len({record["document_id"] for record in rows}) != len(rows):
        raise ValueError("Duplicate document IDs in completed sample")
    if any(record["finish_reason"] != "stop" for record in rows):
        raise ValueError("Incomplete translation in completed sample")
    german_results = json.loads(
        (DATA / "translation_complexity.json").read_text(encoding="utf-8")
    )
    french_parser = load_parser(
        [record["input_fr"] for record in rows], model_name="fr_core_news_sm"
    )
    records = measure_versions(rows, french_parser, german_results)
    summaries = {
        DEPTH: {
            "raw": associations(records),
            "length_adjusted": associations(records, adjusted=True),
        }
    }
    output = {
        "n": len(records),
        "spacy_version": spacy.__version__,
        "parsers": {
            "fr_core_news_sm": {
                "version": french_parser.meta["version"],
                "sources": french_parser.meta["sources"],
            },
            german_results["parser"]: {
                "version": german_results["parser_version"],
                "sources": german_results["parser_sources"],
            },
        },
        "definitions": {
            "depth": "Mean sentence maximum nonpunctuation ancestor count, root=0.",
            "adjustment": "Within each language/version, regress each metric on its own mean sentence length with intercept; correlate residuals. Refit on every bootstrap sample.",
            "uncertainty": "2000 paired document bootstrap draws within year, seed49. No author clustering or multiplicity adjustment.",
        },
        "summary": summaries,
        "records": records,
    }
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "source_tree_depth.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    save_report(summaries)
    for label, values in summaries[DEPTH].items():
        print(
            f"  Source–German depth correlation ({'before length adjustment' if label == 'raw' else 'after length adjustment'}): "
            f"official {values['source_official_r']:.3f}; "
            f"machine {values['source_generated_r']:.3f}."
        )
    print("  Report: results/source_tree_depth.md")
    print("  Data: results/data/source_tree_depth.json")


# Run the syntax comparison when this file is executed directly.
if __name__ == "__main__":
    main()
