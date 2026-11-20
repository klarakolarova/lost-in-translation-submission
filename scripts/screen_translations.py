"""Screen machine translations for possible generation and translation problems.

Check output completion, French function words and
repeated phrases. Validate and summarise the saved human assessments of
flagged texts and a fixed random sample of 20 translations.

Save the checks and reading assessments in results/translation_screening.md.
"""

# Import tools for text checks, reproducible sampling and saved annotations.
from collections import Counter
from pathlib import Path
import csv
import json
import random
import re

# Set input and output locations relative to the project.
ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "data/complexity_fr_author_translations.json"
ANNOTATIONS = ROOT / "data/screening_annotations.csv"
OUTPUT = ROOT / "results/translation_screening.md"

# Use frequent French function words to flag possible untranslated passages.
FRENCH_WORDS = set(
    "le la les des du de et est une un que qui dans pour par sur au aux pas ne nous il "
    "elle ce cette ces son sa ses leur".split()
)
SAMPLE_SEED, SAMPLE_SIZE = 2026, 20


# Check completion and flag possible untranslated passages or repetitive output.
def screen_translations(records: list[dict]) -> dict:
    stopped = sum(record["finish_reason"] == "stop" for record in records)
    french_flags, repetition_flags = [], []
    for record in records:
        tokens = re.findall(r"\w+", record["translation_de"].lower())
        if sum(token in FRENCH_WORDS for token in tokens) / max(1, len(tokens)) > 0.05:
            french_flags.append(str(record["document_id"]))
        phrase_counts = Counter(
            tuple(tokens[start_index : start_index + 6])
            for start_index in range(len(tokens) - 5)
        )
        if (
            sum(
                occurrences - 1
                for occurrences in phrase_counts.values()
                if occurrences > 1
            )
            > 3
        ):
            repetition_flags.append(str(record["document_id"]))

    return {
        "stopped": stopped,
        "french_flag": french_flags,
        "repeat_flag": repetition_flags,
    }


# Recreate the reading sample and ensure every selected or flagged text is annotated.
def validate_annotations(records: list[dict], checks: dict) -> tuple[list[str], dict]:
    sample = [
        str(record["document_id"])
        for record in random.Random(SAMPLE_SEED).sample(records, SAMPLE_SIZE)
    ]
    with open(ANNOTATIONS, encoding="utf-8") as file_handle:
        annotations = list(csv.DictReader(file_handle))
    annotations_by_check = {
        check_name: {
            annotation["document_id"]: annotation
            for annotation in annotations
            if annotation["check"] == check_name
        }
        for check_name in ("reading_sample", "repetition_flag", "french_flag")
    }
    for check, expected in (
        ("reading_sample", sample),
        ("repetition_flag", checks["repeat_flag"]),
        ("french_flag", checks["french_flag"]),
    ):
        if set(annotations_by_check[check]) != set(expected):
            raise SystemExit(
                f"Annotations for {check} do not match the texts drawn/flagged: "
                f"missing {sorted(set(expected) - set(annotations_by_check[check]))}, "
                f"extra {sorted(set(annotations_by_check[check]) - set(expected))}"
            )
    return sample, annotations_by_check


# Save the automatic checks alongside the existing human reading assessments.
def save_report(
    data: dict, checks: dict, sample: list[str], annotations_by_check: dict
) -> None:
    records = data["records"]
    stopped = checks["stopped"]
    french_flags, repetition_flags = checks["french_flag"], checks["repeat_flag"]
    judgement_counts = Counter(
        annotation["judgement"]
        for annotation in annotations_by_check["reading_sample"].values()
    )

    lines = [
        "# Translation quality screening",
        "",
        f"Completed outputs: {len(records)}; failed (output limit): {len(data['failed_records'])}.",
        "",
        "This screening checks for generation problems and records a small manual review before interpreting the linguistic comparisons. Automatic flags identify passages to inspect; they are not error judgements.",
        "",
        "## Automatic checks",
        "",
        f"- Stopped normally: {stopped} of {len(records)}.",
        f"- French function-word share > 5%: {len(french_flags)} ({', '.join(french_flags) or '-'}).",
        f"- Repeated 6-grams (> 3 repeats): {len(repetition_flags)} ({', '.join(repetition_flags)}).",
        "",
        "### Review of flagged texts",
        "",
        "The notes below are the saved human annotations.",
        "",
    ]
    for check in ("repetition_flag", "french_flag"):
        for document_id, annotation in sorted(annotations_by_check[check].items()):
            lines.append(
                f"- **{document_id}** ({'repetition' if check == 'repetition_flag' else 'French words'}): {annotation['judgement'].replace('_', ' ')}. {annotation['note']}"
            )
    lines += [
        "",
        "## Manual reading sample",
        "",
        f"The opening approximately 100 words of {SAMPLE_SIZE} randomly selected texts were reviewed (seed {SAMPLE_SEED}). The categories and notes below reproduce the saved annotations; this is a sample review, not a full-document quality score.",
        "",
        "| Recorded assessment | Texts |",
        "|---|---:|",
        f"| No issue recorded | {judgement_counts['ok']} |",
        f"| Minor issue | {judgement_counts['minor']} |",
        f"| Content-changing issue | {judgement_counts['content']} |",
        "",
    ]
    for document_id in sample:
        annotation = annotations_by_check["reading_sample"][document_id]
        lines.append(
            f"- **{document_id}**: { {'ok': 'No issue recorded', 'minor': 'Minor issue', 'content': 'Content-changing issue'}[annotation['judgement']]}"
            + (f". {annotation['note']}" if annotation["note"] else "")
        )
    lines += [
        "",
        "## Annotation source",
        "",
        "The original judgements and notes are in [screening_annotations.csv](../data/screening_annotations.csv).",
    ]
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


# Run screening and print a short summary with the location of the full report.
def main() -> None:
    data = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))
    records = data["records"]
    checks = screen_translations(records)
    sample, annotations = validate_annotations(records, checks)
    save_report(data, checks, sample, annotations)

    print(
        f"  {len(records)} completed translations; failed generations excluded: {len(data['failed_records'])}."
    )
    print(
        f"  Review flags (not confirmed errors): French words: {len(checks['french_flag'])}; repetition flags: {len(checks['repeat_flag'])}."
    )
    print(
        f"  Saved annotations are present for all flagged texts and {len(sample)} sampled translations."
    )
    print("  Report: results/translation_screening.md")


# Run the screening when this file is executed directly.
if __name__ == "__main__":
    main()
