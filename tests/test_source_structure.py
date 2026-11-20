"""Check report numbers, paired sample integrity and source-analysis audit trails."""

from pathlib import Path
from statistics import correlation
import json

import pytest

INPUTS = Path(__file__).resolve().parents[1] / "data"

DATA = Path("results/data")


def read(name):
    return json.loads(
        (
            (INPUTS if name == "complexity_fr_author_translations.json" else DATA)
            / name
        ).read_text()
    )


def test_completed_sample_is_preserved():
    expected = {
        record["document_id"]
        for record in read("complexity_fr_author_translations.json")["records"]
    }
    structure = read("source_sentence_counts.json")
    syntax = read("source_tree_depth.json")
    for analysis in structure["analyses"].values():
        records = analysis["records"]
        assert len(records) == len(expected) == 259
        assert {record["document_id"] for record in records} == expected
        for record in records:
            for version in ["source", "official", "generated"]:
                measurements = record[version]
                assert 0 < measurements["sentence_count"] <= measurements["word_count"]
    assert {record["document_id"] for record in syntax["records"]} == expected
    assert structure["german_counts_check_against_existing_results"] == []


def test_report_matches_saved_counts_and_correlations():
    structure = read("source_sentence_counts.json")
    analysis = structure["analyses"]["punctuation_and_lines"]
    records = analysis["records"]
    for version, expected_count in [("generated", 166), ("official", 86)]:
        actual = sum(
            row[version]["sentence_count"] == row["source"]["sentence_count"]
            for row in records
        )
        assert actual == expected_count
        assert actual == analysis["summary"][version]["exact_source_count_matches"]
    syntax = read("source_tree_depth.json")
    metric = "mean_sentence_tree_depth"
    source = [record["source"][metric] for record in syntax["records"]]
    for version in ["official", "generated"]:
        target = [record[version][metric] for record in syntax["records"]]
        assert correlation(source, target) == pytest.approx(
            syntax["summary"][metric]["raw"][f"source_{version}_r"]
        )


def test_boundary_rules_and_known_dependency_tree():
    # Use a blank pipeline and hand-built dependencies; no trained model is needed.
    spacy = pytest.importorskip("spacy")
    pytest.importorskip("wordfreq")
    from spacy.tokens import Doc
    from compare_sentence_counts import pipeline, measure
    from compare_tree_depth import measure as measure_syntax

    nlp = pipeline("de", ["Art. 3 gilt.\nEin Titel\nDies gilt auch."])
    text = "Art. 3 gilt.\nEin Titel\nDies gilt auch."
    assert measure(nlp, text) == {"sentence_count": 3, "word_count": 8}
    assert measure(nlp, "Art. 3 gilt. Dies gilt auch.")["sentence_count"] == 2
    # Hand-specified dependencies: think -> know -> sing -> birds.
    doc = Doc(
        spacy.blank("en").vocab,
        words=["I", "think", "you", "know", "birds", "sing"],
        heads=[1, 1, 3, 1, 5, 3],
        deps=["nsubj", "ROOT", "nsubj", "ccomp", "nsubj", "ccomp"],
    )
    result = measure_syntax(doc)
    assert result["mean_sentence_tree_depth"] == 3
