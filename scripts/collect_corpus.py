"""Optionally download and clean Swiss parliamentary motion justifications.

Retrieve German and French records for 2000–2025, preserve downloaded pages
and record exclusions and yearly coverage. Reuse cached pages when rerun.
Save rebuilt data under results/ without replacing the submitted corpus.

Run python scripts/collect_corpus.py --help for directions and output locations.
"""

# Import tools for downloading API pages, cleaning text and saving the corpus.
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

import re

# Locate regenerated files relative to the project.
ROOT = Path(__file__).resolve().parents[1]


# Remove HTML while preserving paragraph and list-item boundaries.
def clean_text(markup: str) -> str:
    from lxml import html

    # Preserve boundaries before removing tags
    markup = re.sub(r"</(?:p|li)>|<br\s*/?>", "\n", markup, flags=re.IGNORECASE)
    text = html.fromstring(markup).text_content()
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


# Retrieve a year of motion records, reusing downloaded pages when available.
def download_year(year: int, language: str, raw_dir: Path) -> list[dict[str, Any]]:
    # Retrieve fixed-size pages and reuse completed downloads
    raw_dir.mkdir(parents=True, exist_ok=True)
    records = []
    offset = 0
    while True:
        query_parameters = {
            "$filter": f"BusinessType eq 5 and Language eq '{language}' and SubmissionDate ge datetime'{year}-01-01T00:00:00' and SubmissionDate lt datetime'{year + 1}-01-01T00:00:00'",
            "$select": "ID,Language,BusinessType,Title,ReasonText,SubmissionDate",
            "$orderby": "ID",
            "$format": "json",
            "$top": 500,
            "$skip": offset,
        }
        url = "https://ws.parlament.ch/OData.svc/Business?" + urlencode(
            query_parameters
        )
        path = raw_dir / f"motions_{year}_{language.lower()}_offset_{offset}.json"
        metadata_path = path.with_suffix(".metadata.json")
        if not path.exists():
            with urlopen(url, timeout=60) as response:
                content = response.read()
            json.loads(content)
            path.write_bytes(content)
            metadata_path.write_text(
                json.dumps(
                    {
                        "query_url": url,
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        page = json.loads(path.read_text(encoding="utf-8"))["d"]
        rows = page if isinstance(page, list) else page["results"]
        records.extend(rows)
        if len(rows) < 500:
            break
        offset += len(rows)

    # Allow exact server duplicates but reject conflicting versions of an ID
    seen = {}
    for row in records:
        if row["ID"] in seen and row != seen[row["ID"]]:
            raise ValueError(
                f"Conflicting records for {row['ID']} in {year} {language}."
            )
        seen[row["ID"]] = row
    return records


# Build the paired corpus and save coverage counts after each completed year.
def audit_coverage(project_dir: Path) -> None:
    # Preserve all usable German texts, including those without a French match
    coverage = []
    corpus = []
    # Flag verified notices without removing genuine short arguments
    oral_notices = {
        "mündlich",
        "erfolgt mündlich",
        "oral",
        "par oral",
        "suivra par oral",
        "fera l'objet d'un compte rendu oral",
    }
    reference_only_ids = {
        20003407,
        20003408,
        20023150,
        20023381,
        20023469,
        20023470,
        20053001,
        20053468,
        20053469,
        20063176,
        20063177,
        20073277,
        20103391,
        20103392,
        20103393,
        20103394,
        20103395,
        20103630,
        20103631,
        20103632,
        20103633,
        20103634,
        20123648,
        20144009,
        20144010,
        20173013,
        20194382,
    }
    for year in range(2000, 2026):
        languages = {}
        totals = {}
        duplicates = {}
        for language in ("DE", "FR"):
            print(
                f"  {year} {language}: retrieving motion records (cached pages reused)...",
                flush=True,
            )
            rows = download_year(year, language, project_dir / "results/raw")
            totals[language] = len(rows)
            duplicates[language] = len(rows) - len({row["ID"] for row in rows})
            texts = {}
            for row in rows:
                markup = (row["ReasonText"] or "").strip()
                text = clean_text(markup) if markup else ""
                if text:
                    texts[row["ID"]] = {**row, "text": text}
            languages[language] = texts
        german, french = languages["DE"], languages["FR"]
        paired_ids = german.keys() & french.keys()
        coverage.append(
            {
                "year": year,
                "de_records": totals["DE"],
                "fr_records": totals["FR"],
                "de_exact_duplicate_rows": duplicates["DE"],
                "fr_exact_duplicate_rows": duplicates["FR"],
                "de_with_justification": len(german),
                "fr_with_justification": len(french),
                "paired_justifications": len(paired_ids),
            }
        )
        for document_id, german_record in sorted(german.items()):
            french_record = french.get(document_id)
            date = datetime.fromtimestamp(
                int(german_record["SubmissionDate"][6:-2]) / 1000, timezone.utc
            ).date()
            if date.year != year:
                raise ValueError(f"Submission year mismatch for {document_id}.")
            exclusions = {}
            for language, row in (("de", german_record), ("fr", french_record)):
                reason = None
                if row:
                    text = row["text"]
                    if (
                        not any(char.isalpha() for char in text)
                        or text.casefold() == "xxx"
                    ):
                        reason = "placeholder"
                    elif text.casefold().rstrip(".! ") in oral_notices:
                        reason = "oral justification notice"
                    elif language == "de" and document_id in reference_only_ids:
                        reason = (
                            "reference to external document only; manually verified"
                        )
                exclusions[language] = reason
            corpus.append(
                {
                    "document_id": document_id,
                    "year": year,
                    "submission_date": date.isoformat(),
                    "title_de": german_record["Title"],
                    "reference_de": german_record["text"],
                    "title_fr": french_record["Title"] if french_record else None,
                    "input_fr": french_record["text"] if french_record else None,
                    "record_url_de": german_record["__metadata"]["uri"],
                    "record_url_fr": (
                        french_record["__metadata"]["uri"] if french_record else None
                    ),
                    "exclusion_de": exclusions["de"],
                    "exclusion_fr": exclusions["fr"],
                }
            )

        year_records = [row for row in corpus if row["year"] == year]
        coverage[-1]["de_substantive_justifications"] = sum(
            not row["exclusion_de"] for row in year_records
        )
        coverage[-1]["substantive_pairs"] = sum(
            bool(row["input_fr"])
            and not row["exclusion_de"]
            and not row["exclusion_fr"]
            for row in year_records
        )

        save_corpus_checkpoint(project_dir, corpus, coverage, year)
        print(
            f"  Saved {year}: {len(german)} German justifications; "
            f"{len(french)} French; {len(paired_ids)} pairs.",
            flush=True,
        )


# Save the accumulated corpus and coverage after each complete year.
def save_corpus_checkpoint(
    project_dir: Path, corpus: list[dict], coverage: list[dict], year: int
) -> None:
    output = project_dir / "results/data"
    output.mkdir(parents=True, exist_ok=True)
    (output / "motion_coverage.json").write_text(
        json.dumps(
            {
                "scope": "BusinessType 5; full ReasonText; submission years 2000-2025.",
                "completed_through": year,
                "years": coverage,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "motion_corpus.json").write_text(
        json.dumps(
            {
                "scope": "Official German motion justifications, with French counterparts where available; original language unverified.",
                "completed_through": year,
                "records": corpus,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


# Explain the optional download and run the corpus retrieval.
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download German and French motion justifications for 2000–2025.",
        epilog=(
            "Requires internet access and the dependencies in requirements.txt. "
            "Run from the project root: python scripts/collect_corpus.py. "
            "Raw pages: results/raw/. Rebuilt data: results/data/motion_corpus.json "
            "and results/data/motion_coverage.json. Rerunning reuses cached pages. "
            "The submitted files in data/ remain unchanged."
        ),
    )
    parser.parse_args()
    print("Optional corpus regeneration", flush=True)
    print(
        "  Source: Swiss Parliament API; German and French motions, 2000–2025.",
        flush=True,
    )
    print(
        "  Internet access is required for pages not already cached in results/raw/.",
        flush=True,
    )
    print(
        "  Download time depends on the API; progress is shown by year and language.",
        flush=True,
    )
    audit_coverage(ROOT)
    print("  Data: results/data/motion_corpus.json")
    print("  Data: results/data/motion_coverage.json")
    print("  Data: results/raw/")
    print("  Submitted corpus files remain the inputs to reproduce.sh.")


# Run optional retrieval when this file is executed directly.
if __name__ == "__main__":
    main()
