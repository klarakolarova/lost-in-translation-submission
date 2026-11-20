"""This script estimates author language from their canton.
For multilingual cantons, biography fields are checked for French and German
word-list matches, requiring at least 75% to support one language.

Each motion is labelled with its author's estimated language.
The classifications and French-authored motion IDs are saved for sample checks
and later analyses.

Author language is a proxy for the original language of a motion.
"""

# Import tools for file handling, data formats and word matching.
from pathlib import Path
import csv
import gzip
import json
import re

# Set the input and output folders relative to the project.
ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "data"
RAW = INPUTS / "authors"
RESULTS = ROOT / "results"
PROC = RESULTS / "data"


# Group monolingual cantons by language; use biographies for the remaining cantons.
DE = set("ZH LU UR SZ OW NW GL ZG SO BS BL SH AR AI SG AG TG".split())
FR = set("VD NE GE JU".split())
IT = {"TI"}

# Define French and German word lists for identifying the language of biographies.
FR_WORDS = set(
    "le la les des du de et pour dans au aux une un président membre conseiller "
    "conseillère député depuis".split()
)
DE_WORDS = set(
    "der die das und für im von des mitglied präsident gemeinderat kantonsrat seit "
    "bis verwaltungsrat".split()
)


# Combine nonempty biography fields into one text for language classification.
def biography(member: dict) -> str:
    return " ".join(
        filter(
            None,
            [
                member.get("Mandates"),
                member.get("AdditionalActivity"),
                member.get("AdditionalMandate"),
            ],
        )
    )


# Estimate biography language by counting French and German word-list matches.
def bio_language(text: str) -> str | None:
    words = re.findall(r"[a-zäöüéèàç]+", (text or "").lower())
    french_matches = sum(word in FR_WORDS for word in words)
    german_matches = sum(word in DE_WORDS for word in words)
    total = french_matches + german_matches
    if total == 0:
        return None
    # Require at least 75% of matches to support one language.
    if french_matches / total >= 0.75:
        return "FR"
    if german_matches / total >= 0.75:
        return "DE"
    return None  # Leave inconclusive biographies unclassified.


# Assign language from the canton, falling back to the biography when needed.
def member_language(member: dict) -> tuple[str, str]:
    canton = member.get("CantonAbbreviation") or ""
    if canton in DE:
        return "DE", "canton"
    if canton in FR:
        return "FR", "canton"
    if canton in IT:
        return "IT", "canton"
    language = bio_language(biography(member))
    return (
        (language, "bilingual canton + biography language")
        if language
        else ("", "unknown")
    )


# Check whether biography-based language agrees with the language of monolingual cantons.
def check_biography_agreement(members: dict) -> tuple[int, int]:
    classified_count = agreement_count = 0
    for member in members.values():
        canton = member.get("CantonAbbreviation")
        if canton in DE or canton in FR:
            language = bio_language(biography(member))
            if language:
                classified_count += 1
                agreement_count += language == ("DE" if canton in DE else "FR")

    return agreement_count, classified_count


# Assign an author-language record to each motion.
def classify_motions(roles: dict, members: dict) -> list[dict]:
    # Group author-role records by motion ID so we can look up each motion's author.
    roles_by_motion: dict[int, list[dict]] = {}
    for record in roles["rows"]:
        roles_by_motion.setdefault(record["BusinessNumber"], []).append(record)

    # Find each motion's submitting member
    rows = []
    # The API inventory contains a repeated ID; classify each motion once.
    for document_id in dict.fromkeys(roles["business_ids"]):
        authors = roles_by_motion.get(document_id, [])
        member_rows = [
            record for record in authors if record["MemberCouncilNumber"] in members
        ]

        # Estimate the member's language and save it with the motion ID and classification details.
        if member_rows:
            member = members[member_rows[0]["MemberCouncilNumber"]]
            language, method = member_language(member)
            rows.append(
                {
                    "document_id": document_id,
                    "author_type": "member",
                    "member_id": member["ID"],
                    "canton": member.get("CantonAbbreviation") or "",
                    "author_language": language,
                    "method": method,
                }
            )

        # Record motions without an identified member, with author language unclassified.
        else:
            if any(record["CommitteeNumber"] for record in authors):
                author_type = "committee"
            elif any(record["ParlGroupNumber"] for record in authors):
                author_type = "parl_group"
            else:
                author_type = "none"

            rows.append(
                {
                    "document_id": document_id,
                    "author_type": author_type,
                    "member_id": "",
                    "canton": "",
                    "author_language": "",
                    "method": author_type,
                }
            )

    return rows


