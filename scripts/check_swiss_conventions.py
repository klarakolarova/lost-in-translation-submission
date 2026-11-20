"""Compare Swiss terminology and writing conventions in official and machine German.

For terms found in the French sources, check whether each German version uses
the corresponding Swiss institutional term. Record alternative translations,
French abbreviations retained without their German equivalents, and spelling
and punctuation conventions.

Save summary tables and text excerpts for manual inspection in results/.
"""

# Import tools for pattern matching, counts and saved data.
from collections import Counter
from pathlib import Path
import csv
import json
import re

# Set the input and output locations relative to the project.
ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "data/complexity_fr_author_translations.json"
OUT = ROOT / "results"

# term: (French pattern, Swiss German pattern, [(alternative label, pattern)], fallback label)
TERMS = {
    "motion": (
        r"\bmotions?\b",
        r"\bMotion\w*",
        [("Antrag", r"\bAntr(ag|äg)\w*")],
        "other",
    ),
    "interpellation": (
        r"\binterpellations?\b",
        r"\bInterpellation\w*",
        [("Anfrage", r"\bAnfrage\w*")],
        "lost",
    ),
    "postulat": (
        r"\bpostulats?\b",
        r"\bPostulat\w*",
        [
            ("Petition", r"\bPetition\w*"),
            ("Punkt", r"\bPunkt\b"),
            ("Prämisse", r"\bPrämisse\b"),
        ],
        "other",
    ),
    "initiative parlementaire": (
        r"\binitiatives? parlementaires?\b",
        r"\bInitiative\w*",
        [],
        "other",
    ),
    "Conseil fédéral": (
        r"\bconseil f[ée]d[ée]ral\b",
        r"\bBundesrat\w*",
        [("Bundesregierung", r"\bBundesregierung\w*")],
        "other",
    ),
    "Conseil national": (r"\bconseil national\b", r"\bNationalrat\w*", [], "other"),
    "Conseil des Etats": (
        r"\bconseil des [ée]tats\b",
        r"\bStänderat\w*",
        [("Rat der Stände", r"\bRat der Stände\b")],
        "other",
    ),
}
# French abbreviation -> Swiss German abbreviation (unambiguous forms only)
ABBREVIATIONS = {
    "AVS": "AHV",
    "LAMal": "KVG",
    "LPP": "BVG",
    "LIFD": "DBG",
    "LHID": "StHG",
    "CFF": "SBB",
    "EPF": "ETH",
    "OFSP": "BAG",
    "OFEV": "BAFU",
    "OFAS": "BSV",
    "LCR": "SVG",
    "DFAE": "EDA",
    "DDPS": "VBS",
    "DETEC": "UVEK",
    "OFROU": "ASTRA",
    "LAA": "UVG",
    "APG": "EO",
    "OFEN": "BFE",
    "OFT": "BAV",
    "LPE": "USG",
    "LAT": "RPG",
    "OFAG": "BLW",
    "AFC": "ESTV",
    "CDF": "EFK",
    "LAI": "IVG",
    "LAVS": "AHVG",
    "OFS": "BFS",
    "OFJ": "BJ",
    "DFF": "EFD",
    "DFI": "EDI",
    "DEFR": "WBF",
    "DFJP": "EJPD",
    "CEDH": "EMRK",
    "LACI": "AVIG",
}


# Patterns for Swiss spelling and punctuation conventions.
CONVENTIONS = {
    "ß (never used in Swiss German)": r"ß",
    "German quotes „ “": r"[„“]",
    "Swiss quotes « »": r"[«»]",
    "thousands with dot (10.000)": r"\b\d{1,3}\.\d{3}\b",
    "thousands with space/apostrophe (10 000, 10'000)": r"\b\d{1,3}[  '’]\d{3}\b",
}


