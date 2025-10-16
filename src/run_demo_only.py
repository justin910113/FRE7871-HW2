
import os, subprocess, sys, pandas as pd, numpy as np
ROOT = os.path.dirname(os.path.dirname(__file__))
rawE = os.path.join(ROOT, "data", "raw", "events"); os.makedirs(rawE, exist_ok=True)
rawM = os.path.join(ROOT, "data", "raw", "market"); os.makedirs(rawM, exist_ok=True)

# demo events
if not os.path.exists(os.path.join(rawE, "events_text.csv")):
    dates = pd.date_range("2021-01-01", periods=18, freq="MS")
    demo = pd.DataFrame({
        "event_id": [str(100000+i) for i in range(len(dates))],
        "doc_id": [f"doc_{i}" for i in range(len(dates))],
        "event_dt_et": dates,
        "event_type": ["PressRelease"]*len(dates),
        "title": [f"FOMC statement demo {i}" for i in range(len(dates))],
        "url": [f"https://example.com/{i}" for i in range(len(dates))],
        "text": np.where(np.arange(len(dates))%2==0,
                         "Policy remains restrictive with inflation persistent and labor strong.",
                         "Signs of softening demand and downside risks; policy sufficiently restrictive."),
        "word_count": [12]*len(dates)
    })
    demo.to_csv(os.path.join(rawE, "events_text.csv"), index=False)

# demo market
if not os.path.exists(os.path.join(rawM, "h15_rates.csv")):
    rng = np.random.default_rng(0)
    h15 = pd.DataFrame({
        "date": pd.date_range("2020-12-01", periods=600, freq="D"),
        "dgs2": 0.5 + np.cumsum(rng.normal(0, 0.01, 600)),
        "dgs10": 1.1 + np.cumsum(rng.normal(0, 0.01, 600)),
        "effr": 0.1 + np.cumsum(rng.normal(0, 0.001, 600)),
    })
    h15.to_csv(os.path.join(rawM, "h15_rates.csv"), index=False)

if not os.path.exists(os.path.join(rawM, "zq_daily.csv")):
    rng = np.random.default_rng(1)
    zq = pd.DataFrame({"date": pd.date_range("2020-12-01", periods=600, freq="D"),
                       "Close": 96 + np.cumsum(rng.normal(0, 0.02, 600))})
    zq.to_csv(os.path.join(rawM, "zq_daily.csv"), index=False)

def run(p): print(">>", p); r = subprocess.run([sys.executable, p], cwd=ROOT); r.check_returncode()
def main():
    run("src/analysis.py"); run("src/plots.py"); run("src/build_report.py")
    print("DEMO finished, check outputs/。")
if __name__ == "__main__":
    main()
