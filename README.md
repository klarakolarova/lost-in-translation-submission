# Lost in Translation?

**Klára Kolářová and Luisa Müller · Essentials in Text and Speech Processing, 2026**

This project compares TranslateGemma 4B translations of French Swiss parliamentary
motion justifications with their official German versions. It examines linguistic
complexity, Swiss terminology and writing conventions, and translation similarity
over time.

The fixed sample contains 260 motions from 2000–2025. Of these, 259 machine
translations completed; one reached the output limit and is excluded from the
comparisons. The report PDF is submitted separately.

## Reproduce the results

### First run

Open a terminal in this repository’s root directory. Python 3.14 was used for
validation. Create an environment and install the dependencies, including the
French and German spaCy models:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
bash reproduce.sh
```

Installation requires internet access. After installation, the analysis runs
offline using the saved corpus, translations and manual annotations. No language
model download or new translation generation is needed.

### Subsequent runs

```bash
source .venv/bin/activate
bash reproduce.sh
```

The script takes a few minutes and runs five stages: sample checks, complexity,
Swiss conventions, historical comparisons, and automated tests. It regenerates
the analysis reports, figures and measurements in `results/`. A successful run
ends with:

```text
44 passed
Reproduction completed successfully; all verification tests passed.
```

## Read the results

Start with the **[results guide](results/README.md)**. It links every analysis to
its summary and supporting data and explains how to read the comparisons.

| Research question | Main summaries |
|---|---|
| RQ1: How does linguistic complexity differ? | [Complexity comparison](results/translation_complexity_summary.md), with checks for repeated authors and French-source structure in the results guide |
| RQ2: Are Swiss terms and conventions retained? | [Parliamentary terminology](results/swiss_terminology.md) and [spelling and formatting](results/swiss_writing_conventions.md) |
| RQ3: Does translation similarity change over time? | [Similarity trend](results/translation_similarity.md), [adjustment for French inputs](results/source_adjusted_similarity.md) and [character conventions](results/character_conventions.md) |

## Additional robustness analysis

An expanded, year-balanced sample of 598 translation pairs and a separate check
using 338 new translations reproduce the main patterns. See the
[supplementary analysis](supplementary/README.md) for results, review status and
reproduction instructions. This optional analysis is separate from the report.

## Project structure

| Location | Contents |
|---|---|
| [reproduce.sh](reproduce.sh) | Analysis steps in execution order, with a description of each script |
| [scripts/](scripts/) | Analysis scripts; shared linguistic measurements in `linguistic_measures.py` |
| [data/](data/) | Fixed corpus, sample selection, translation attempts and manual annotations |
| [results/](results/) | Readable summaries and CSV tables |
| [results/figures/](results/figures/) | Report figures and `design_tikz.tex`, the static study-diagram source |
| [results/data/](results/data/) | Regenerated sample checks, author labels and document measurements |
| [tests/](tests/) | Checks of sampling, measurement rules and reported results |

To run one analysis separately, activate the environment and use
`python scripts/<script_name>.py` from the repository root. Some scripts use
outputs from earlier steps; [reproduce.sh](reproduce.sh) shows the required order.

## Sample and fixed inputs

Author language is estimated from canton and biography information and serves as
a proxy for original text language. Of 10,573 eligible French–German text pairs,
2,245 are classified as French-authored.

The fixed sample contains 10 motions per year. The selected IDs and eligibility
exclusions are recorded in `data/sample_design.json`; reproduction checks this
selection without drawing new motions.

The following inputs are stored in `data/`. The [input-data guide](data/README.md)
explains their fields and how they link together:

| Input | Contents |
|---|---|
| `motion_corpus.json.gz` | Cleaned motion justifications and exclusion flags for 2000–2025: 10,622 records, including 10,581 usable German texts and 10,573 usable German–French pairs |
| `motion_coverage.json` | Yearly retrieval and coverage counts |
| `authors/` | Archived Parliament API author-role and member records |
| `sample_design.json` | Fixed sample IDs, yearly sample size and development exclusions |
| `complexity_fr_author_translations.json` | All 260 translation attempts, model settings and prompts |
| `screening_annotations.csv` | Saved human judgements for the reading sample and automatically flagged texts; reproduction checks their coverage but does not generate the judgements |

The texts and author records were retrieved from the Swiss Parliament’s Curia
Vista open-data service in November 2026. This submission was initially prepared
from commit `3cb3d43` of [the development repository](https://github.com/luisaellamueller/lost-in-translation),
which retains the original raw downloads and development history. The submission
code has since been cleaned and reorganised; the archived source texts,
translation attempts and manual annotations remain the fixed inputs.

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
and place it in `models/`. The following SHA-256 checksum identifies the exact model file used (it is a file fingerprint, not a secret):

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