# Identify the Swiss term or the first matching alternative in the German text.
def machine_rendering(term: str, german: str) -> str:
    _, german_pattern, alternatives, fallback = TERMS[term]
    if re.search(german_pattern, german):
        return "kept"
    return next(
        (label for label, pattern in alternatives if re.search(pattern, german)),
        fallback,
    )


# Flag a French abbreviation only when its German equivalent is absent.
def keeps_french_abbreviation(abbreviation: str, german: str) -> bool:
    return bool(re.search(rf"\b{abbreviation}\b", german)) and not re.search(
        rf"\b{ABBREVIATIONS[abbreviation]}\b", german
    )


# Collect approximate sentence excerpts containing the requested term.
def matching_excerpts(text: str, pattern: str, flags: int = 0) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " | ".join(
        sentence for sentence in sentences if re.search(pattern, sentence, flags)
    )


# Count texts containing each spelling or formatting feature at least once.
def convention_counts(records: list[dict]) -> str:
    rows = ["| Feature | Official German | Machine German |", "|---|---:|---:|"]
    for name, pattern in CONVENTIONS.items():
        official_count = sum(
            bool(re.search(pattern, record["reference_de"])) for record in records
        )
        machine_count = sum(
            bool(re.search(pattern, record["translation_de"])) for record in records
        )
        rows.append(f"| {name} | {official_count} | {machine_count} |")
    heading = (
        f"# Swiss spelling and formatting conventions\n\n"
        f"Comparison of {len(records)} completed translation pairs from motions classified as French-authored. These counts show whether the two German versions follow the same spelling, quotation and number-formatting conventions.\n\n"
        "## Results\n\nNumber of texts containing each feature at least once; a text may contain more than one feature. These are presence checks, not counts of all occurrences.\n\n"
    )
    return (
        heading
        + "\n".join(rows)
        + "\n\n## Related results\n\nSee [parliamentary terminology](swiss_terminology.md) for institutional terms and [character conventions](character_conventions.md) for comparisons with the wider corpus.\n"
    )


# Check the terminology rules and collect text excerpts for reviewing the matches.
def check_terms(records: list[dict]) -> tuple[list[str], list[dict], list[dict]]:
    rows, contexts = [], []
    lines = [
        "# Swiss parliamentary terminology",
        "",
        f"Comparison of {len(records)} completed translation pairs from motions classified as French-authored. This checks whether French institutional terms are rendered using the expected Swiss German terminology.",
        "",
        "## Institutional terms",
        "",
        "Counts refer to texts containing the French term. A German version counts as retaining the term when an accepted form appears anywhere in that text. Alternatives show the first matching replacement; ‘other’ means no listed alternative matched, and ‘lost’ is the rule’s category for an interpellation not retained.",
        "",
        "| French source | Texts | Official keeps | Machine keeps | Machine instead (texts) |",
        "|---|---:|---:|---:|---|",
    ]
    for term, (french_pattern, german_pattern, _, _) in TERMS.items():
        matching_records = [
            record
            for record in records
            if re.search(french_pattern, record["input_fr"], re.I)
        ]
        official_count = machine_count = 0
        alternative_counts = Counter()
        for record in matching_records:
            official_keeps = bool(re.search(german_pattern, record["reference_de"]))
            rendering = machine_rendering(term, record["translation_de"])
            machine_keeps = rendering == "kept"
            official_count += official_keeps
            machine_count += machine_keeps
            if not machine_keeps:
                alternative_counts[rendering] += 1
            rows.append(
                {
                    "term": term,
                    "document_id": record["document_id"],
                    "official_keeps": int(official_keeps),
                    "machine_keeps": int(machine_keeps),
                    "machine_rendering": rendering,
                }
            )
            contexts.append(
                {
                    "term": term,
                    "document_id": record["document_id"],
                    "french": matching_excerpts(
                        record["input_fr"], french_pattern, re.I
                    ),
                    "official": matching_excerpts(
                        record["reference_de"], german_pattern
                    ),
                    "machine": (
                        matching_excerpts(record["translation_de"], german_pattern)
                        if machine_keeps
                        else record["translation_de"]
                    ),
                }
            )
        alternative_summary = (
            ", ".join(
                f"{alternative} ({count})"
                for alternative, count in alternative_counts.most_common()
            )
            or "-"
        )
        lines.append(
            f"| {term} | {len(matching_records)} | {official_count} | {machine_count} | {alternative_summary} |"
        )

    return lines, rows, contexts