# Save the full classifications and French-authored motion IDs.
def save_classifications(rows: list[dict]) -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    # Save all motion classifications for use in later analyses.
    with open(
        PROC / "motion_author_language.csv", "w", newline="", encoding="utf-8"
    ) as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    # Save French-authored motion IDs for sample selection.
    french = [record for record in rows if record["author_language"] == "FR"]
    with open(
        PROC / "french_authored_motions.csv", "w", newline="", encoding="utf-8"
    ) as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow(["document_id", "method"])
        writer.writerows([record["document_id"], record["method"]] for record in french)


# Save and display the agreement check and eligible-pair counts.
def report_classifications(rows: list[dict], members: dict, retrieved: str) -> None:
    # Compare biography-based language with canton language and collect the agreement counts.
    agreement_count, classified_count = check_biography_agreement(members)

    # Count eligible French–German text pairs and how many have French-classified authors.
    corpus = json.load(
        gzip.open(INPUTS / "motion_corpus.json.gz", "rt", encoding="utf-8")
    )["records"]
    eligible = [
        record
        for record in corpus
        if record["exclusion_de"] is None
        and record["exclusion_fr"] is None
        and record["reference_de"]
        and record["input_fr"]
    ]
    language_by_motion = {
        record["document_id"]: record["author_language"] for record in rows
    }
    french_pairs = sum(
        language_by_motion.get(int(record["document_id"])) == "FR"
        for record in eligible
    )

    # Save the data provenance, biography agreement counts and eligible-pair counts in a summary.
    RESULTS.mkdir(exist_ok=True)
    lines = [
        "# Author language and the sampling pool",
        "",
        "This classification identifies the pool of motions likely to have been written in French before translation into German. Author language is estimated from canton and biography information.",
        "",
        "## Classification rule",
        "",
        "For multilingual cantons, a language was assigned when at least 75% of "
        "French/German word-list matches supported it; otherwise, it remained unclassified.",
        "",
        "## Agreement check",
        "",
        f"Among members from monolingual German/French cantons whose biographies could "
        f"be classified, {agreement_count} of {classified_count} biography-based estimates agreed with the "
        "canton language. This measures agreement with the canton proxy, rather than "
        "verified author language.",
        "",
        "## Eligible sampling pool",
        "",
        f"Of {len(eligible):,} eligible French–German text pairs, {french_pairs:,} were "
        "classified as French-authored and formed the pool for sample selection.",
        "",
        "## Data source",
        "",
        f"Author records retrieved {retrieved}; archived in `data/authors/`. Per-motion classifications are saved in [motion_author_language.csv](data/motion_author_language.csv).",
    ]
    (RESULTS / "author_language_summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    # Print a short summary and output location.
    print(
        f"  Biography estimates agree with canton language for {agreement_count} of {classified_count} classifiable biographies."
    )
    print(
        f"  {french_pairs:,} of {len(eligible):,} eligible French–German pairs are classified as French-authored."
    )
    print("  Report: results/author_language_summary.md")


# Load the author data, classify motions and save the results.
def main() -> None:
    # Load motion–author links and organise member records by ID.
    roles = json.loads((RAW / "business_roles.json").read_text(encoding="utf-8"))
    members = {
        member["ID"]: member
        for member in json.loads((RAW / "members.json").read_text(encoding="utf-8"))[
            "rows"
        ]
    }

    rows = classify_motions(roles, members)
    save_classifications(rows)
    report_classifications(rows, members, roles["meta"]["retrieved"])


# Run the classification when this file is executed directly.
if __name__ == "__main__":
    main()
