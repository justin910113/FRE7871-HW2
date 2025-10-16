
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(__file__))
PROC = os.path.join(ROOT, "data", "processed")
OUTF = os.path.join(ROOT, "outputs", "figures")
os.makedirs(OUTF, exist_ok=True)

def boxplots(ev):
    groups = ["Dovish (Bottom 1/3)","Neutral (Mid 1/3)","Hawkish (Top 1/3)"]
    for col in ["d_y2y_bp","d_y10y_bp","d_ff_bp"]:
        fig = plt.figure()
        data = [ev.loc[ev["group3"]==g, col].dropna().values for g in groups]
        plt.boxplot(data, labels=["Dovish","Neutral","Hawkish"])
        plt.title(f"{col} by Hawkishness Group"); plt.xlabel("Group"); plt.ylabel("Change (bp)")
        plt.savefig(os.path.join(OUTF, f"fig_box_{col}.png"), bbox_inches="tight"); plt.close()

def scatter(ev):
    for col in ["d_y2y_bp","d_y10y_bp","d_ff_bp"]:
        x = ev["hawkish_score_event"].values; y = ev[col].values
        m = np.isfinite(x) & np.isfinite(y); x, y = x[m], y[m]
        if len(y) < 5: continue
        A = np.vstack([x, np.ones_like(x)]).T; beta, alpha = np.linalg.lstsq(A, y, rcond=None)[0]
        xs = np.linspace(x.min(), x.max(), 100); ys = beta*xs + alpha
        fig = plt.figure(); plt.scatter(x, y); plt.plot(xs, ys)
        plt.title(f"{col} vs Hawkish Score"); plt.xlabel("Hawkish Score"); plt.ylabel("Change (bp)")
        plt.savefig(os.path.join(OUTF, f"fig_scatter_{col}.png"), bbox_inches="tight"); plt.close()

def main():
    ev = pd.read_csv(os.path.join(PROC, "event_level_changes_grouped.csv"))
    boxplots(ev); scatter(ev)

if __name__ == "__main__":
    main()
