# Pressure Reliability Dashboard

Static dashboard ranking IPL (2022–26) and T20I batters and bowlers by how reliably they deliver under pressure, built for SupeRR Selector Season 2, Round 1.

```
rr-pressure-dashboard/
├── site/                 <- deploy this folder (static, no build step)
│   ├── index.html
│   ├── css/styles.css
│   ├── js/               state.js, charts.js, insights.js, views.js, main.js
│   ├── data/dash.json    all player profiles and rankings (generated)
│   ├── netlify.toml  vercel.json  .nojekyll
├── pipeline/             <- Python that regenerates data, figures and the PDF
├── data_raw/             <- put the raw CSVs here (not included)
└── docs/                 methodology report (PDF) and ranking CSVs
```

## Run locally
```
cd site && python3 -m http.server 8000      # open http://localhost:8000
```
Opening index.html straight from disk will not work, because the page loads `data/dash.json` with `fetch`.

## Deploy (any static host; publish directory = `site`)
- **Netlify**: drag the `site` folder onto app.netlify.com/drop, or connect the repo (`netlify.toml` is included).
- **Vercel**: `cd site && npx vercel --prod` (`vercel.json` is included).
- **GitHub Pages**: push the contents of `site/` to a `gh-pages` branch, or set Pages to serve the `/site` folder via Actions. `.nojekyll` is included.
- **Any web server / S3 / nginx**: upload the contents of `site/`.

## Rebuild the data
```
pip install -r pipeline/requirements.txt && playwright install chromium
cd pipeline && RAW_DIR=../data_raw ./run_all.sh
```
This reruns the win-probability models, pressure flags, shrinkage, bootstrap and robustness checks, rewrites `site/data/dash.json`, and regenerates the report PDF (about 30 seconds).

## Notes
- Fonts load from Google Fonts; the page falls back to system fonts offline.
- Method, reliability results and limits are in `docs/Pressure_Reliability_Methodology_Report.pdf` and the dashboard's "Method and limits" tab.
