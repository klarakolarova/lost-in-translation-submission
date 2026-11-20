"""Translate an additional fixed random sample, separate from the report analyses.

Run from the repository root with the translation dependencies installed:
    python supplementary/scripts/translate_additional.py
The first batch selects 10 additional motions per year using seed 49. Use
--batch 2 (or higher) for a separate batch, with seed 48 plus the batch number.
Each batch selects up to 10 remaining eligible motions per year. Later runs
reuse that selection and resume unattempted translations. Results are not read
by reproduce.sh and require screening before use in an expanded analysis.
"""

import argparse
import csv
import gzip
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from translate_sample import save_checkpoint, translate


# Select extra eligible motions without changing the submitted sample.
def prepare_sample(sample_path: Path, seed: int = 49) -> None:
    if sample_path.exists():
        return
    design = json.loads((ROOT / "data/sample_design.json").read_text())
    excluded = set(design["selected_ids"] + design["excluded_development_ids"])
    # Exclude every previously selected supplementary motion, including failed attempts.
    for previous_path in sample_path.parent.glob("additional_sample*.json"):
        previous = json.loads(previous_path.read_text())
        excluded.update(row["document_id"] for row in previous["records"])
    with (ROOT / "results/data/french_authored_motions.csv").open() as handle:
        french_ids = {int(row["document_id"]) for row in csv.DictReader(handle)}
    with gzip.open(ROOT / "data/motion_corpus.json.gz", "rt", encoding="utf-8") as handle:
        corpus = json.load(handle)["records"]
    eligible = [
        row for row in corpus
        if row["document_id"] in french_ids
        and row["document_id"] not in excluded
        and row["exclusion_de"] is None and row["exclusion_fr"] is None
        and row["input_fr"] and row["reference_de"]
    ]
    generator = random.Random(seed)
    selected = []
    for year in range(2000, 2026):
        candidates = sorted(
            [row for row in eligible if row["year"] == year],
            key=lambda row: row["document_id"],
        )
        selected.extend(generator.sample(candidates, min(10, len(candidates))))
    counts = {year: sum(row["year"] == year for row in selected) for year in range(2000, 2026)}
    save_checkpoint({"seed": seed, "maximum_per_year": 10, "year_counts": counts, "records": selected}, sample_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=int, default=1, help="Batch number; rerunning resumes the same batch.")
    parser.add_argument("--prepare-only", action="store_true", help="Save the selection without loading the model.")
    args = parser.parse_args()
    if args.batch < 1:
        parser.error("--batch must be at least 1")
    folder = ROOT / "supplementary/data"
    suffix = "" if args.batch == 1 else f"_{args.batch}"
    sample_path = folder / f"additional_sample{suffix}.json"
    prepare_sample(sample_path, seed=48 + args.batch)
    print(f"Supplementary batch {args.batch}: {sample_path}", flush=True)
    if args.prepare_only:
        return
    translate(
        ROOT,
        input_name=str(sample_path),
        output_name=str(folder / f"additional_translations{suffix}.json"),
        record_over_limit=True,
    )


if __name__ == "__main__":
    main()
