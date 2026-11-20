# Input data

These are the fixed inputs used to reproduce the report. Generated measurements
and summaries are stored separately in `results/`. All JSON and CSV text uses UTF-8.

## Files and their role

| File | What it contains | Used by |
|---|---|---|
| `motion_corpus.json.gz` | Cleaned German motion justifications and available French counterparts, 2000–2025 | Sample validation, author-pool counts and wider-corpus character checks |
| `motion_coverage.json` | Yearly retrieval totals and counts after cleaning | Documentation of corpus coverage; not required by the analysis calculations |
| `authors/business_roles.json` | Links between motions and their submitting members, committees or parliamentary groups | Author-language classification |
| `authors/members.json` | Member IDs, cantons and biography fields | Author-language classification |
| `sample_design.json` | Selected motion IDs, development exclusions and the number of motions per year | Validation of the fixed sample |
| `complexity_fr_author_translations.json` | Saved model settings, prompts and all translation attempts | Translation screening and the paired analyses |
| `screening_annotations.csv` | Saved human judgements and notes | Translation screening |

The translation filename is retained from data collection. It contains the inputs
for all paired analyses, not just complexity. The compressed corpus can be read
directly with Python’s `gzip` and `json` modules; no manual extraction is needed.

## Motion records

`document_id` identifies the motion and links the corpus, translations and sample.
In author-role records the same identifier is called `BusinessNumber`, following
the original API naming. CSV identifiers are read as text and converted where needed.

| Field | Meaning |
|---|---|
| `year`, `submission_date` | Submission year and date |
| `title_fr`, `title_de` | French and German titles |
| `input_fr` | French justification supplied to the translation model |
| `reference_de` | Published German justification used for comparison |
| `record_url_fr`, `record_url_de` | Links to the source API records |
| `exclusion_fr`, `exclusion_de` | Cleaning exclusion reason, or `null` when none was assigned |

A `null` exclusion alone does not guarantee a usable text: eligibility also
requires nonempty French and German justifications. The corpus contains 10,622
records with German justifications, 10,581 usable German texts and 10,573 usable
French–German pairs. The coverage file also counts retrieved records without
justifications, so its retrieval totals are larger.

## Author records

Both author files retain API field names and retrieval metadata. `MemberCouncilNumber`
in the role file links to `ID` in the member file. `CommitteeNumber` and
`ParlGroupNumber` identify non-member submitters. Canton and the biography fields
`Mandates`, `AdditionalActivity` and `AdditionalMandate` support language estimation;
they do not directly identify the original language of a motion.

The role snapshot has 11,551 entries in `business_ids`, representing 11,550 unique
motions. The repeated ID comes from the retrieved inventory; the classification
script stores one result per motion. The archive is retained as retrieved.

## Sample and translation attempts

`selected_ids` fixes the 260 motions, with 10 per year. `excluded_development_ids`
identifies documents reserved for development and excluded from the sample.
Reproduction checks these IDs rather than making a new selection.

The translation file contains:

- `model_file`, `settings`, `source_language`, `target_language`: model identity and generation settings.
- `records`: 259 completed translation attempts.
- `failed_records`: one attempt that reached the output limit, retained for completeness and excluded from comparisons.

Each attempt includes the original motion fields plus `translation_de`, the rendered
`prompt`, `finish_reason`, token counts in `usage`, and `generation_seconds`.
Repeated source fields allow the validation script to confirm that translations
still match the corpus. The prompt and generation metadata document how the saved
output was produced; they are not additional observations.

## Manual screening annotations

Each row identifies a `check`, `document_id`, `judgement` and free-text `note`.
The same motion may appear under different checks.

| Check | Recorded judgements |
|---|---|
| `reading_sample` | `ok`, `minor`, `content`: the saved assessment of the opening approximately 100 words in 20 sampled translations |
| `repetition_flag` | `mirrors_source`: the repeated wording reflects repetition in the French source |
| `french_flag` | `not_untranslated`: the flag does not indicate an untranslated French passage |

An empty note means no explanatory note was recorded. These are human annotations;
the script checks their coverage and reads them without generating new judgements.
Notes containing commas or quotation marks must use standard CSV quoting. Use a
CSV-aware editor or Python’s `csv` writer when editing them.
