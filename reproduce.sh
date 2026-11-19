#!/usr/bin/env bash
# Run from any directory after activating the Python environment.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results/data results/figures

echo "1/5 Author language and fixed sample"
python scripts/authors.py
python scripts/sample.py

echo "2/5 Complexity and French-source structure"
python scripts/complexity.py
python scripts/complexity_report.py
python scripts/author_robustness.py
python scripts/source_structure.py
python scripts/source_syntax.py

echo "3/5 Terminology, conventions and translation screening"
python scripts/terminology.py
python scripts/screening.py

echo "4/5 Similarity over time and historical appendix"
python scripts/similarity.py
python scripts/source_adjustment.py
python scripts/character_trends.py
python scripts/history.py

echo "5/5 Verification"
python -m pytest -q
echo "Finished. Tables: results/; figures: results/figures/."
