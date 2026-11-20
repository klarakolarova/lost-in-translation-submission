"""Check conventions, terminology, source structure and similarity in balanced samples.

Run: python supplementary/scripts/compare_other_results.py
Uses the selection saved by compare_balanced_sample.py and shared analysis rules.
New terminology matches are automatic checks, not new human annotations.
"""
import csv
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SUPPLEMENT = ROOT / "supplementary"
DATA = SUPPLEMENT / "data"
OUT = SUPPLEMENT / "results"
sys.path.insert(0, str(ROOT / 'scripts'))
from check_swiss_conventions import convention_counts, check_terms, abbreviation_summary
from compare_translation_similarity import score_pairs, summarise_periods
from adjust_similarity_for_source import compare_trends
from linguistic_measures import load_parser, measure_sentences
from translate_sample import save_checkpoint


def correlation(source, target, adjusted=False):
    x = np.array([r['mean_sentence_tree_depth'] for r in source])
    y = np.array([r['mean_sentence_tree_depth'] for r in target])
    if adjusted:
        for values, records in ((x, source), (y, target)):
            design = np.column_stack([np.ones(len(records)), [r['mean_sentence_words'] for r in records]])
            values -= design @ np.linalg.lstsq(design, values, rcond=None)[0]
    return float(np.corrcoef(x, y)[0, 1])


def main():
    design = json.loads((DATA / 'balanced_design.json').read_text())
    records = json.loads((ROOT / 'data/complexity_fr_author_translations.json').read_text())['records']
    for path in sorted(DATA.glob('additional_translations*.json')):
        records.extend(json.loads(path.read_text())['records'])
    by_id = {r['document_id']: r for r in records}
    selected = [by_id[i] for i in design['selected_ids']]
    measured = {r['document_id']: r for r in json.loads((OUT / 'balanced_complexity.json').read_text())['comparisons']['expanded']['records']}
    with (ROOT / 'results/data/motion_author_language.csv').open() as handle:
        authors = {int(r['document_id']): r['member_id'] for r in csv.DictReader(handle)}
    print('Parsing French sources and scoring translation similarity...', flush=True)
    parser = load_parser([r['input_fr'] for r in selected], 'fr_core_news_sm')
    sources = {r['document_id']: measure_sentences(parser(r['input_fr'])) for r in selected}
    scores = {r['document_id']: r for r in score_pairs(selected)}
    output = {}
    for name, ids in [('expanded', design['selected_ids']), ('new_only', design['new_only_ids'])]:
        sample = [by_id[i] for i in ids]
        folder = OUT / name
        folder.mkdir(exist_ok=True)
        conventions = convention_counts(sample).split('## Related results')[0]
        (folder / 'writing_conventions.md').write_text(conventions)
        lines, matches, contexts = check_terms(sample)
        lines += abbreviation_summary(sample)
        lines += ['', 'These are automated applications of the original terminology rules. New examples have not yet been manually checked. Term presence anywhere in a document does not guarantee every occurrence is correctly translated.']
        (folder / 'terminology.md').write_text('\n'.join(lines)+'\n')
        for filename, data in [('terminology_matches.csv', matches), ('terminology_examples.csv', contexts)]:
            with (folder / filename).open('w', newline='', encoding='utf-8') as handle:
                writer = csv.DictWriter(handle, fieldnames=list(data[0]))
                writer.writeheader(); writer.writerows(data)
        rows = [{**scores[i], 'author': authors[i],
                 'source_mean_sentence_words': sources[i]['mean_sentence_words'],
                 'source_mean_sentence_tree_depth': sources[i]['mean_sentence_tree_depth'],
                 'source_word_count': sources[i]['word_count']} for i in ids]
        assert all(r['author'] for r in rows)
        trend = compare_trends(rows)
        periods = summarise_periods([scores[i] for i in ids])
        structure = {}
        source = [sources[i] for i in ids]
        for version in ('official', 'generated'):
            target = [measured[i][version] for i in ids]
            structure[version] = {
                'sentence_count_matches': sum(s['sentence_count'] == t['sentence_count'] for s,t in zip(source,target)),
                'depth_correlation': correlation(source,target),
                'length_adjusted_depth_correlation': correlation(source,target,True),
            }
        output[name] = {'n': len(ids), 'trend': trend, 'periods': periods, 'source_structure': structure}
        lines = [f'# Supplementary similarity and source structure: {name}', '', f'{len(ids)} pairs.', '',
                 '## Similarity trend', '', 'chrF points per decade; 95% intervals resample authors (2,000 draws).', '',
                 '| Model | Trend | 95% interval |', '|---|---:|---:|']
        for model in ('unadjusted', 'adjusted'):
            s=trend[model]; lo,hi=s['author_bootstrap_95_ci']
            lines.append(f"| {model} | {s['slope_per_decade']:+.3f} | [{lo:+.3f}, {hi:+.3f}] |")
        lines += ['', 'Adjustment includes French mean sentence length, mean maximum sentence depth and log document word count.', '',
                  '| Period | Pairs | Mean chrF | Mean BLEU |', '|---|---:|---:|---:|']
        for p in periods:
            lines.append(f"| {p['period']} | {p['n']} | {p['chrf']:.2f} | {p['bleu']:.2f} |")
        lines += ['', '## Source structure', '', '| German version | Sentence count matches | Depth correlation | Length-adjusted correlation |', '|---|---:|---:|---:|']
        for version,s in structure.items():
            lines.append(f"| {version} | {s['sentence_count_matches']}/{len(ids)} ({100*s['sentence_count_matches']/len(ids):.1f}%) | {s['depth_correlation']:.3f} | {s['length_adjusted_depth_correlation']:.3f} |")
        lines += ['', 'Source correlations are descriptive and do not establish sentence-level structural equivalence. Similarity trends do not establish use of MT by official translators. These supplementary results do not change the report sample.']
        (folder / 'similarity_and_structure.md').write_text('\n'.join(lines)+'\n')
        print(f'Saved supplementary/results/{name}/ summaries.', flush=True)
    save_checkpoint(output, OUT / 'other_results.json')


if __name__ == '__main__':
    main()
