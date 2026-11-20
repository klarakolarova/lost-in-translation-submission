"""Unit tests of the rules behind the report's numbers (no data needed)."""

import random

import pytest

from classify_author_language import bio_language, member_language
from compare_character_conventions import DASH, fisher_zero_one_sided
from check_swiss_conventions import keeps_french_abbreviation, machine_rendering


# --- author language -------------------------------------------------------
def test_bio_language_counts_function_words():
    assert (
        bio_language(
            "Membre du conseil communal de la ville et président de la commission"
        )
        == "FR"
    )
    assert (
        bio_language(
            "Mitglied des Kantonsrats und Präsident der Kommission für Verkehr"
        )
        == "DE"
    )
    assert bio_language("") is None
    assert bio_language("Ingénieur EPFL, MBA") is None  # no function words: undecided


@pytest.mark.parametrize(
    "text,expected",
    [
        ("le la et und", "FR"),
        ("der die und et", "DE"),
        ("le la und", None),
        ("der die et", None),
        ("le und", None),
        ("le", "FR"),
        ("und", "DE"),
    ],
)
def test_bio_language_requires_three_quarters_of_matches(text, expected):
    assert bio_language(text) == expected


@pytest.mark.parametrize(
    "canton,expected", [("ZH", "DE"), ("GE", "FR"), ("JU", "FR"), ("TI", "IT")]
)
def test_monolingual_canton_decides(canton, expected):
    member = {
        "CantonAbbreviation": canton,
        "Mandates": "Mitglied der Kommission und des Vorstands",
    }
    assert member_language(member) == (expected, "canton")


def test_bilingual_canton_uses_biography():
    french_member = {
        "CantonAbbreviation": "VS",
        "Mandates": "Président de la commune et membre du conseil",
    }
    german_member = {
        "CantonAbbreviation": "VS",
        "AdditionalActivity": "Präsident der Gemeinde und Mitglied des Rats",
    }
    unknown = {"CantonAbbreviation": "BE"}
    assert member_language(french_member) == (
        "FR",
        "bilingual canton + biography language",
    )
    assert member_language(german_member) == (
        "DE",
        "bilingual canton + biography language",
    )
    assert member_language(unknown) == ("", "unknown")


# --- terminology -----------------------------------------------------------
@pytest.mark.parametrize(
    "term,text,expected",
    [
        ("motion", "Die vorliegende Motion verlangt ...", "kept"),
        ("motion", "Der Motionär verzichtet ...", "kept"),  # derived form counts
        ("motion", "Der vorliegende Antrag zielt darauf ab ...", "Antrag"),
        ("motion", "Mit diesem Entwurf soll ...", "other"),
        ("interpellation", "In seiner Antwort auf meine Anfrage ...", "Anfrage"),
        ("interpellation", "Zahlreiche Politiker haben ...", "lost"),
        ("postulat", "im Antwort auf die Petition von Polla", "Petition"),
        ("Conseil fédéral", "Ich bitte die Bundesregierung ...", "Bundesregierung"),
        ("Conseil fédéral", "Der Bundesrat wird beauftragt ...", "kept"),
    ],
)
def test_machine_rendering(term, text, expected):
    assert machine_rendering(term, text) == expected


def test_french_abbreviation_kept_only_without_german_form():
    assert keeps_french_abbreviation("AVS", "das AVS-Alter")
    assert not keeps_french_abbreviation("AVS", "das AHV-Alter (AVS)")
    assert not keeps_french_abbreviation("AVS", "die Rente")


# --- special characters ----------------------------------------------------
def test_dash_is_spaced_en_dash_not_range():
    assert DASH in "Das ist – wie gesagt – falsch"
    assert DASH not in "in den Jahren 2023–2025"


def test_fisher_by_simulation():
    rng, n_group, n_other, hits = random.Random(1), 40, 120, 6
    texts = list(range(n_group + n_other))
    simulated_probability = (
        sum(
            all(text_index >= n_group for text_index in rng.sample(texts, hits))
            for _ in range(20000)
        )
        / 20000
    )
    assert simulated_probability == pytest.approx(
        fisher_zero_one_sided(n_group, n_other, hits), abs=0.01
    )
