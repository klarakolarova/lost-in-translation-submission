"""Reconstruct the fixed sample from author labels and the recorded sampling design."""

from pathlib import Path
import csv
import gzip
import json
import random


def main():
    data = Path("data")
    generated = Path("results/data")
    design = json.loads((data / "sample_design.json").read_text())
    corpus = json.load(
        gzip.open(data / "motion_corpus.json.gz", "rt", encoding="utf-8")
    )["records"]
    with (generated / "french_authored_motions.csv").open() as f:
        french = {int(r["document_id"]) for r in csv.DictReader(f)}
    excluded = set(design["excluded_development_ids"])
    reused = set(design["reused_translation_ids"])
    eligible = [
        r
        for r in corpus
        if r["exclusion_de"] is None
        and r["exclusion_fr"] is None
        and r["reference_de"]
        and r["input_fr"]
        and r["document_id"] in french
        and r["document_id"] not in excluded
    ]
    rng = random.Random(design["seed"])
    selected = []
    for year in range(2000, 2026):
        pool = sorted(
            (r for r in eligible if r["year"] == year), key=lambda r: r["document_id"]
        )
        keep = [r for r in pool if r["document_id"] in reused]
        rest = [r for r in pool if r["document_id"] not in reused]
        chosen = keep + rng.sample(rest, design["per_year"] - len(keep))
        selected.extend(sorted(chosen, key=lambda r: r["document_id"]))
    ids = [r["document_id"] for r in selected]
    if ids != design["selected_ids"]:
        raise ValueError("Redrawn sample differs from the recorded sample")
    translations = json.loads(
        (data / "complexity_fr_author_translations.json").read_text()
    )
    attempts = translations["records"] + translations["failed_records"]
    assert len(ids) == len(set(ids)) == len(attempts) == 260
    assert set(ids) == {r["document_id"] for r in attempts}
    expected = {r["document_id"]: r for r in selected}
    for r in attempts:
        if any(r[k] != v for k, v in expected[r["document_id"]].items()):
            raise ValueError(
                f"Translation input differs from corpus: {r['document_id']}"
            )
    assert len(corpus) == len({r["document_id"] for r in corpus}) == 10622
    assert sum(not r["exclusion_de"] for r in corpus) == 10581
    assert (
        sum(
            not r["exclusion_de"] and not r["exclusion_fr"] and bool(r["input_fr"])
            for r in corpus
        )
        == 10573
    )
    generated.mkdir(parents=True, exist_ok=True)
    (generated / "sample.json").write_text(
        json.dumps({"records": selected}, ensure_ascii=False, indent=2) + "\n"
    )
    print("Redrawn sample identical to recorded sample: True (260 IDs)")


if __name__ == "__main__":
    main()
