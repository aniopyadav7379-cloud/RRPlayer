#!/usr/bin/env bash
# Rebuilds ratings, figures, report PDF and site/data/dash.json from the raw CSVs.
# Usage: RAW_DIR=../data_raw ./run_all.sh   (run from the pipeline/ folder)
set -euo pipefail
export RAW_DIR="${RAW_DIR:-../data_raw}" WORK_DIR="${WORK_DIR:-build}"
mkdir -p "$WORK_DIR" figs
unzip -o -q "$RAW_DIR/ball_by_ball.zip" -d "$WORK_DIR"
python3 build2.py      # win-probability models, leverage, per-ball values  -> balls.pkl
python3 an3.py         # pressure flags + validation tables                  -> balls2.pkl
python3 final1.py      # shrinkage, bootstrap, reliability, robustness       -> out_final.pkl
python3 final2.py      # player tables, CSVs, dash.json
python3 figs.py        # report charts
python3 report.py      # report.html
python3 - <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.goto('file://'+__import__('os').path.abspath('report.html'))
    pg.pdf(path='Pressure_Reliability_Methodology_Report.pdf',format='A4',print_background=True); b.close()
PY
python3 - <<'PY'
import json
d=json.load(open('dash.json')); json.dump(d,open('../site/data/dash.json','w'),separators=(',',':'))
PY
echo "Done. Site data updated in ../site/data/dash.json"
