#!/usr/bin/env bash
# Run from any directory after activating the Python environment.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results/data results/figures

# Use colours only in an interactive terminal; NO_COLOR disables them.
stage_colour='' script_colour='' path_colour='' success_colour='' reset=''
if [[ -t 1 && "${TERM:-dumb}" != dumb && -z "${NO_COLOR+x}" ]]; then
    stage_colour=$'\033[1;35m'
    script_colour=$'\033[1;36m'
    path_colour=$'\033[36m'
    success_colour=$'\033[1;32m'
    reset=$'\033[0m'
fi

# Highlight output locations while leaving results and warnings as plain text.
show_output() {
    local line label rest path
    while IFS= read -r line || [[ -n "$line" ]]; do
        case "$line" in
            '  Report: '*|'  Data: '*|'  Figure: '*)
                label="${line%%: *}: "
                rest="${line#*: }"
                path="${rest%% *}"
                printf '%s%s%s%s%s\n' "$label" "$path_colour" "$path" "$reset" "${rest#"$path"}"
                ;;
            *) printf '%s\n' "$line" ;;
        esac
    done
}

# Introduce each stage and separate it from the preceding results.
stage() {
    printf '\n%s=== %s ===%s\n%s\n' "$stage_colour" "$1" "$reset" "$2"
}

# Explain each script before running it; scripts print their results and file paths.
run_analysis() {
    printf '\n%s%s%s — %s\n' "$script_colour" "$1" "$reset" "$2"
    python -u "scripts/$1" | show_output
}

printf '%s\n' \
    "Lost in Translation: reproduce the report analyses" \
    "This run uses the saved corpus, translations and manual annotations." \
    "It regenerates analysis outputs and runs the verification tests." \
    "No new translations or downloads are needed. Allow a few minutes." \
    "Descriptions introduce each analysis; the following lines show its results and output files."

stage "Step 1/5: Prepare and check the sample" \
    "Establish the author-language proxy, validate the fixed sample and check translation outputs."
run_analysis classify_author_language.py "Classify author language using canton and biography information."
run_analysis validate_sample.py "Validate the 260 selected motions and their saved translation attempts."
run_analysis screen_translations.py "Screen completed outputs for French words and repetition; verify saved reading assessments."

stage "Step 2/5: Compare linguistic complexity (RQ1)" \
    "Compare machine and official German, then examine repeated authors and French-source structure. Differences are machine minus official German."
run_analysis compare_translation_complexity.py "Measure German complexity and estimate uncertainty in paired differences."
run_analysis report_complexity_comparison.py "Create the complexity comparison table and Figure 2."
run_analysis check_author_dependence.py "Check whether the paired findings persist when accounting for repeated authors."
run_analysis compare_sentence_counts.py "Compare sentence counts in the French sources and both German versions."
run_analysis compare_tree_depth.py "Compare French–German sentence-depth correlations before and after adjusting for length; higher values mean a stronger association."

stage "Step 3/5: Check terminology and conventions (RQ2)" \
    "Check preservation of Swiss institutional terms, abbreviation equivalents and writing conventions."
run_analysis check_swiss_conventions.py "Save terminology counts, convention counts and excerpts for inspection."

stage "Step 4/5: Examine changes over time (RQ3)" \
    "Measure translation similarity by year and compare character conventions in recent official texts."
run_analysis compare_translation_similarity.py "Compare wording over time using chrF (character overlap) and BLEU (word overlap); higher scores mean greater similarity."
run_analysis adjust_similarity_for_source.py "Check whether the chrF trend persists after accounting for French-source properties."
run_analysis compare_character_conventions.py "Compare ß and dash use by author-language group, with a character-storage check."

stage "Step 5/5: Verify the reproduced results" \
    "Run the automated checks of sampling, measurement rules and saved results."
python -m pytest -q

printf '\n%s%s%s\n' "$success_colour" \
    "Reproduction completed successfully; all verification tests passed." "$reset"
printf '%s\n' \
    "Start with results/README.md for a guide to all summaries and supporting files." \
    "Find regenerated figures in results/figures/ and measurements in results/data/." \
    "The README maps each analysis to its scripts and outputs."
