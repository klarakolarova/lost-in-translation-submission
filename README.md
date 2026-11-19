# Lost in Translation?

**Klára Kolářová and Luisa Müller · Essentials in Text and Speech Processing, 2026**

This submission compares TranslateGemma 4B translations of French Swiss parliamentary
motion justifications with their official German versions. It contains the final
analyses for the report, including the source-structure and chrF robustness checks.
The report PDF is submitted separately.

## Run the analysis

Python 3.14 was used for validation. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
bash reproduce.sh
```

The run takes a few minutes. After installation it works offline, using the saved
translations and historical scores. It recreates the tables, figures and derived
measurements, then runs the tests. It does not generate new translations or
redownload data. Small floating-point and figure-rendering differences can occur
between environments.

## Where to start

| Location | Purpose |
|---|---|
| `reproduce.sh` | The analysis steps in execution order |
| `scripts/` | One named script per analysis; shared measurements in `metrics.py` |
| `data/` | Fixed inputs, including the original translation attempts and screening annotations |
| `results/*.md` and `results/*.csv` | Readable tables and term-by-term evidence |
| `results/figures/` | Figures used in the report; `design_tikz.tex` is the static study diagram |
| `results/data/` | Recomputed sample, author labels and per-document measurements |
| `tests/` | Checks of sampling, measurement rules and reported results |

## Code and report

| Report analysis | Scripts | Main result |
|---|---|---|
| Corpus and sample | `authors.py`, `sample.py` | 2,245 eligible French-author pairs; the same 260 sampled motions |
| RQ1: German complexity | `metrics.py`, `complexity.py`, `complexity_report.py` | `rq1_complexity.md`, `complexity_details.md`, Figure 2 (`paired_differences.png`) |
| RQ1: repeated authors | `author_robustness.py` | `author_robustness.md` |
| French-source preservation | `source_structure.py`, `source_syntax.py` | Sentence-count matching and raw/length-adjusted tree-depth correlations |
| RQ2: terminology and conventions | `terminology.py` | `terminology_french.md`, convention counts and term contexts |
| Translation screening | `screening.py` | `screening_french.md` |
| RQ3: similarity over time | `similarity.py` | `similarity.md`, Figure 3 |
| RQ3: source adjustment | `source_adjustment.py` | `similarity_source_adjustment.md` |
| RQ3: special characters | `character_trends.py` | `character_trends.md` |
| Historical appendix | `history.py` | `historical_summary.md`, `historical_complexity.png` |

Author language is a proxy for original text language. The sample retains the
63 eligible completed translations from the earlier sample and fills each year
to 10 motions with seed 48, excluding 30 development documents. These IDs and the
selected sample are recorded in `data/sample_design.json`, so the earlier pilot
files are not needed to reconstruct the final sample.

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
- `historical_scores.json.gz`: the six numerical measures used in the appendix,
  with original yearly summaries and bootstrap intervals. Duplicate sentence
  text and unused measures have been removed from this snapshot.

The texts and author records were retrieved from the Swiss Parliament's Curia Vista
open data service in November 2026. This copy was prepared from commit `3cb3d43` of
[the development repository](https://github.com/luisaellamueller/lost-in-translation),
which retains the original raw downloads and development history. Input text,
translation attempts, annotations and numerical results are preserved.

## Optional regeneration

These slower steps are not part of the normal run:

- **Corpus:** `python scripts/collect_corpus.py` downloads raw pages and writes a
  rebuilt corpus under `results/`, leaving the submitted inputs intact. The live
  API can change; archived inputs define the report's dataset.
- **Historical scores:** `python scripts/history.py --rescore` reparses all
  10,581 German texts and writes new scores under `results/data/`. Subsequent
  appendix runs use these scores if present.
- **Translations:** install `requirements-translation.txt`; place
  `translategemma-4b-it-Q4_K_M.gguf` from
  [Menterium's model repository](https://huggingface.co/Menterium/translategemma-4b-it-GGUF)
  in `models/`. Its SHA-256 is
  `e7d9523174272fca61264b339f06d10c6115426267bb0f752b0124084e487b8e`.
  After the normal run has reconstructed the sample, run
  `python scripts/translate.py`. This writes `results/data/translations_rerun.json`
  and resumes from it if interrupted. The main analyses continue to use the
  submitted translations. Generation may differ across hardware and libraries.

## Licence

Code and derived results use the included MIT licence. Parliamentary texts remain
subject to the Parliament's open-data terms; model weights are not included and
retain their own licence.
