"""Compare the maximum balanced extension with the report's fixed sample.

Run: python supplementary/scripts/compare_balanced_sample.py
Keeps original completed pairs and randomly adds completed translations up to
23 per year (the smallest eligible yearly pool). Selection does not use scores.
All outputs stay in supplementary/; reproduce.sh and report inputs are unchanged.
"""
import csv
import gzip
import json
from pathlib import Path
import random
import sys
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
SUPPLEMENT = ROOT / "supplementary"
DATA = SUPPLEMENT / "data"
OUT = SUPPLEMENT / "results"
sys.path.insert(0, str(ROOT / 'scripts'))
from linguistic_measures import load_parser, measure_pairs, summarise_pairs, REPORTED_MEASURES
from compare_translation_complexity import add_bootstrap_intervals
from screen_translations import screen_translations
from translate_sample import save_checkpoint


def main():
    design = json.loads((ROOT / 'data/sample_design.json').read_text())
    original = json.loads((ROOT / 'data/complexity_fr_author_translations.json').read_text())
    with (ROOT / 'results/data/french_authored_motions.csv').open() as handle:
        french_ids = {int(row['document_id']) for row in csv.DictReader(handle)}
    with gzip.open(ROOT / 'data/motion_corpus.json.gz', 'rt', encoding='utf-8') as handle:
        corpus = json.load(handle)['records']
    eligible = {r['document_id']: r for r in corpus if r['document_id'] in french_ids
                and r['document_id'] not in design['excluded_development_ids']
                and r['exclusion_de'] is None and r['exclusion_fr'] is None
                and r['input_fr'] and r['reference_de']}
    counts = Counter(r['year'] for r in eligible.values())
    target = min(counts[y] for y in range(2000, 2026))
    extra = []
    for path in sorted(DATA.glob('additional_translations*.json')):
        batch = json.loads(path.read_text())
        for key in ('model_file', 'settings', 'source_language', 'target_language'):
            if batch[key] != original[key]:
                raise ValueError(f'Mismatched generation metadata: {path.name}: {key}')
        extra.extend(batch['records'])
    all_records = original['records'] + extra
    assert len(all_records) == len({r['document_id'] for r in all_records})
    for row in all_records:
        assert row['finish_reason'] == 'stop' and row['translation_de'].strip()
        assert all(row[k] == v for k, v in eligible[row['document_id']].items())
    generator = random.Random(51)
    selected, added = [], []
    for year in range(2000, 2026):
        existing = [r for r in original['records'] if r['year'] == year]
        candidates = sorted([r for r in extra if r['year'] == year], key=lambda r: r['document_id'])
        chosen = generator.sample(candidates, target - len(existing))
        selected.extend(existing + chosen)
        added.extend(chosen)
    assert Counter(r['year'] for r in selected) == {y: target for y in range(2000, 2026)}
    # Use an equal-sized, non-overlapping-with-original check of additional translations.
    independent = []
    per_year = min(Counter(r['year'] for r in added).values())
    generator = random.Random(52)
    for year in range(2000, 2026):
        independent.extend(generator.sample([r for r in added if r['year'] == year], per_year))
    save_checkpoint({'seed': 51, 'per_year': target, 'selected_ids': [r['document_id'] for r in selected],
                     'new_only_seed': 52, 'new_only_ids': [r['document_id'] for r in independent],
                     'eligible_year_counts': dict(counts)}, DATA / 'balanced_design.json')
    print(f'Balanced sample: {len(selected)} ({target}/year); new-only check: {len(independent)}.', flush=True)
    base = json.loads((ROOT / 'results/data/translation_complexity.json').read_text())
    print(f'Measuring {len(added)} additional pairs with shared report functions...', flush=True)
    parser = load_parser([r[k] for r in added for k in ('reference_de', 'translation_de')])
    measurements = base['records'] + measure_pairs(added, parser)
    measured = {r['document_id']: r for r in measurements}
    results = {}
    for name, records in [('expanded', selected), ('new_only', independent)]:
        rows = [measured[r['document_id']] for r in records]
        result = {'records': rows, 'summary': summarise_pairs(rows)}
        add_bootstrap_intervals(result, records)
        results[name] = result
    flags = screen_translations(added)
    save_checkpoint({'comparisons': results, 'new_translation_screening': flags}, OUT / 'balanced_complexity.json')
    lines = ['# Supplementary balanced complexity comparison', '',
             f'The expanded sample contains {len(selected)} pairs ({target} per year, 2000–2025), retaining all 259 completed report pairs. The smallest eligible yearly pool (2002) limits the balanced total. Random additions use seed 51.', '',
             f'The new-only comparison uses {len(independent)} pairs ({per_year} per year; seed 52) with no overlap with the original sample. It is a subset of the expanded sample.', '',
             'Differences are machine minus official German. Intervals use the report’s 2,000 within-year paired bootstrap resamples. They do not adjust for repeated authors or multiple comparisons. Selection was made without inspecting the new linguistic scores.', '',
             '| Measure | Original difference | Expanded difference [95% CI] | New-only difference [95% CI] | Expanded / new-only pairs |',
             '|---|---:|---:|---:|---:|']
    for key, label, _ in REPORTED_MEASURES:
        original_mean = base['summary'][key]['mean_difference']
        entries = []
        for name in ('expanded', 'new_only'):
            s = results[name]['summary'][key]
            lo, hi = s['paired_bootstrap_ci95']
            entries.append(f"{s['mean_difference']:+.3f} [{lo:+.3f}, {hi:+.3f}]")
        counts_text = ' / '.join(str(results[n]['summary'][key]['paired_count']) for n in ('expanded', 'new_only'))
        lines.append(f'| {label} | {original_mean:+.3f} | {entries[0]} | {entries[1]} | {counts_text} |')
    lines += ['', '## Screening and scope', '',
              f"All {len(added)} added outputs stopped normally. Automated French-word flags: {len(flags['french_flag'])}; repetition flags: {len(flags['repeat_flag'])}.", '',
              'These new flags have not yet been manually reviewed; completed generation does not guarantee translation accuracy. No new human quality annotations are claimed. The original analyses and report sample remain unchanged.', '',
              'This table reports all seven complexity measures. Conventions, terminology and similarity are analysed separately by compare_other_results.py.', '',
              'Run from the repository root: `python supplementary/scripts/compare_balanced_sample.py`. Requires the analysis dependencies and both completed supplementary batches.']
    (OUT / 'balanced_complexity_summary.md').write_text('\n'.join(lines)+'\n')
    print('Saved supplementary/results/balanced_complexity_summary.md', flush=True)


if __name__ == '__main__':
    main()
