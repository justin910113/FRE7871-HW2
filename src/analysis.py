
import os, numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm
from utils_text import DictScorer

ROOT = os.path.dirname(os.path.dirname(__file__))
PROC = os.path.join(ROOT, "data", "processed")
RAW_E = os.path.join(ROOT, "data", "raw", "events")
RAW_M = os.path.join(ROOT, "data", "raw", "market")
OUT_T = os.path.join(ROOT, "outputs", "tables")
os.makedirs(PROC, exist_ok=True); os.makedirs(OUT_T, exist_ok=True)

def load_wordlist(p): return [x.strip() for x in open(p, "r", encoding="utf-8").read().splitlines() if x.strip()]

def score_events():
    docs = pd.read_csv(os.path.join(RAW_E, "events_text.csv"))
    docs["event_dt_et"] = pd.to_datetime(docs["event_dt_et"])
    hawk = load_wordlist(os.path.join(ROOT, "wordlists", "hawk_words.txt"))
    dove = load_wordlist(os.path.join(ROOT, "wordlists", "dove_words.txt"))
    scorer = DictScorer(hawk_terms=hawk, dove_terms=dove)
    s, w = zip(*[scorer.score_doc(str(t)) for t in docs["text"].fillna("")])
    docs["score_doc"] = s; docs["wc"] = w
    g = docs.groupby("event_id", sort=False)

    def wavg_score(s):
        w = docs.loc[s.index, "wc"]
        return float((s * w).sum() / w.sum()) if w.sum() else float("nan")

    evt = g.agg(
        event_dt_et=("event_dt_et", "min"),
        n_docs=("event_id", "size"),
        total_words=("wc", "sum"),
        hawkish_score_event=("score_doc", wavg_score),
    ).reset_index()
    
    evt.to_csv(os.path.join(PROC, "events_scored.csv"), index=False)
    return evt

def prepare_markets():
    h15 = pd.read_csv(os.path.join(RAW_M, "h15_rates.csv"))
    h15["date"] = pd.to_datetime(h15["date"]).dt.date
    zq = pd.read_csv(os.path.join(RAW_M, "zq_daily.csv"))
    zq["date"] = pd.to_datetime(zq["date"]).dt.date
    zq["zq_implied"] = 100.0 - (zq["Close"] if "Close" in zq.columns else zq["Adj Close"])
    mkt = h15.merge(zq[["date","zq_implied"]], on="date", how="outer").sort_values("date")
    mkt.to_csv(os.path.join(PROC, "market_daily.csv"), index=False)
    return mkt

def event_window_changes(evt, pre=1, post=1):
    m = pd.read_csv(os.path.join(PROC, "market_daily.csv"))
    m["date"] = pd.to_datetime(m["date"]).dt.date

    rows = []
    for _, r in evt.iterrows():
        ts = pd.to_datetime(r["event_dt_et"])
        if getattr(ts, "tzinfo", None) is None:
            ts = ts.tz_localize("America/New_York")
        else:
            ts = ts.tz_convert("America/New_York")
        d0 = ts.date()

        pre_row  = m[m["date"] <= d0].tail(1)
        post_row = m[m["date"] >  d0].head(1)
        if len(pre_row)==0 or len(post_row)==0: 
            continue
        def delta(col):
            if col not in m.columns: return np.nan
            pre_v, post_v = pre_row[col].values[0], post_row[col].values[0]
            if pd.isna(pre_v) or pd.isna(post_v): return np.nan
            return float(post_v - pre_v) * 100.0
        rows.append({
            "event_id": r["event_id"],
            "event_dt_et": r["event_dt_et"],
            "hawkish_score_event": r["hawkish_score_event"],
            "d_y2y_bp":  delta("dgs2"),
            "d_y10y_bp": delta("dgs10"),
            "d_ff_bp":   delta("zq_implied"),
        })
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(PROC, "event_level_changes.csv"), index=False)
    return out

def grouping_and_tests(ev):
    ql, qh = ev["hawkish_score_event"].quantile([1/3, 2/3])
    def g(x): 
        return "Dovish (Bottom 1/3)" if x<=ql else ("Hawkish (Top 1/3)" if x>=qh else "Neutral (Mid 1/3)")
    ev["group3"] = ev["hawkish_score_event"].apply(g)
    ev.to_csv(os.path.join(PROC, "event_level_changes_grouped.csv"), index=False)
    top = ev[ev["group3"].str.startswith("Hawkish")]
    bot = ev[ev["group3"].str.startswith("Dovish")]
    rows = []
    for col in ["d_y2y_bp","d_y10y_bp","d_ff_bp"]:
        x, y = top[col].dropna(), bot[col].dropna()
        t, p = (np.nan, np.nan) if (len(x)<2 or len(y)<2) else stats.ttest_ind(x, y, equal_var=False)
        rows.append({"metric": col, "mean_top": x.mean() if len(x) else np.nan, "mean_bottom": y.mean() if len(y) else np.nan,
                     "diff_top_minus_bottom": (x.mean()-y.mean()) if (len(x) and len(y)) else np.nan,
                     "t_stat_welch": t, "p_value": p, "n_top": len(x), "n_bottom": len(y)})
    pd.DataFrame(rows).to_csv(os.path.join(OUT_T, "tableB_group_means_ttest.csv"), index=False)
    return ev

def ols_hac(ev):
    X = sm.add_constant(ev["hawkish_score_event"].values)
    rows = []
    for yname in ["d_y2y_bp","d_y10y_bp","d_ff_bp"]:
        y = ev[yname].values
        mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
        Xi, yi = X[mask], y[mask]
        if len(yi) < 5:
            rows.append({"dep_var": yname, "alpha": np.nan, "beta_hawkish": np.nan,
                         "se_alpha": np.nan, "se_beta": np.nan, "t_alpha": np.nan, "t_beta": np.nan, "R2": np.nan, "n": int(len(yi))})
        else:
            m = sm.OLS(yi, Xi).fit(cov_type="HAC", cov_kwds={"maxlags":2})
            rows.append({"dep_var": yname, "alpha": float(m.params[0]), "beta_hawkish": float(m.params[1]),
                         "se_alpha": float(m.bse[0]), "se_beta": float(m.bse[1]),
                         "t_alpha": float(m.tvalues[0]), "t_beta": float(m.tvalues[1]),
                         "R2": float(m.rsquared), "n": int(m.nobs)})
    pd.DataFrame(rows).to_csv(os.path.join(OUT_T, "tableC_ols_hac.csv"), index=False)

def summary_table(ev):
    row = {
        "n_events": int(len(ev)),
        "hawkish_mean": float(ev["hawkish_score_event"].mean()),
        "hawkish_std": float(ev["hawkish_score_event"].std()),
        "mean_d_y2y_bp": float(ev["d_y2y_bp"].mean()),
        "mean_d_y10y_bp": float(ev["d_y10y_bp"].mean()),
        "mean_d_ff_bp": float(ev["d_ff_bp"].mean()),
    }
    pd.DataFrame([row]).to_csv(os.path.join(OUT_T, "tableA_event_summary.csv"), index=False)

def main():
    evt = score_events()
    _ = prepare_markets()
    evchg = event_window_changes(evt)
    evgrp = grouping_and_tests(evchg)
    ols_hac(evgrp)
    summary_table(evgrp)

if __name__ == "__main__":
    main()
