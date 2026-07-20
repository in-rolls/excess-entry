"""
namesakes.py -- how often two candidates share an identical name on the
same ballot, a documented vote-splitting/confusion tactic ("dummy"
candidates). Reported against a chance baseline (within-state name shuffle),
and split by father/husband name to separate genuine distinct namesakes
(different father) from data duplicates (same father).

Reads tables/candidates.csv.gz.
Caveats printed in the README: names cluster geographically, so the
within-state shuffle is a permissive baseline; same-name-different-father
is the namesake form but does not prove intent.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np, pandas as pd

RNG = np.random.default_rng(42)


def analyze(cand: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for st, d in cand.groupby("state"):
        d = d[d.cand_name.str.len() > 0]

        def seatstat(x):
            vc = x.cand_name.value_counts()
            namesake = 0
            for nm, c in vc[vc >= 2].items():
                fa = x.loc[x.cand_name == nm, "father_name"]
                if fa.nunique() >= 2 or (fa == "").all():
                    namesake = 1
            return pd.Series({"dup_any": int((vc >= 2).any()),
                              "namesake": namesake, "maxcl": int(vc.max())})
        s = d.groupby("seat_id").apply(seatstat, include_groups=False)
        # chance baseline: shuffle names across seats within state
        names = d.cand_name.to_numpy(dtype=object).copy(); RNG.shuffle(names)
        dperm = d.assign(nm=names)
        exp = dperm.groupby("seat_id").nm.apply(lambda v: int(v.value_counts().ge(2).any())).mean()
        rows.append({"state": st, "seats": len(s),
                     "pct_same_name": round(100 * s.dup_any.mean(), 1),
                     "pct_expected_by_chance": round(100 * exp, 1),
                     "pct_namesake_diff_father": round(100 * s.namesake.mean(), 1),
                     "pct_3plus_same_name": round(100 * (s.maxcl >= 3).mean(), 1),
                     "max_cluster": int(s.maxcl.max())})
    return pd.DataFrame(rows)


def main(cand_path, outdir):
    res = analyze(pd.read_csv(cand_path, low_memory=False))
    res.to_csv(Path(outdir) / "namesakes.csv", index=False)
    print(res.to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", default="tables/candidates.csv.gz")
    ap.add_argument("--outdir", default="tables")
    a = ap.parse_args()
    main(a.cand, a.outdir)
