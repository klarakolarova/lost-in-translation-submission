"""Compare ß and dash use in machine output and recent official German texts.

Check how special characters appear in the corpus before and from 2023.
For 2023–2025, compare official texts by author language, inspect those
containing ß and summarise dash use by year. Include the machine translations
from the full sample as a comparison.

Save the counts and statistical comparison in results/character_conventions.md.
"""

# Import tools for counting characters, reading the corpus and exact probabilities.
from collections import Counter
from math import comb
from pathlib import Path
import csv
import gzip
import json
import re

# Set input and output locations relative to the project.
ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "data"
PROC = ROOT / "results/data"
OUTPUT = ROOT / "results/character_conventions.md"

# Count spaced en dashes, excluding ranges such as 2023–2025.
DASH = " – "


# Calculate the exact probability of zero hits in one group, given the total.
def fisher_zero_one_sided(n_group: int, other_count: int, hits_total: int) -> float:
    return comb(other_count, hits_total) / comb(n_group + other_count, hits_total)


# Load corpus texts, author classifications and completed machine translations.
def load_inputs() -> tuple[list[dict], dict, list[dict]]:
    with gzip.open(
        INPUTS / "motion_corpus.json.gz", "rt", encoding="utf-8"
    ) as file_handle:
        corpus = json.load(file_handle)["records"]
    with open(PROC / "motion_author_language.csv", encoding="utf-8") as file_handle:
        author = {
            int(record["document_id"]): record for record in csv.DictReader(file_handle)
        }
    machine_translations = json.loads(
        (INPUTS / "complexity_fr_author_translations.json").read_text(encoding="utf-8")
    )["records"]

    return corpus, author, machine_translations


# Compare character storage across periods to contextualise the 2023 cutoff.
def storage_summary(corpus: list[dict]) -> list[str]:
    lines = [
        "## Storage of special characters in the API",
        "",
        "This comparison checks how special characters appear in the archived API texts. Changes in their storage can complicate historical comparisons of punctuation.",
        "",
        "| Period | French texts | with 'oeuvre' | with 'œuvre' | with « » |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, in_period in (
        ("2000-2022", lambda year: year < 2023),
        ("2023-2025", lambda year: year >= 2023),
    ):
        texts = [
            record["input_fr"]
            for record in corpus
            if record["input_fr"] and in_period(int(record["year"]))
        ]
        lines.append(
            f"| {label} | {len(texts):,} | {sum('oeuvre' in text for text in texts):,} | "
            f"{sum('œuvre' in text for text in texts):,} | {sum('«' in text for text in texts):,} |"
        )

    return lines


# Select recent official texts and group them by the submitting member's language.
def group_official_texts(corpus: list[dict], author: dict) -> tuple[list[dict], dict]:
    eligible = [
        record
        for record in corpus
        if record["exclusion_de"] is None
        and record["reference_de"]
        and int(record["year"]) >= 2023
    ]

    # Look up the saved language classification for each eligible motion.
    def author_language(record: dict) -> str:
        return author.get(int(record["document_id"]), {}).get("author_language", "")

    groups = {
        "Official German translations of French-authored motions": [
            record for record in eligible if author_language(record) == "FR"
        ],
        "Official German texts by German- or Italian-speaking members": [
            record for record in eligible if author_language(record) in ("DE", "IT")
        ],
    }
    return eligible, groups


# Compare character counts in machine output and the two official-text groups.
def convention_summary(machine_translations: list[dict], groups: dict) -> list[str]:
    lines = [
        "",
        "## Character conventions by group (official texts: 2023-2025)",
        "",
        "Each count is the number of texts containing the character at least once. Here, ‘dash’ means an en dash with a space on each side. The machine row covers the full 2000–2025 sample; the official groups cover 2023–2025 and are not matched pairs.",
        "",
        "| Group | Texts | With ß | With spaced en dash |",
        "|---|---:|---:|---:|",
        f"| Our MT model (French-authored sample, all years) | {len(machine_translations)} | "
        f"{sum('ß' in record['translation_de'] for record in machine_translations)} | {sum(DASH in record['translation_de'] for record in machine_translations)} |",
    ]
    for name, rows in groups.items():
        lines.append(
            f"| {name} | {len(rows):,} | {sum('ß' in record['reference_de'] for record in rows)} | "
            f"{sum(DASH in record['reference_de'] for record in rows)} |"
        )
    lines.append(
        f"\nOfficial translations in the {len(machine_translations)}-pair sample with a dash: "
        f"{sum(DASH in record['reference_de'] for record in machine_translations)} (machine: {sum(DASH in record['translation_de'] for record in machine_translations)})."
    )

    return lines


