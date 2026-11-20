#!/usr/bin/env bash
# Reproduce the supplementary analyses using saved translations.
set -euo pipefail
cd "$(dirname "$0")/.."
for required in results/data/french_authored_motions.csv results/data/motion_author_language.csv results/data/translation_complexity.json; do
    if [[ ! -f "$required" ]]; then
        printf 'Missing %s. Run bash reproduce.sh first.\n' "$required" >&2
        exit 1
    fi
done
mkdir -p supplementary/results
printf '\n=== Step 1/3: Compare the balanced samples ===\n'
printf 'Reuse the report measurements and measure additional German translations.\n'
python -u supplementary/scripts/compare_balanced_sample.py
printf '\n=== Step 2/3: Check conventions, terminology and similarity ===\n'
printf 'Apply the same rules to the expanded and new-only samples.\n'
python -u supplementary/scripts/compare_other_results.py
printf '\n=== Step 3/3: Create matching reports and figures ===\n'
python -u supplementary/scripts/report_results.py
printf '\nSupplementary reproduction complete. See supplementary/README.md for the results guide.\n'
