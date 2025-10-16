
import os
import pandas as pd
from fredapi import Fred
import yfinance as yf
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT = os.path.join(ROOT, "data", "raw", "market")
os.makedirs(OUT, exist_ok=True)

def fetch_h15(start_date, end_date, api_key, series_map):
    fred = Fred(api_key=api_key or os.environ.get("FRED_API_KEY"))
    cols = {}
    for name, code in series_map.items():
        s = fred.get_series(code, observation_start=start_date, observation_end=end_date)
        cols[name] = s
    df = pd.DataFrame(cols); df.index.name = "date"; df.reset_index(inplace=True)
    path = os.path.join(OUT, "h15_rates.csv"); df.to_csv(path, index=False); return path

def fetch_zq(start_date, end_date, symbol="ZQ=F"):
    end = end_date or datetime.today().strftime("%Y-%m-%d")
    df = yf.download(symbol, start=start_date, end=end, progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = [c[0] for c in df.columns]
    df.reset_index(inplace=True); df.rename(columns={"Date":"date"}, inplace=True)
    path = os.path.join(OUT, "zq_daily.csv"); df.to_csv(path, index=False); return path

def main():
    import yaml
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config.yaml"), "r", encoding="utf-8"))
    start = cfg["start_date"]; end = cfg.get("end_date")
    series = cfg.get("fred",{}).get("series", {"dgs2":"DGS2","dgs10":"DGS10","effr":"EFFR"})
    key = cfg.get("fred",{}).get("api_key")
    zq = cfg.get("futures",{}).get("zq_symbol","ZQ=F")
    print("Fetching H.15..."); print(fetch_h15(start, end, key, series))
    print("Fetching ZQ..."); print(fetch_zq(start, end, zq))

if __name__ == "__main__":
    main()