# Inspect official texts containing ß and compare its presence between groups.
def sharp_s_summary(eligible: list[dict], groups: dict, author: dict) -> list[str]:
    sharp_s_records = [record for record in eligible if "ß" in record["reference_de"]]
    counts_by_language = Counter(
        author.get(int(record["document_id"]), {}).get("author_language", "")
        or author.get(int(record["document_id"]), {}).get("author_type", "unknown")
        for record in sharp_s_records
    )
    members = {
        author[int(record["document_id"])]["member_id"]
        for record in sharp_s_records
        if int(record["document_id"]) in author
    }
    words = Counter(
        word
        for record in sharp_s_records
        for word in re.findall(r"\w*ß\w*", record["reference_de"])
    )
    french_count = len(
        groups["Official German translations of French-authored motions"]
    )
    other_count = len(
        groups["Official German texts by German- or Italian-speaking members"]
    )
    sharp_s_count = sum(
        "ß" in record["reference_de"]
        for record in groups[
            "Official German texts by German- or Italian-speaking members"
        ]
    )
    if any(
        "ß" in record["reference_de"]
        for record in groups["Official German translations of French-authored motions"]
    ):
        raise ValueError(
            "The zero-hit Fisher calculation requires no French-authored texts with ß"
        )
    lines = [
        "",
        "## Official 2023-2025 texts containing ß",
        "",
        f"- Texts: {len(sharp_s_records)}; classified as German-authored: {counts_by_language['DE']}; Italian-authored: {counts_by_language['IT']}; distinct members: {len(members)}",
        f"- Most frequent ß words: {', '.join(f'{word} ({count})' for word, count in words.most_common(8))}",
        f"- One-sided Fisher exact test comparing the presence of ß in the two official author-language groups: p = {fisher_zero_one_sided(french_count, other_count, sharp_s_count):.4f}.",
        "",
        "| Motion | Year | Member | Canton | Estimated language |",
        "|---|---:|---|---|---|",
    ]
    for record in sharp_s_records:
        author_record = author.get(int(record["document_id"]), {})
        lines.append(
            f"| {record['document_id']} | {record['year']} | {author_record.get('member_id', '?')} | "
            f"{author_record.get('canton', '?')} | {author_record.get('author_language', '?')} |"
        )

    return lines


# Count each group's texts with a spaced en dash in each recent year.
def yearly_dash_summary(groups: dict) -> list[str]:
    lines = [
        "",
        "## Share of official texts with a dash, per year",
        "",
        "| Year | Classified as French-authored | Classified as German/Italian-authored |",
        "|---|---:|---:|",
    ]
    for year in (2023, 2024, 2025):
        cells = []
        for rows in groups.values():
            year_rows = [record for record in rows if int(record["year"]) == year]
            dash_count = sum(DASH in record["reference_de"] for record in year_rows)
            cells.append(
                f"{dash_count}/{len(year_rows)} "
                f"({100 * dash_count / len(year_rows):.0f}%)"
            )
        lines.append(f"| {year} | {cells[0]} | {cells[1]} |")

    return lines


# Assemble the report and print a short summary of the comparison groups.
def main() -> None:
    corpus, author, machine_translations = load_inputs()
    eligible, groups = group_official_texts(corpus, author)
    lines = [
        "# Character conventions in the wider corpus",
        "",
        "This analysis places the sample’s spelling and punctuation differences in context by examining recent official texts and historical character storage. Author-language groups use the same estimates as the sample selection.",
        "",
    ]
    lines.extend(storage_summary(corpus))
    lines.extend(convention_summary(machine_translations, groups))
    lines.extend(sharp_s_summary(eligible, groups, author))
    lines.extend(yearly_dash_summary(groups))
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"  {len(machine_translations)} machine translations (2000–2025).")
    for label, rows in groups.items():
        print(f"  {label}: {len(rows):,} (2023–2025).")
    print("  Report: results/character_conventions.md")


# Run the character comparison when this file is executed directly.
if __name__ == "__main__":
    main()
