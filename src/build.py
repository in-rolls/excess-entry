"""
build.py -- harmonize four in-rolls local-election datasets into one
candidate-level frame for the excess-entry analyses.

Posts are all gram-panchayat heads and comparable:
  Rajasthan sarpanch (2020), Bihar mukhiya (2016),
  Uttar Pradesh pradhan (2021), Uttarakhand pradhan (2008/2014/2019).

Output columns (one row per contesting candidate):
  state, year, post, seat_id, cand_name, father_name, votes,
  woman_seat (0/1 horizontal women's reservation),
  caste (General/SC/ST/OBC/Other vertical reservation)

Votes are NA for Rajasthan (the contesting file records no per-candidate
votes; only winner and runner-up appear in WinnerSarpanch).

Data (clone next to this repo, or pass --root):
  github.com/in-rolls/local_elections_rajasthan
  github.com/in-rolls/local_elections_bihar
  github.com/in-rolls/local_elections_up
  github.com/in-rolls/local_elections_uttarakhand
"""
from __future__ import annotations
import argparse, re, unicodedata, zipfile
from pathlib import Path
import numpy as np, pandas as pd

WOMAN = re.compile(r"\(Woman\)|महिला|female|woman", re.I)
CASTE_MAP = {
    "अनारक्षित": "General", "general": "General", "unreserved": "General",
    "अनुसूचित जाति": "SC", "sc": "SC",
    "अनुसूचित जनजाति": "ST", "st": "ST",
    "अन्य पिछड़ा वर्ग": "OBC", "अन्य पिछडा वर्ग": "OBC", "obc": "OBC",
    "अति पिछड़ा वर्ग": "OBC", "पिछड़ा": "OBC",
}


def norm_name(s) -> str:
    s = str(s).replace("\u200d", "").replace("\u200c", "")
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"\s+", " ", s).strip().upper()


def caste_of(res: str) -> str:
    r = WOMAN.sub("", str(res)).strip().lower()
    r = re.sub(r"\s+", " ", r)
    for k, v in CASTE_MAP.items():
        if k.lower() in r or k in str(res):
            return v
    return "General" if not r else "Other"


def _frame(df, seat_keys, name, father, res, votes, state, year, post):
    out = pd.DataFrame()
    out["seat_id"] = df[seat_keys].astype(str).agg("|".join, axis=1)
    out["cand_name"] = df[name].map(norm_name)
    out["father_name"] = df[father].map(norm_name) if father else ""
    out["votes"] = pd.to_numeric(df[votes], errors="coerce") if votes else np.nan
    out["woman_seat"] = df[res].astype(str).str.contains(WOMAN).astype(int)
    out["caste"] = df[res].map(caste_of)
    out["state"] = state; out["year"] = year; out["post"] = post
    return out[out.cand_name.str.len() > 0]


def build(root: Path) -> pd.DataFrame:
    frames = []

    r = pd.read_csv(root / "local_elections_rajasthan/data/ContestingSarpanch.csv.gz", low_memory=False)
    r = r[r.ElectionType == "General Election"]
    frames.append(_frame(r, ["District", "PanchayatSamiti", "NameOfGramPanchayat"],
                         "NameOfContestingCandidate", "FatherHusbandOfContestingCandidate",
                         "CategoryOfGramPanchayat", None, "Rajasthan", 2020, "sarpanch"))

    b = pd.read_csv(root / "local_elections_bihar/data/mukhiya.csv", low_memory=False)
    frames.append(_frame(b, ["district", "block", "panchayat"],
                         "candidate_name", "father_husband_name",
                         "reservation_status", "valid_vote", "Bihar", 2016, "mukhiya"))

    with zipfile.ZipFile(root / "local_elections_up/data/up_gram_panchayat_pradhan_2021.csv.zip") as zf:
        with zf.open(zf.namelist()[0]) as f:
            u = pd.read_csv(f, low_memory=False)
    frames.append(_frame(u, ["zila", "block", "gram_panchayat"],
                         "candidate_name_2021", "father_husband_name_2021",
                         "reservation", "vote_percentage", "UP", 2021, "pradhan"))

    uk = pd.read_csv(root / "local_elections_uttarakhand/data/uttarakhand-panchayat-elections.csv", low_memory=False)
    uk = uk[uk["निर्वाचित पद"].astype(str).str.contains("प्रधान")].copy()

    def _n(s):
        s = str(s).replace("\u200d", ""); s = re.sub(r"^\s*\d+\s*-\s*", "", s)
        return re.sub(r"\s+", "", re.sub(r"[\(（].*?[\)）]", "", s)).strip()
    for c in ["जनपद", "विकास खण्\u200dड", "ग्राम पंचायत"]:
        uk[c + "_k"] = uk[c].map(_n)
    for y, d in uk.groupby("Year"):
        frames.append(_frame(d, ["जनपद_k", "विकास खण्\u200dड_k", "ग्राम पंचायत_k", "Year"],
                             "अभ्\u200dयर्थी का नाम", "पिता/पति का नाम",
                             "आरक्षण स्थिति", "प्राप्\u200dत मत", "Uttarakhand", int(y), "pradhan"))

    out = pd.concat(frames, ignore_index=True)
    out["seat_id"] = out.state + "::" + out.seat_id
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="tables/candidates.csv.gz")
    a = ap.parse_args()
    df = build(Path(a.root))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False, compression="gzip")
    print(f"built {len(df):,} candidates across "
          f"{df.seat_id.nunique():,} GP-head seats, {df.state.nunique()} states -> {a.out}")