# Summarise texts retaining French abbreviations without the German equivalents.
def abbreviation_summary(records: list[dict]) -> list[str]:
    texts_with_abbreviations = machine_french_count = official_french_count = 0
    examples = Counter()
    for record in records:
        source_abbreviations = [
            abbreviation
            for abbreviation in ABBREVIATIONS
            if re.search(rf"\b{abbreviation}\b", record["input_fr"])
        ]
        if not source_abbreviations:
            continue
        texts_with_abbreviations += 1
        retained_abbreviations = lambda text: [
            abbreviation
            for abbreviation in source_abbreviations
            if keeps_french_abbreviation(abbreviation, text)
        ]
        machine_abbreviations, official_abbreviations = retained_abbreviations(
            record["translation_de"]
        ), retained_abbreviations(record["reference_de"])
        machine_french_count += bool(machine_abbreviations)
        official_french_count += bool(official_abbreviations)
        examples.update(machine_abbreviations)
    return [
        "",
        "## Abbreviations",
        "",
        "A French abbreviation counts as retained only when it appears without its German equivalent.",
        "",
        f"French abbreviations of Swiss authorities and laws: {texts_with_abbreviations} texts contain one; "
        f"the machine output keeps the French form in {machine_french_count}, the official translation in {official_french_count}.",
        "",
        "Most frequently retained French abbreviations (French → German; number of texts): "
        + ", ".join(
            f"{abbreviation} → {ABBREVIATIONS[abbreviation]} ({count})"
            for abbreviation, count in examples.most_common(8)
        )
        + ".",
    ]


# Save the terminology table, match records and excerpts for manual inspection.
def save_results(lines: list[str], rows: list[dict], contexts: list[dict]) -> None:
    lines += [
        "",
        "## Supporting data",
        "",
        "[Term matches](terminology_matches.csv) list each text-level decision; [text excerpts](terminology_examples.csv) allow inspection of the French source and German renderings. See also [spelling and formatting conventions](swiss_writing_conventions.md).",
    ]
    (OUT / "swiss_terminology.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name, data in (
        ("terminology_matches.csv", rows),
        ("terminology_examples.csv", contexts),
    ):
        with open(OUT / name, "w", newline="", encoding="utf-8") as file_handle:
            writer = csv.DictWriter(file_handle, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)


# Load completed translations and check terminology, abbreviations and conventions.
def main() -> None:
    records = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))["records"]
    OUT.mkdir(exist_ok=True)
    lines, rows, contexts = check_terms(records)
    lines.extend(abbreviation_summary(records))
    save_results(lines, rows, contexts)
    (OUT / "swiss_writing_conventions.md").write_text(
        convention_counts(records), encoding="utf-8"
    )

    # Print a short summary and output locations instead of the full tables.
    print(
        f"  {len(records)} completed pairs; {len(TERMS)} institutional terms checked."
    )
    print(
        f"  {len(ABBREVIATIONS)} French–German abbreviation equivalents and {len(CONVENTIONS)} spelling or formatting patterns."
    )
    print("  Report: results/swiss_terminology.md (terms and abbreviations)")
    print("  Report: results/swiss_writing_conventions.md (spelling and formatting)")
    print("  Data: results/terminology_matches.csv (text-level decisions)")
    print("  Data: results/terminology_examples.csv (excerpts for inspection)")


# Run the terminology checks when this file is executed directly.
if __name__ == "__main__":
    main()
