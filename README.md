# election_entry

How many people contest a gram-panchayat head seat in India, and what that
does to the vote. A descriptive study of candidate entry across four states,
built on the [in-rolls](https://github.com/in-rolls) local-election data.

The name is the [excess-entry theorem](https://en.wikipedia.org/wiki/Excess_entry_theorem)
(Mankiw and Whinston, 1986): with free entry and a business-stealing
externality, more competitors pile into a market than is efficient.
Panchayat elections are non-partisan, so there is little party gatekeeping
to consolidate the field, and the equilibrium number of candidates scales
with the value of the seat over the cost of standing. The data show that
scaling, and the welfare cost that comes with it: winners elected on a
quarter of the vote.

## Findings

All posts are gram-panchayat heads and comparable (sarpanch, mukhiya,
pradhan).

**Contestation scales across states.** Mean candidates per seat: Uttarakhand
3.1-3.9, Rajasthan 6.0, UP 7.5, Bihar 12.0. The distributions barely
overlap; Bihar's 25th percentile (8) beats UP's median (7) and Rajasthan's
75th (8).

| state (year) | p25 | p50 | p75 | mean | median effective N |
|---|---|---|---|---|---|
| Uttarakhand (2019) | 2 | 3 | 4 | 3.1 | 3.0 |
| Rajasthan (2020) | 3 | 5 | 8 | 6.0 | — |
| UP (2021) | 5 | 7 | 9 | 7.5 | 3.5 |
| Bihar (2016) | 8 | 11 | 15 | 12.0 | 5.5 |

**The votes split, and the mandate erodes.** The typical Bihar mukhiya wins
with 28% of the vote; 92% of winners fall short of a majority and 67% short
of a third. In 92% of Bihar seats the result is "split-decided": the votes
held by third-place-and-below candidates exceed the winner's margin over the
runner-up, so the field could have flipped it. UP and Uttarakhand are milder
(78% and 66% split-decided) but the pattern is monotonic everywhere: more
candidates, weaker winners, more split-decided seats. Condorcet cycles are
not observable here (no ranked ballots), but this is the condition under
which the plurality winner is unlikely to be the majority's choice.

**Reservation swaps the field, it does not shrink it.** Women-reserved and
open seats draw essentially the same number of candidates at every quartile,
in every state. The caste dimension moves contestation and only in two
states: SC-reserved seats are more contested than General in Bihar (14.9 vs
10.7) and UP (8.5 vs 7.2), flat in Rajasthan and Uttarakhand.

**Namesake candidates run above chance.** Two candidates share an identical
name on 3.7% (Uttarakhand) to 7.0% (Bihar) of ballots, 1.6x to 7x more than
random name assignment predicts, and almost all are genuinely different
people (same name, different father). Clusters reach five identical names in
Bihar, seven in UP. Consistent with engineered vote-splitting, though intent
is not identified here.

## Data

UP and Rajasthan download automatically at the pinned commits below. Clone
the Bihar and Uttarakhand source repos next to this one (or pass `--root`):

- [`local_elections_rajasthan`](https://github.com/in-rolls/local_elections_rajasthan) — sarpanch 2020
- [`local_elections_bihar`](https://github.com/in-rolls/local_elections_bihar) — mukhiya 2016
- [`local_elections_up`](https://github.com/in-rolls/local_elections_up) — pradhan 2021
- [`local_elections_uttarakhand`](https://github.com/in-rolls/local_elections_uttarakhand) — pradhan 2008/2014/2019

## Reproduce

```bash
pip install -r requirements.txt
ROOT=..
python src/build.py        --root "$ROOT" --out tables/candidates.csv.gz
python src/contestation.py --cand tables/candidates.csv.gz
python src/mandates.py     --cand tables/candidates.csv.gz
python src/namesakes.py    --cand tables/candidates.csv.gz
```

Deterministic. `build.py` harmonizes the four datasets to one
candidate-level frame (602,404 candidates, 87,838 GP-head seats); the three
analysis scripts write CSVs to `tables/` and PNGs to `figures/`.

## Layout

```
src/build.py          harmonize the four states -> candidate-level frame
src/contestation.py   candidates per seat by reservation/caste/year, quartiles, effective N
src/mandates.py       winner vote share, sub-majority winners, split-decided share
src/namesakes.py      same-name candidates per seat vs a chance baseline
tables/               generated CSVs
figures/              generated PNGs
```

## Caveats

- **Effective N and mandates use per-candidate votes**, available for Bihar,
  UP, and Uttarakhand but not Rajasthan (its file records only winner and
  runner-up votes).
- **Cross-state levels partly reflect electorate size.** Bigger panchayats
  mechanically draw more candidates, so the gradient mixes fragmentation
  with seat size. Candidates-per-thousand-electors is the fix and is not yet
  in the repo. Within-state cuts (Uttarakhand over time, reservation within a
  state) are cleaner.
- **OBC labels.** Bihar's EBC scheme and a UP spelling variant leave some
  backward-class seats in an "Other" caste bucket; those seats are real but
  uncategorized.
- **"Split-decided" bounds the spoiler potential**, it does not prove the
  plurality winner is not the Condorcet winner (that needs second
  preferences). "Namesake" is a form, not a proven intent; the within-state
  shuffle is a permissive chance baseline because names cluster
  geographically.

## License / attribution

Analysis code under MIT. Underlying data are the in-rolls local-election
datasets; cite those repos and their sources.

## Pinned election inputs

`data_sources.json` records immutable upstream commits, relative paths and
SHA-256 checksums. Pooch downloads the declared inputs once and verifies
their checksums on reuse. All consumers share
`$INDIA_DATA_HOME/<provider>/<commit>/<relative-path>`; `INDIA_DATA_HOME`
defaults to `~/data`. An existing verified cache supports offline rebuilds.

- UP v1.2: `9f051cd607b9a42aa3afc498e57737200ef22024`,
  `data/raw/2021/gram_panchayat_pradhan_candidates.csv.gz`.
- Rajasthan v1.1: `b543c4759519dd44682fbd278d81bdccaa152e99`,
  `data/ContestingSarpanch.csv.gz`.

Bihar and Uttarakhand still read the local repositories supplied by `--root`.

Run the focused input checks with `python -m unittest discover -s tests`.
