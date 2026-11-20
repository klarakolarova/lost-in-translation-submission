"""Compare French sentence counts with official and machine German translations.

The script counts exact sentence-count matches for the 259 completed triples.
It also saves word counts for the later source-adjusted analysis and checks
German counts against the complexity results. Equal counts do not necessarily
mean that sentence boundaries or meanings match.
"""

# Import tools for tokenization, counting and saved data.
from pathlib import Path
import json

import spacy

from linguistic_measures import add_abbreviation_rules, paragraph_boundaries

# Set the input and output folders relative to the project.
ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "data"
RESULTS = ROOT / "results"
DATA = RESULTS / "data"
FIELDS = {
    "source": "input_fr",
    "official": "reference_de",
    "generated": "translation_de",
}


# Build a language-specific tokenizer using the shared sentence-boundary rules.
def pipeline(language: str, texts: list[str]):
    nlp = spacy.blank(language)
    add_abbreviation_rules(nlp, texts)
    nlp.add_pipe("sentencizer", config={"punct_chars": [".", "!", "?"]})
    return nlp


# Count words and nonempty sentences, excluding punctuation and whitespace.
def measure(nlp, text: str) -> dict:
    doc = nlp(text)
    paragraph_boundaries(doc)
    sentences = []
    for sentence in doc.sents:
        count = sum(not token.is_punct and not token.is_space for token in sentence)
        if count:
            sentences.append(count)
    words = sum(sentences)
    assert sentences and words
    return {
        "sentence_count": len(sentences),
        "word_count": words,
    }


# Count how often each German version has the same sentence count as the French source.
def summarize(records: list[dict]) -> dict:
    return {
        "n": len(records),
        **{
            version: {
                "exact_source_count_matches": sum(
                    row[version]["sentence_count"] == row["source"]["sentence_count"]
                    for row in records
                )
            }
            for version in ("official", "generated")
        },
    }


# Apply the same counting rules to each source and its two translations.
def measure_versions(rows: list[dict], french_pipeline, german_pipeline) -> list[dict]:
    records = []
    for row in rows:
        record = {"document_id": row["document_id"], "year": row["year"]}
        for version, field in FIELDS.items():
            record[version] = measure(
                french_pipeline if version == "source" else german_pipeline, row[field]
            )
        records.append(record)
    return records


# Compare German counts with the saved complexity measurements.
def compare_german_counts(records: list[dict]) -> list[dict]:
    saved = {
        record["document_id"]: record
        for record in json.loads(
            (DATA / "translation_complexity.json").read_text(encoding="utf-8")
        )["records"]
    }
    mismatches = []
    for record in records:
        for version in ["official", "generated"]:
            for metric in ["sentence_count", "word_count"]:
                if (
                    record[version][metric]
                    != saved[record["document_id"]][version][metric]
                ):
                    mismatches.append(
                        {
                            "document_id": record["document_id"],
                            "version": version,
                            "metric": metric,
                            "new": record[version][metric],
                            "saved": saved[record["document_id"]][version][metric],
                        }
                    )
    return mismatches


# Save the sentence-count comparison and the German-count consistency check.
def save_report(output: dict, mismatches: list[dict]) -> None:
    summary = output["analyses"]["punctuation_and_lines"]["summary"]
    lines = [
        "# Preservation of French sentence counts",
        "",
        f"Comparison of {summary['n']} completed French–German translation triples. "
        "Both German versions use the same counting rules as the French source, "
        "with language-specific tokenizers and sentence boundaries at punctuation and nonempty lines.",
        "",
        "This comparison checks whether the machine output follows the French source’s sentence count more closely than the official translation does.",
        "",
        "## Results",
        "",
        "| German version | Matches French sentence count | Percentage |",
        "|---|---:|---:|",
    ]
    for version, label in (("official", "Official"), ("generated", "Machine")):
        matches = summary[version]["exact_source_count_matches"]
        lines.append(
            f"| {label} | {matches}/{summary['n']} | {100 * matches / summary['n']:.1f}% |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "Equal sentence counts suggest count preservation, but do not establish "
        "matching boundaries or preservation of meaning. Abbreviations and numbered "
        "lists can affect rule-based sentence counts.",
        "",
        "## Consistency check and data",
        "",
        f"German count mismatches against the complexity results: {len(mismatches)}.",
        "Sentence and word counts are saved in [source_sentence_counts.json](data/source_sentence_counts.json). Word counts also support the [source-adjusted similarity analysis](source_adjusted_similarity.md).",
    ]
    (RESULTS / "source_sentence_counts.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


# Load completed translations, compare counts and save the results.
def main() -> None:
    source = json.loads(
        (INPUTS / "complexity_fr_author_translations.json").read_text(encoding="utf-8")
    )
    rows = source["records"]
    assert len({record["document_id"] for record in rows}) == len(rows)
    assert all(record["finish_reason"] == "stop" for record in rows)
    french_pipeline = pipeline("fr", [record["input_fr"] for record in rows])
    german_pipeline = pipeline(
        "de",
        [
            record[field]
            for record in rows
            for field in ["reference_de", "translation_de"]
        ],
    )
    output = {
        "input": "complexity_fr_author_translations.json",
        "spacy_version": spacy.__version__,
        "excluded_failure_ids": [
            record["document_id"] for record in source.get("failed_records", [])
        ],
        "analyses": {},
    }
    records = measure_versions(rows, french_pipeline, german_pipeline)
    output["analyses"]["punctuation_and_lines"] = {
        "summary": summarize(records),
        "records": records,
    }
    mismatches = compare_german_counts(records)
    output["german_counts_check_against_existing_results"] = mismatches
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "source_sentence_counts.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    save_report(output, mismatches)
    summary = output["analyses"]["punctuation_and_lines"]["summary"]
    print(
        f"  {len(records)} French sources, each with an official and a machine German translation."
    )
    print(
        f"  French sentence count matched by machine in {summary['generated']['exact_source_count_matches']}/{len(records)} texts; "
        f"official in {summary['official']['exact_source_count_matches']}/{len(records)} texts."
    )
    print(
        f"  {len(mismatches)} German sentence counts differ from those used in the complexity analysis."
    )
    print("  Report: results/source_sentence_counts.md")
    print("  Data: results/data/source_sentence_counts.json")


# Run the count comparison when this file is executed directly.
if __name__ == "__main__":
    main()
