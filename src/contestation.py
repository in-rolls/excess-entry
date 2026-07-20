"""
contestation.py -- how many candidates contest a GP-head seat, by
reservation status, across states and cycles, with the p25/p50/p75
distribution and the effective number of candidates (vote splitting).

Reads tables/candidates.csv.gz from build.py.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np, pandas as pd


def eff_n(votes) -> float:
    v = pd.to_numeric(votes, errors="coerce").fillna(0).clip(lower=0)
    t = v.sum()
    if t <= 0:
        return np.nan
    p = v / t
    return 1.0 / (p ** 2).sum()


def seat_frame(cand: pd.DataFrame) -> pd.DataFrame:
    g = cand.groupby("seat_id")
    seat = g.agg(state=("state", "first"), year=("year", "first"),
                 n_cand=("cand_name", "size"),
                 woman_seat=("woman_seat", "max"), caste=("caste", "first")).reset_index()
    en = g.apply(lambda d: eff_n(d.votes), include_groups=False)
    seat["eff_n"] = seat.seat_id.map(en)
    seat["cell"] = seat.caste + np.where(seat.woman_seat == 1, " (W)", "")
    seat["reservation"] = np.where(seat.woman_seat == 1, "Women-reserved", "Open")
    return seat


def _dist(g, col="n_cand"):
    return pd.Series({"seats": g[col].size, "mean": g[col].mean(),
                      "p25": g[col].quantile(.25), "p50": g[col].quantile(.50),
                      "p75": g[col].quantile(.75),
                      "mean_eff_n": g["eff_n"].mean(), "p50_eff_n": g["eff_n"].quantile(.50)})


def main(cand_path, outdir, figdir):
    out, fig = Path(outdir), Path(figdir)
    out.mkdir(parents=True, exist_ok=True); fig.mkdir(parents=True, exist_ok=True)
    seat = seat_frame(pd.read_csv(cand_path, low_memory=False))
    seat.to_csv(out / "seat_level.csv.gz", index=False, compression="gzip")

    by_state = seat.groupby(["state", "year"]).apply(_dist, include_groups=False).round(2).reset_index()
    by_res = seat.groupby(["state", "year", "reservation"]).apply(_dist, include_groups=False).round(2).reset_index()
    by_cell = seat.groupby(["state", "cell"]).apply(_dist, include_groups=False).round(2).reset_index()
    by_state.to_csv(out / "contestation_by_state_year.csv", index=False)
    by_res.to_csv(out / "contestation_by_reservation.csv", index=False)
    by_cell.to_csv(out / "contestation_by_caste_x_woman.csv", index=False)
    print(by_state.to_string(index=False))

    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                             "axes.spines.right": False, "figure.dpi": 140,
                             "font.family": "DejaVu Sans"})
        agg = by_state.groupby("state").agg(raw=("mean", "mean"), eff=("mean_eff_n", "mean"))
        order = ["Uttarakhand", "Rajasthan", "UP", "Bihar"]
        agg = agg.reindex(order)
        x = np.arange(len(order)); w = .38
        f, ax = plt.subplots(figsize=(7.5, 4.4)); f.subplots_adjust(top=0.83)
        ax.bar(x - w/2, agg.raw, w, color="#9aa0a6", label="On ballot")
        ax.bar(x + w/2, agg.eff, w, color="#b3202c", label="Effective (vote-weighted)")
        for i, (r, e) in enumerate(zip(agg.raw, agg.eff)):
            ax.text(i - w/2, r + .2, f"{r:.1f}", ha="center", fontsize=9)
            if e == e:
                ax.text(i + w/2, e + .2, f"{e:.1f}", ha="center", fontsize=9, color="#b3202c")
        ax.set_xticks(x); ax.set_xticklabels(order); ax.set_ylabel("Candidates per GP-head seat")
        ax.legend(frameon=False, fontsize=9)
        f.suptitle("Candidates per gram-panchayat head seat", x=.06, ha="left",
                   fontsize=12, fontweight="bold", y=.96)
        f.text(.06, .88, "Bihar averages 12 on the ballot but ~6 effective; Uttarakhand ~3 with little splitting.",
               fontsize=8.5, color="#555")
        f.savefig(fig / "contestation.png", bbox_inches="tight")
        print("figure -> contestation.png")
    except Exception as e:
        print("(figure skipped:", e, ")")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", default="tables/candidates.csv.gz")
    ap.add_argument("--outdir", default="tables"); ap.add_argument("--figdir", default="figures")
    a = ap.parse_args()
    main(a.cand, a.outdir, a.figdir)
