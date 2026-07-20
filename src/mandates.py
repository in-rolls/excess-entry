"""
mandates.py -- the excess-entry footprint in vote shares. More candidates
mean weaker plurality winners and more seats where the trailing vote could
have flipped the result ("split-decided"). We cannot detect Condorcet
cycles (no ranked ballots), but this is the observable condition under
which the plurality winner is unlikely to be the majority's choice.

split-decided := votes held by 3rd-place-and-below candidates exceed the
winner's margin over the runner-up.

Uses states with per-candidate votes (Bihar, UP, Uttarakhand; not Rajasthan).
Reads tables/candidates.csv.gz.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np, pandas as pd


def per_seat(cand: pd.DataFrame) -> pd.DataFrame:
    d = cand.dropna(subset=["votes"]).copy()
    d = d[d.votes >= 0]

    def f(x):
        v = np.sort(x.votes.values)[::-1]
        t = v.sum()
        if t <= 0:
            return None
        s = v / t
        s1 = s[0]; s2 = s[1] if len(s) > 1 else 0.0
        elim = s[2:].sum() if len(s) > 2 else 0.0
        return pd.Series({"state": x.state.iloc[0], "n": len(v), "win": s1,
                          "margin": s1 - s2, "split_decided": int(elim > (s1 - s2))})
    return d.groupby("seat_id").apply(f, include_groups=False).dropna()


def main(cand_path, outdir, figdir):
    out, fig = Path(outdir), Path(figdir)
    ps = per_seat(pd.read_csv(cand_path, low_memory=False))
    summ = (ps.groupby("state")
            .apply(lambda x: pd.Series({
                "seats": len(x), "mean_winner_share": x.win.mean(),
                "median_winner_share": x.win.median(),
                "pct_winner_below_50": (x.win < .5).mean() * 100,
                "pct_winner_below_33": (x.win < 1/3).mean() * 100,
                "pct_split_decided": x.split_decided.mean() * 100}), include_groups=False)
            .round(2).reset_index())
    summ.to_csv(Path(outdir) / "mandates_by_state.csv", index=False)
    print(summ.to_string(index=False))

    # by candidate count
    ps["nb"] = pd.cut(ps.n, [0, 2, 4, 6, 9, 100], labels=["2", "3-4", "5-6", "7-9", "10+"])
    bycount = (ps.groupby(["state", "nb"], observed=True)
               .agg(seats=("win", "size"), winner_share=("win", "mean"),
                    split_decided=("split_decided", "mean")).round(3).reset_index())
    bycount.to_csv(Path(outdir) / "mandates_by_candidate_count.csv", index=False)

    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        plt.rcParams.update({"font.size": 10.5, "axes.spines.top": False,
                             "axes.spines.right": False, "figure.dpi": 140,
                             "font.family": "DejaVu Sans"})
        f, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4)); f.subplots_adjust(top=0.80, wspace=.27)
        xs = np.arange(2, 13)
        cols = {"Bihar": "#b3202c", "UP": "#1f6f8b", "Uttarakhand": "#2a6f4e"}
        for st, c in cols.items():
            d = ps[(ps.state == st) & ps.n.between(2, 12)]
            a1.plot(xs, d.groupby("n").win.mean().reindex(xs), "o-", color=c, ms=4, label=st)
            a2.plot(xs, d.groupby("n").split_decided.mean().reindex(xs) * 100, "o-", color=c, ms=4, label=st)
        a1.axhline(.5, ls="--", color="#999", lw=1); a1.set_ylim(0, .75)
        a1.set_ylabel("Winner's vote share"); a1.set_xlabel("Candidates on ballot")
        a2.set_ylabel("% seats split-decided"); a2.set_xlabel("Candidates on ballot"); a2.set_ylim(0, 105)
        a1.legend(frameon=False, fontsize=9)
        a1.set_title("Winners win with less", fontsize=10.5, fontweight="bold", loc="left")
        a2.set_title("...and the field could have flipped it", fontsize=10.5, fontweight="bold", loc="left")
        f.suptitle("Excess entry erodes the mandate", x=.05, ha="left", fontsize=12, fontweight="bold", y=.965)
        f.savefig(fig / "mandates.png", bbox_inches="tight")
        print("figure -> mandates.png")
    except Exception as e:
        print("(figure skipped:", e, ")")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", default="tables/candidates.csv.gz")
    ap.add_argument("--outdir", default="tables"); ap.add_argument("--figdir", default="figures")
    a = ap.parse_args()
    main(a.cand, a.outdir, a.figdir)
