# Lost in Translation?

**Klára Kolářová and Luisa Müller · Essentials in Text and Speech Processing, 2026**

This submission compares TranslateGemma 4B translations of French Swiss parliamentary
motion justifications with their official German versions. It contains the final
analyses for the report, including the source-structure and chrF robustness checks.
The report PDF is submitted separately.

The [results guide](results/README.md) explains each output and links to the analysis summaries, figures and supporting data.

## Run the analysis

Python 3.14 was used for validation. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
bash reproduce.sh
```

The run takes a few minutes. After installation it works offline, using the saved
translations and corpus data. It recreates the tables, figures and derived
measurements, then runs the tests. It does not generate new translations or
redownload data. Small floating-point and figure-rendering differences can occur
between environments.

## Where to start

| Location | Purpose |
|---|---|
| `reproduce.sh` | The analysis steps in execution order |
| `scripts/` | One named script per analysis; shared measurements in `linguistic_measures.py` |
| `data/` | Fixed inputs, including the original translation attempts and screening annotations |
| `results/*.md` and `results/*.csv` | Readable tables and term-by-term evidence |
| `results/figures/` | Figures used in the report; `design_tikz.tex` is the static study diagram |
| `results/data/` | Recomputed sample, author labels and per-document measurements |
| `tests/` | Checks of sampling, measurement rules and reported results |

## Code and report

| Report analysis | Scripts | Main result |
|---|---|---|
| Corpus and sample | `classify_author_language.py`, `validate_sample.py` | 2,245 eligible French-author pairs; the same 260 sampled motions |
| Translation screening | `screen_translations.py` | `translation_screening.md` |
| RQ1: German complexity | `linguistic_measures.py`, `compare_translation_complexity.py`, `report_complexity_comparison.py` | `translation_complexity_summary.md`, `translation_complexity_details.md`, Figure 2 (`complexity_differences.png`) |
| RQ1: repeated authors | `check_author_dependence.py` | `complexity_author_dependence.md` |
| French-source preservation | `compare_sentence_counts.py`, `compare_tree_depth.py` | `source_sentence_counts.md`, `source_tree_depth.md` |
| RQ2: terminology and conventions | `check_swiss_conventions.py` | `swiss_terminology.md`, `swiss_writing_conventions.md`, `terminology_matches.csv`, `terminology_examples.csv` |
| RQ3: similarity over time | `compare_translation_similarity.py` | `translation_similarity.md`, Figure 3 (`translation_similarity.png`) |
| RQ3: source adjustment | `adjust_similarity_for_source.py` | `source_adjusted_similarity.md` |
| RQ3: special characters | `compare_character_conventions.py` | `character_conventions.md` |

Author language is a proxy for original text language. The sample was constructed by retaining
63 eligible completed translations from the earlier random sample and randomly
filling each year to 10 motions with seed 48, excluding 30 development documents.
This selection history and the final IDs are recorded in `data/sample_design.json`.
Reproduction loads the fixed IDs and verifies eligibility, yearly counts and
agreement with saved translation inputs; it does not draw a new sample.

## Fixed inputs

- `motion_corpus.json.gz`: cleaned motion justifications and exclusion flags,
  2000–2025. The corpus contains 10,622 records, including 10,581 usable German
  texts and 10,573 usable German–French pairs.
- `motion_coverage.json`: yearly retrieval and coverage counts.
- `authors/`: saved Parliament API author-role and member snapshots.
- `sample_design.json`: sampling seed, reused IDs, excluded IDs and selected IDs.
- `complexity_fr_author_translations.json`: all 260 attempts, model settings and
  prompts; 259 completed outputs and one output-limit failure.
- `screening_annotations.csv`: recorded judgements for the reading sample and
  automatically flagged outputs. The script validates their coverage; it does
  not generate these judgements.

The texts and author records were retrieved from the Swiss Parliament's Curia Vista
open data service in November 2026. This copy was prepared from commit `3cb3d43` of
[the development repository](https://github.com/luisaellamueller/lost-in-translation),
which retains the original raw downloads and development history. Input text,
translation attempts, annotations and numerical results are preserved.

## Optional regeneration

These commands regenerate inputs; they are not needed to reproduce the report.
Run them from the project root after creating the Python environment above.
Each script supports `--help`, reports progress and prints its output locations.

### Download the corpus again

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/collect_corpus.py
```

This retrieves German and French motion justifications for 2000–2025. Internet
access is needed for uncached pages. Downloads are saved in `results/raw/`;
rerunning the command reuses those pages and rebuilds the cleaned data.

- Cleaned corpus: `results/data/motion_corpus.json`
- Retrieval and coverage counts: `results/data/motion_coverage.json`

The live API can change, so a fresh download may differ from the submitted
snapshot. The main analyses continue to read the archived inputs in `data/`.

### Generate the translations again

Prepare the environment and the fixed sample:

```bash
source .venv/bin/activate
python -m pip install -r requirements-translation.txt
python scripts/classify_author_language.py
python scripts/validate_sample.py
mkdir -p models
```

Download `translategemma-4b-it-Q4_K_M.gguf` from
[Menterium's model repository](https://huggingface.co/Menterium/translategemma-4b-it-GGUF)
and place it in `models/`. The model used for the submitted translations has SHA-256:

```text
e7d9523174272fca61264b339f06d10c6115426267bb0f752b0124084e487b8e
```

Then run:

```bash
python scripts/translate_sample.py
```

This translates the fixed French sample and saves each attempt to
`results/data/translations_rerun.json`. The terminal shows progress by document.
Model loading and generation can take substantially longer than `reproduce.sh`,
depending on the hardware.

If interrupted, run the same command again: it processes only unattempted texts.
Failed attempts stay recorded and are not automatically retried. The script
checks that saved inputs and settings match before resuming. To start from
scratch, move the rerun JSON elsewhere first.

The submitted translations are preserved, and `reproduce.sh` continues to use
them. Regenerated wording may differ across hardware and library versions.

## Licence

Code and derived results use the included MIT licence. Parliamentary texts remain
subject to the Parliament's open-data terms; model weights are not included and
retain their own licence.
