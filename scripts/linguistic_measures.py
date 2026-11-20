"""Calculate German linguistic measures and summarise paired translation differences.

The parser and text measures are shared with the source-structure analyses.
Translation scoring returns its results to compare_translation_complexity.py,
which adds confidence intervals and saves the outputs.
"""

# Import tools for parsing, word frequencies, averages and saved input data.
from importlib.metadata import version
from pathlib import Path
from statistics import mean
from typing import Any
import json
import re

from spacy.language import Language
from spacy.symbols import ORTH
from spacy.tokens import Doc
from wordfreq import zipf_frequency
import spacy

# Set the input folder relative to the project.
ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "data"


# Share the seven reported measures and their labels across reporting scripts.
REPORTED_MEASURES = [  # (key, label, group)
    ("mean_sentence_words", "Words per sentence", "Syntax"),
    ("mean_sentence_tree_depth", "Mean max. sentence depth", "Syntax"),
    ("subordinators_per_100_words", "Subordinate markers / 100 words", "Syntax"),
    ("relative_markers_per_100_words", "Relative markers / 100 words", "Syntax"),
    ("mean_content_word_zipf", "Word frequency (Zipf)", "Vocabulary"),
    ("mattr_50", "Lexical variety (MATTR)", "Vocabulary"),
    ("lix", "Readability index (LIX)", "Readability"),
]


# Compare only the measures used in the report, including the Zipf sensitivity check.
COMPARISON_METRICS = (
    "mean_sentence_words",
    "mean_sentence_tree_depth",
    "mean_dependency_distance",
    "mean_content_word_zipf",
    "mean_covered_content_word_zipf",
    "lexical_density_percent",
    "mattr_50",
    "subordinators_per_100_words",
    "relative_markers_per_100_words",
    "lix",
)


# Mark nonempty line starts as sentence boundaries before dependency parsing.
@Language.component("paragraph_boundaries")
def paragraph_boundaries(doc: Doc) -> Doc:
    for token_index, token in enumerate(doc):
        if token_index and not token.is_space:
            previous = doc[token_index - 1]
            if "\n" in previous.text + previous.whitespace_:
                token.is_sent_start = True
    return doc


# Keep legal abbreviations together in parsed and rule-based tokenization.
def add_abbreviation_rules(nlp: Language, texts: list[str]) -> None:
    abbreviations = {"Art.", "art."}
    for text in texts:
        abbreviations.update(re.findall(r"\b\d+[a-z]+\.", text))
    for abbreviation in sorted(abbreviations):
        nlp.tokenizer.add_special_case(abbreviation, [{ORTH: abbreviation}])


# Load a language model with shared abbreviation and sentence-boundary rules.
def load_parser(texts: list[str], model_name: str = "de_core_news_sm") -> Language:
    nlp = spacy.load(model_name, disable=["ner"])
    add_abbreviation_rules(nlp, texts)
    nlp.add_pipe(
        "sentencizer", before="parser", config={"punct_chars": [".", "!", "?"]}
    )
    nlp.add_pipe("paragraph_boundaries", before="parser")
    return nlp


# Measure sentence length, maximum tree depth and dependency distance.
def measure_sentences(doc: Doc) -> dict:
    # Exclude punctuation and whitespace, but include numbers as word tokens.
    sentences = []
    distances = []
    for sentence in doc.sents:
        words = [
            token for token in sentence if not token.is_punct and not token.is_space
        ]
        if not words:
            continue
        positions = {token.i: word_index for word_index, token in enumerate(words)}
        depth = max(
            sum(
                not ancestor.is_punct and not ancestor.is_space
                for ancestor in token.ancestors
            )
            for token in words
        )
        distances.extend(
            abs(positions[token.i] - positions[token.head.i])
            for token in words
            if token.head.i in positions and token.head != token
        )
        sentences.append({"words": len(words), "tree_depth": depth})

    word_count = sum(sentence["words"] for sentence in sentences)
    return {
        "word_count": word_count,
        "sentence_count": len(sentences),
        "mean_sentence_words": word_count / len(sentences),
        "mean_sentence_tree_depth": sum(
            sentence["tree_depth"] for sentence in sentences
        )
        / len(sentences),
        "mean_dependency_distance": (
            sum(distances) / len(distances) if distances else None
        ),
    }


# Measure vocabulary variety, content-word share and word length.
def measure_vocabulary(lexical_words: list) -> dict:
    # Use lowercase lemmas for overlapping windows of 50 words.
    lemmas = [token.lemma_.lower() for token in lexical_words]
    mattr = (
        mean(
            len(set(lemmas[window_start : window_start + 50])) / 50
            for window_start in range(len(lemmas) - 49)
        )
        if len(lemmas) >= 50
        else None
    )
    lexical_density = (
        100
        * sum(
            token.pos_ in {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}
            for token in lexical_words
        )
        / len(lexical_words)
    )
    long_word_percent = (
        100 * sum(len(token.text) > 6 for token in lexical_words) / len(lexical_words)
    )

    return {
        "alphabetic_word_count": len(lexical_words),
        "long_word_percent": long_word_percent,
        "lexical_density_percent": lexical_density,
        "mattr_50": mattr,
    }


# Measure content-word frequency, with and without words absent from the resource.
def measure_frequency(lexical_words: list) -> dict:
    # Use surface forms and exclude proper nouns from the frequency calculation.
    word_frequencies = [
        zipf_frequency(token.text, "de")
        for token in lexical_words
        if token.pos_ in {"NOUN", "VERB", "ADJ", "ADV"}
    ]
    covered_frequencies = [value for value in word_frequencies if value > 0]

    return {
        "mean_content_word_zipf": (
            mean(word_frequencies) if word_frequencies else None
        ),
        "mean_covered_content_word_zipf": (
            mean(covered_frequencies) if covered_frequencies else None
        ),
    }


