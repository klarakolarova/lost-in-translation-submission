"""Check sample integrity, annotation coverage and selected reported results."""

from pathlib import Path
import csv
import gzip
import json
import re

import pytest

from compare_character_conventions import fisher_zero_one_sided
from check_swiss_conventions import TERMS, machine_rendering
from validate_sample import check_corpus_totals, check_sample, check_translation_inputs
from screen_translations import screen_translations, validate_annotations

PROC = Path("results/data")


def translations():
    return json.loads(
        (Path("data/complexity_fr_author_translations.json")).read_text(
            encoding="utf-8"
        )
    )


def test_translation_sample_size():
    data = translations()
    assert len(data["records"]) == 259 and len(data["failed_records"]) == 1


def test_sample_matches_recorded_ids():
    sample = json.loads((PROC / "validated_sample.json").read_text(encoding="utf-8"))[
        "records"
    ]
    design = json.loads(Path("data/sample_design.json").read_text(encoding="utf-8"))
    with gzip.open("data/motion_corpus.json.gz", "rt", encoding="utf-8") as file_handle:
        corpus = json.load(file_handle)["records"]
    with (PROC / "french_authored_motions.csv").open(encoding="utf-8") as file_handle:
        french_ids = {int(row["document_id"]) for row in csv.DictReader(file_handle)}

    # Compare the saved sample with its original corpus records in the fixed order.
    corpus_by_id = {row["document_id"]: row for row in corpus}
    assert sample == [
        corpus_by_id[document_id] for document_id in design["selected_ids"]
    ]
    check_corpus_totals(corpus)
    check_sample(sample, french_ids, design)
    check_translation_inputs(sample)


@pytest.mark.skipif(
    not (PROC / "motion_author_language.csv").exists(),
    reason="run scripts/classify_author_language.py first",
)
def test_french_authored_pairs():
    with open(PROC / "motion_author_language.csv", encoding="utf-8") as file_handle:
        language_by_motion = {
            int(record["document_id"]): record["author_language"]
            for record in csv.DictReader(file_handle)
        }
    corpus = json.load(gzip.open("data/motion_corpus.json.gz", "rt", encoding="utf-8"))[
        "records"
    ]
    eligible = [
        record
        for record in corpus
        if record["exclusion_de"] is None
        and record["exclusion_fr"] is None
        and record["reference_de"]
        and record["input_fr"]
    ]
    assert len(eligible) == 10573
    assert (
        sum(
            language_by_motion.get(int(record["document_id"])) == "FR"
            for record in eligible
        )
        == 2245
    )


@pytest.mark.parametrize(
    "term,texts,official,machine",
    [
        ("motion", 43, 41, 22),
        ("interpellation", 15, 14, 1),
        ("postulat", 4, 4, 1),
        ("initiative parlementaire", 2, 2, 2),
        ("Conseil fédéral", 108, 108, 95),
        ("Conseil des Etats", 3, 3, 2),
    ],
)
def test_table1_terminology(term, texts, official, machine):
    french_pattern, german_pattern, _, _ = TERMS[term]
    matching_records = [
        record
        for record in translations()["records"]
        if re.search(french_pattern, record["input_fr"], re.I)
    ]
    assert len(matching_records) == texts
    assert (
        sum(
            bool(re.search(german_pattern, record["reference_de"]))
            for record in matching_records
        )
        == official
    )
    assert (
        sum(
            machine_rendering(term, record["translation_de"]) == "kept"
            for record in matching_records
        )
        == machine
    )


def test_ss_in_machine_but_not_official():
    records = translations()["records"]
    assert sum("ß" in record["translation_de"] for record in records) == 193
    assert sum("ß" in record["reference_de"] for record in records) == 0


def test_rq1_differences():
    results = json.loads(
        (PROC / "translation_complexity.json").read_text(encoding="utf-8")
    )["summary"]
    expected = {
        "mean_sentence_words": 1.078,
        "mean_sentence_tree_depth": 0.277,
        "mean_content_word_zipf": 0.118,
        "lix": 1.774,
    }
    for key, value in expected.items():
        assert results[key]["mean_difference"] == pytest.approx(value, abs=0.001)
        low, high = results[key]["paired_bootstrap_ci95"]
        assert low > 0 and high > 0  # interval excludes zero, as reported


def test_fisher_value_in_report():
    assert fisher_zero_one_sided(435, 1058, 14) == pytest.approx(0.008, abs=0.0005)


def test_screening_annotations_cover_sample_and_flags():
    records = translations()["records"]
    checks = screen_translations(records)
    validate_annotations(records, checks)
