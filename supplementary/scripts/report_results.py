"""Present supplementary results with the same reports and figures as the main analysis.

Reuse the main reporting functions so corresponding files have matching layouts.
Run after compare_balanced_sample.py and compare_other_results.py.
"""
from pathlib import Path
import json
import csv
import sys

ROOT = Path(__file__).resolve().parents[2]
SUPPLEMENT = ROOT / 'supplementary'
RESULTS = SUPPLEMENT / 'results'
sys.path.insert(0, str(ROOT / 'scripts'))
import report_complexity_comparison as complexity
import compare_translation_complexity as details
import compare_translation_similarity as similarity
import adjust_similarity_for_source as adjustment
import compare_sentence_counts as counts
import compare_tree_depth as depth
from check_swiss_conventions import convention_counts, check_terms, abbreviation_summary
from screen_translations import screen_translations
from translate_sample import save_checkpoint


# Write each sample using the original report layouts and matching file names.
def report_sample(name, measurements, other, translations):
    folder = RESULTS / name
    (folder / 'data').mkdir(parents=True, exist_ok=True)
    records = measurements['records']
    ids = {row['document_id'] for row in records}
    sample = [row for row in translations if row['document_id'] in ids]
    years = {row['document_id']: row['year'] for row in sample}
    measurements.update(attempted_count=len(sample), completed_count=len(sample), excluded_failures=[])
    measurements['uncertainty'] = measurements['uncertainty'].replace('Author dependence and multiple comparisons are examined separately in the robustness analysis.', 'Author-adjusted mixed models and multiple-comparison correction have not been repeated for this sample.')
    save_checkpoint(measurements, folder / 'data/translation_complexity.json')
    pairs = [(row['document_id'], row['official'], row['generated']) for row in records]
    figure_rows = complexity.save_report(measurements, pairs, years, folder / 'translation_complexity_summary.md', author_check=False)
    complexity.save_figure(figure_rows, folder / 'figures/complexity_differences.png')
    details.save_report(measurements, folder / 'translation_complexity_details.md')

    # The conventions and terminology tables already use the shared reporting rules.
    (folder / 'swiss_writing_conventions.md').write_text(convention_counts(sample).replace("(character_conventions.md)", "(../../../results/character_conventions.md)"))
    lines, matches, contexts = check_terms(sample)
    for filename, rows in (("terminology_matches.csv", matches), ("terminology_examples.csv", contexts)):
        with (folder / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    lines += abbreviation_summary(sample)
    lines += ['', '## Review status', '', 'New terminology matches have not been manually checked. Term presence anywhere in a document does not guarantee correct translation of every occurrence. See [screening](translation_screening.md) and [terminology examples](terminology_examples.csv).']
    (folder / 'swiss_terminology.md').write_text('\n'.join(lines)+'\n')

    # Reuse saved scores, and add the original document-bootstrap trend and figure.
    scores = [{key: row[key] for key in ('document_id', 'year', 'chrf', 'bleu')} for row in other['trend']['records']]
    similarity.save_report(scores, other['periods'], similarity.estimate_trend(scores), folder)
    similarity.save_figure(other['periods'], folder)
    adjustment.save_report(other['trend'], folder)

    # Recount sentences with the original rule-based counting pipeline.
    french = counts.pipeline('fr', [row['input_fr'] for row in sample])
    german = counts.pipeline('de', [row[key] for row in sample for key in ('reference_de', 'translation_de')])
    sentence_records = counts.measure_versions(sample, french, german)
    measured = {row['document_id']: row for row in records}
    mismatches = [{'document_id': row['document_id'], 'version': version, 'metric': metric}
                  for row in sentence_records for version in ('official', 'generated')
                  for metric in ('sentence_count', 'word_count')
                  if row[version][metric] != measured[row['document_id']][version][metric]]
    output = {'analyses': {'punctuation_and_lines': {'summary': counts.summarize(sentence_records), 'records': sentence_records}}}
    save_checkpoint(output, folder / 'data/source_sentence_counts.json')
    counts.save_report(output, mismatches, folder)

    # Recover source measurements already saved for the source-adjusted model.
    source = {row['document_id']: row for row in other['trend']['records']}
    tree_records = [{**row, 'year': years[row['document_id']], 'source': {
        'mean_sentence_words': source[row['document_id']]['source_mean_sentence_words'],
        'mean_sentence_tree_depth': source[row['document_id']]['source_mean_sentence_tree_depth']}}
        for row in records]
    summary = {depth.DEPTH: {'raw': depth.associations(tree_records), 'length_adjusted': depth.associations(tree_records, adjusted=True)}}
    save_checkpoint({'n': len(sample), 'summary': summary, 'records': tree_records}, folder / 'data/source_tree_depth.json')
    depth.save_report(summary, len(sample), folder)

    # Keep manual-review status explicit rather than copying the original annotations.
    flags = screen_translations(sample)
    save_checkpoint(flags, folder / 'data/translation_screening.json')
    (folder / 'translation_screening.md').write_text(
        f'# Screening of machine translations\n\n{len(sample)} completed outputs.\n\n## Automatic checks\n\n'
        f'French-word flags: {len(flags["french_flag"])}; repetition flags: {len(flags["repeat_flag"])}. Flags identify cases for inspection, not confirmed errors.\n\n'
        '## Manual review\n\nThe original report annotations apply only to the original sample. New supplementary cases have not been manually reviewed.\n\n'
        '## Supporting data\n\nFlagged IDs are saved in [translation_screening.json](data/translation_screening.json).\n')
    names = ['translation_complexity_summary', 'translation_complexity_details', 'swiss_writing_conventions', 'swiss_terminology', 'translation_screening', 'translation_similarity', 'source_adjusted_similarity', 'source_sentence_counts', 'source_tree_depth']
    (folder / 'README.md').write_text(f'# Supplementary results: {name.replace("_", " ")}\n\n{len(sample)} pairs. File names, tables and figures match the corresponding main results.\n\n'+ '\n'.join(f'- [{title.replace("_", " ").capitalize()}]({title}.md)' for title in names)+'\n\nAuthor-adjusted complexity models and corpus-wide character trends are not repeated here.\n')
    print(f'  Reports: supplementary/results/{name}/README.md', flush=True)


def main():
    measurements = json.loads((RESULTS / 'balanced_complexity.json').read_text())['comparisons']
    other = json.loads((RESULTS / 'other_results.json').read_text())
    translations = json.loads((ROOT / 'data/complexity_fr_author_translations.json').read_text())['records']
    for path in sorted((SUPPLEMENT / 'data').glob('additional_translations*.json')):
        translations.extend(json.loads(path.read_text())['records'])
    for name in ('expanded', 'new_only'):
        report_sample(name, measurements[name], other[name], translations)


if __name__ == '__main__':
    main()
