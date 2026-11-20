"""This script loads and checks the fixed motion sample used in the project.

It retrieves the 260 selected motions from the corpus, checks their eligibility
and verifies that there are 10 motions per year from 2000 to 2025.
It also checks that their texts match the saved translation inputs.

The sample is saved to results/data/validated_sample.json for subsequent analyses.
No new motions are selected or translated.
"""

# Import tools for counting, file handling and reading the saved data.
from collections import Counter
from pathlib import Path
import csv
import gzip
import json

# Set the input and output folders relative to the project.
ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "data"
PROC = ROOT / "results/data"


# Check the expected corpus totals; these do not verify every text.
def check_corpus_totals(corpus: list[dict]) -> None:
    # Verify the recorded corpus totals: unique motions, usable German texts and usable text pairs.
    assert len(corpus) == len({record["document_id"] for record in corpus}) == 10622
    assert (
        sum(
            record["exclusion_de"] is None and bool(record["reference_de"])
            for record in corpus
        )
        == 10581
    )
    assert (
        sum(
            record["exclusion_de"] is None
            and record["exclusion_fr"] is None
            and bool(record["reference_de"])
            and bool(record["input_fr"])
            for record in corpus
        )
        == 10573
    )


# Check that saved translation attempts match the selected motions.
def check_translation_inputs(selected: list[dict]) -> None:
    ids = [record["document_id"] for record in selected]
    # Load completed translations and failed attempts for comparison with the fixed sample.
    translations = json.loads(
        (INPUTS / "complexity_fr_author_translations.json").read_text(encoding="utf-8")
    )
    attempts = translations["records"] + translations["failed_records"]

    # Verify that all 260 selected motions are unique and have a saved translation attempt.
    assert len(ids) == len(set(ids)) == len(attempts) == 260
    assert set(ids) == {record["document_id"] for record in attempts}

    # Verify that the texts and metadata saved with each translation attempt match the corpus.
    expected = {record["document_id"]: record for record in selected}
    for record in attempts:
        if any(
            record[field] != value
            for field, value in expected[record["document_id"]].items()
        ):
            raise ValueError(
                f"Translation input differs from corpus: {record['document_id']}"
            )


# Check eligibility and the number of selected motions per year.
def check_sample(selected: list[dict], french_ids: set[int], design: dict) -> None:
    # Exclude the 30 motions used to develop or inspect the measures.
    excluded = set(design["excluded_development_ids"])
    # Check that each motion has both usable texts, a French-classified author and no development exclusion.
    for record in selected:
        if (
            record["exclusion_de"] is not None
            or record["exclusion_fr"] is not None
            or not record["reference_de"]
            or not record["input_fr"]
            or record["document_id"] not in french_ids
            or record["document_id"] in excluded
        ):
            raise ValueError(
                f"Recorded motion is not eligible: {record['document_id']}"
            )

    # Verify that the sample contains exactly 10 motions for each year from 2000 to 2025.
    if Counter(record["year"] for record in selected) != {
        year: design["per_year"] for year in range(2000, 2026)
    }:
        raise ValueError("Recorded sample must contain 10 motions per year, 2000–2025")


# Load the fixed sample, run the checks and save it for later analyses.
def main() -> None:
    # Load the recorded sample design and motion corpus.
    design = json.loads((INPUTS / "sample_design.json").read_text(encoding="utf-8"))
    corpus = json.load(
        gzip.open(INPUTS / "motion_corpus.json.gz", "rt", encoding="utf-8")
    )["records"]

    # Load French-authored motion IDs for the sample eligibility check.
    with (PROC / "french_authored_motions.csv").open(encoding="utf-8") as file_handle:
        french_ids = {
            int(record["document_id"]) for record in csv.DictReader(file_handle)
        }

    check_corpus_totals(corpus)

    # Retrieve the selected motions from the corpus in their recorded order.
    ids = design["selected_ids"]
    corpus_by_id = {record["document_id"]: record for record in corpus}
    selected = [corpus_by_id[document_id] for document_id in ids]

    # Verify sample eligibility and saved translation inputs.
    check_sample(selected, french_ids, design)
    check_translation_inputs(selected)

    # Save the verified sample.
    PROC.mkdir(parents=True, exist_ok=True)
    (PROC / "validated_sample.json").write_text(
        json.dumps({"records": selected}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Print a short summary and output location.
    print(f"  {len(selected)} motions, {design['per_year']} per year (2000–2025).")
    print(
        "  Eligibility, yearly counts, corpus totals and translation inputs all match the saved design."
    )
    print("  Data: results/data/validated_sample.json")


# Run the sample checks when this file is executed directly.
if __name__ == "__main__":
    main()