# Count subordinate and relative markers using the parser's tags.
def measure_clauses(doc: Doc, word_count: int) -> dict:
    # Count markers as proxies for clauses, rather than identifying whole clauses.
    subordinators = sum(token.tag_ in {"KOUS", "KOUI"} for token in doc)
    relatives = sum(token.tag_ in {"PRELS", "PRELAT"} for token in doc)
    return {
        "subordinators_per_100_words": 100 * subordinators / word_count,
        "relative_markers_per_100_words": 100 * relatives / word_count,
    }


# Combine the report measures and supporting counts for one parsed text.
def measure_text(doc: Doc) -> dict[str, Any]:
    sentences = measure_sentences(doc)
    lexical_words = [token for token in doc if token.is_alpha]
    vocabulary = measure_vocabulary(lexical_words)
    return {
        **sentences,
        **measure_frequency(lexical_words),
        **vocabulary,
        **measure_clauses(doc, len(lexical_words)),
        # LIX combines alphabetic words per sentence with the percentage of long words.
        "lix": len(lexical_words) / sentences["sentence_count"]
        + vocabulary["long_word_percent"],
    }


# Summarise paired differences while giving each motion equal weight.
def summarise_pairs(records: list[dict]) -> dict:
    summary = {}
    for metric in COMPARISON_METRICS:
        available = [
            record
            for record in records
            if record["official"][metric] is not None
            and record["generated"][metric] is not None
        ]
        if not available:
            continue
        differences = [
            record["generated"][metric] - record["official"][metric]
            for record in available
        ]
        summary[metric] = {
            "paired_count": len(available),
            "official_mean": mean(record["official"][metric] for record in available),
            "generated_mean": mean(record["generated"][metric] for record in available),
            "mean_difference": mean(differences),
            "generated_lower": sum(value < -1e-8 for value in differences),
            "generated_higher": sum(value > 1e-8 for value in differences),
            "ties": sum(abs(value) <= 1e-8 for value in differences),
        }

    return summary


# Measure both German versions of each completed motion.
def measure_pairs(translations: list[dict], nlp: Language) -> list[dict]:
    records = []

    for record in translations:
        if record["finish_reason"] != "stop" or not record["translation_de"].strip():
            raise ValueError(
                f"Incomplete output in completed records: {record['document_id']}"
            )
        official = measure_text(nlp(record["reference_de"]))
        generated = measure_text(nlp(record["translation_de"]))
        records.append(
            {
                "document_id": record["document_id"],
                "title": record["title_de"],
                "official": official,
                "generated": generated,
            }
        )

    return records


# Calculate measures and collect the metadata needed to interpret them.
def score_translations(
    input_name: str = "complexity_fr_author_translations.json",
    completed_cases_only: bool = False,
) -> dict[str, Any]:
    """Measure completed translation pairs and return results without saving files."""
    source = json.loads((INPUTS / input_name).read_text(encoding="utf-8"))
    if source.get("failed_records") and not completed_cases_only:
        raise ValueError(
            "Resolve flagged translations before evaluating the full sample."
        )
    nlp = load_parser(
        [
            record[field]
            for record in source["records"]
            for field in ("reference_de", "translation_de")
        ]
    )
    records = measure_pairs(source["records"], nlp)

    summary = summarise_pairs(records)

    output = {
        "input_file": input_name,
        "analysis_population": "Normally stopped outputs only; not necessarily semantically valid translations.",
        "attempted_count": len(source["records"])
        + len(source.get("failed_records", [])),
        "completed_count": len(source["records"]),
        "completed_cases_only": completed_cases_only,
        "excluded_failures": [
            {"document_id": row["document_id"], "finish_reason": row["finish_reason"]}
            for row in source.get("failed_records", [])
        ],
        "spacy_version": spacy.__version__,
        "parser": "de_core_news_sm",
        "parser_version": nlp.meta["version"],
        "parser_sources": nlp.meta["sources"],
        "wordfreq_version": version("wordfreq"),
        "definitions": {
            "sentences": "Punctuation sentencizer plus each nonempty line; preserve Art./art. and digit-letter legal references ending in a period as tokens. Semicolons do not split sentences. Identical rules for both versions.",
            "frequency": "Token-weighted surface-form Zipf frequency for alphabetic NOUN, VERB, ADJ, ADV tokens; exclude PROPN. Higher means more common. Report mean including zero and mean over positive entries only; zero means below resource coverage, not a validated difficulty score. Swiss spelling and domain vocabulary can affect coverage.",
            "lexical_measures": "Alphabetic tokens only. MATTR is mean lemma type-token ratio across overlapping windows of 50 words; unavailable below window size. Density counts NOUN, PROPN, VERB, ADJ, ADV as content words.",
            "clause_markers": "STTS KOUS/KOUI subordinators and PRELS/PRELAT relative markers per 100 alphabetic words. These are proxies, not counts of clauses or embedding depth.",
            "lix": "Alphabetic words per sentence plus percentage of alphabetic words longer than six letters. Tokenization-specific implementation; no grade-level interpretation.",
            "words": "Tokens excluding punctuation and whitespace; numbers included.",
            "tree_depth": "Maximum number of non-punctuation, non-whitespace ancestors per sentence; root depth zero. Document value is the unweighted mean over sentences.",
            "dependency_distance": "Mean absolute word-position distance over non-root dependencies whose endpoints are word tokens; punctuation and whitespace excluded from positions.",
        },
        "limitations": "Sample provenance is recorded in the input and methods log. Parser estimates, not validated complexity judgments. Shortening can reflect omissions; length, syntax and tone are different constructs.",
        "summary": summary,
        "records": records,
    }
    return output
