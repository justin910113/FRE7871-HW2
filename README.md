FOMC Communication Impact Analysis (since Oct 2020)

Analyze how dovish/hawkish FOMC communications move key U.S. rate benchmarks (2Y/10Y Treasuries, Fed Funds futures). The pipeline fetches Fed texts, builds a hawkishness score, computes event-window moves, runs significance tests (Welch t-tests) and OLS with Newey–West (HAC), then exports tables, figures, and a short report.

1) Quick Start

Prerequisites

Python 3.9+ (3.10–3.12 recommended)

Internet access (for live data; not needed for demo mode)

A free FRED API Key (paste into config.yaml, no env vars required)

Setup (Windows / macOS / Linux)
# 1) cd into the project root (the folder containing src/, config.yaml)
python -m venv .venv

# 2) activate the venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3) install dependencies
pip install -r requirements.txt

Configure FRED key (no environment variables needed)

Open config.yaml and paste your key:

fred:
  api_key: "YOUR_FRED_API_KEY"
  series: { dgs2: "DGS2", dgs5: "DGS5", dgs10: "DGS10", effr: "EFFR" }


Fed Funds futures use Yahoo Finance (ZQ=F) and do not require a key.

One-command full run (fetch → analyze → charts → report)
python src/run_pipeline.py

----------------------------------------------------------------------------

Where are the outputs?

Tables → outputs/tables/

tableA_event_summary.csv

tableB_group_means_ttest.csv

tableC_ols_hac.csv

Figures → outputs/figures/

fig_box_*.png (boxplots by terciles)

fig_scatter_*.png (scatter + fitted line)


2) Demo Mode (no internet, no keys)

Use bundled demo data to smoke-test the pipeline end-to-end:

python src/run_demo_only.py


This produces the same folders/files under outputs/, using synthetic event/market data.

--------------------------------------------------------------------------------------------

3) What the Pipeline Does

Fetch Fed communications (src/fetch_fed_events.py)

Scrapes federalreserve.gov RSS feeds (Monetary Policy press releases, Speeches) since the start_date in config.yaml.

Saves raw text to data/raw/events/events_text.csv.

Fetch markets (src/fetch_market_free.py)

FRED H.15: DGS2, DGS5, DGS10, EFFR → data/raw/market/h15_rates.csv.

ZQ futures (Yahoo Finance: ZQ=F) and implied rate = 100 - Price → data/raw/market/zq_daily.csv.

Score hawkishness & align markets (src/analysis.py)

Dictionary method on text (wordlists in wordlists/).

Event-level score = word-count–weighted average across documents for the same event.

Event window = from the last trading day ≤ event time to the first trading day > event time (robust to weekends/holidays).

Exports:

data/processed/events_scored.csv

data/processed/market_daily.csv

data/processed/event_level_changes.csv

outputs/tables/* (Tables A–C)

Charts (src/plots.py)

Boxplots by terciles of hawkishness

Scatter plots (Δbp vs hawkishness) with fitted line

Short report (src/build_report.py)

Markdown/HTML summary listing methods and output file paths.

4) Configuration

Edit config.yaml:

start_date: "2020-10-01"     # analysis begins Oct 2020 (required by assignment)
end_date: null               # or set e.g. "2025-10-01"
timezone: "America/New_York"

fred:
  api_key: "YOUR_FRED_API_KEY"
  series: { dgs2: "DGS2", dgs5: "DGS5", dgs10: "DGS10", effr: "EFFR" }

futures:
  zq_symbol: "ZQ=F"

events:
  use_press_release_rss: true
  use_speeches_rss: true

event_window: { pre_days: 1, post_days: 1 }  # kept for reference; the code uses prev/next trading day logic

scoring:
  method: "dictionary"
  min_words: 50
  type_weights: { Statement: 1.0, PressConf: 1.0, Minutes: 0.8, Speech: 0.7 }

grouping:
  quantiles: [0.3333, 0.6667]


Customize wordlists: edit wordlists/hawk_words.txt and wordlists/dove_words.txt.

Focus on specific event types (optional):
Inside score_events() you can filter (e.g., only Press Releases) before aggregation:

docs = docs[docs["event_type"].isin(["PressRelease"])]


5) Folder Structure (key items)
project_root/
├─ config.yaml
├─ requirements.txt
├─ wordlists/
│  ├─ hawk_words.txt
│  └─ dove_words.txt
├─ src/
│  ├─ fetch_fed_events.py
│  ├─ fetch_market_free.py
│  ├─ analysis.py
│  ├─ plots.py
│  ├─ run_pipeline.py
│  └─ run_demo_only.py
├─ data/
│  ├─ raw/
│  │  ├─ events/ (events_text.csv)
│  │  └─ market/ (h15_rates.csv, zq_daily.csv)
│  └─ processed/ (...intermediate csvs...)
└─ outputs/
   ├─ tables/
   ├─ figures/
