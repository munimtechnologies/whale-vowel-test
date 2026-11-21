# VOWEL3-PREREG: is sperm whale coda "coarticulation" carryover, or symmetric?

Pre-registration by MV2, Munim, Inc. (mv2@munimtech.com), 2026-11-21. Made with AI agents working
in MV2's name; no human expert has checked it yet. Text CC BY 4.0, code Apache-2.0. Third test in
whale-vowel-test (test 1: RESULTS-VOWEL.md; test 2: VOWEL2-PREREG.md).

## 0. What we had seen before writing this

The authors' R script `PhonologyCodaVowel.R` (the coarticulation block quoted below); the 35 column
names of `focal-coarticulation-metadata.csv`; and, through a web page summary, its first eight data
rows (all ATWOOD, coart `aa`, one spectral peak on both clicks, so eight no-change pairs with no
mismatch). No statistic of this file by change type, click or deployment had been computed by us.
We also knew our test 1 result: hand-labelled vowels persist strongly through bouts (switches at
Q = 0.2129 of the shuffled rate).

## 1. The claim

Begus, Dabkowski, Sprouse, Gruber & Gero (2026), Proc R Soc B 293:20252994
(doi 10.1098/rspb.2025.2994), report coarticulation in sperm whale codas: when the vowel changes
between two consecutive codas, the first click of the new coda is more often "mismatched" with its
own coda's vowel, i.e. it resembles the previous coda. Their public code (github.com/Project-CETI/
coda-vowel-phonology, commit be751b8) reads `focal-coarticulation-metadata.csv`, keeps
0 < `deltasec` < 10 and whales PINCHY, FORK, ATWOOD, TBB, and defines

- `match` = 0 if (`handvcat` a and `numpks` 1) or (i and 2); 1 if (a and 2) or (i and 1); else NA
  (so `match` = 1 means a mismatch of the coda's first click with the coda's label);
- `type` = noChange for `coart` aa or ii, Change for ia or ai;

and fits `glmer(match ~ type + handvcat + prevhandvcat + (1|whale), family = binomial)`.

## 2. Why this needs a mirror test

Each row of the file is a pair: the last click of the previous coda (`prevnumpks`, label
`prevhandvcat`) and the first click of the current coda (`numpks`, label `handvcat`). Carryover
coarticulation predicts that at a change only the **first click of the new coda** drifts toward the
previous vowel. Two other mechanisms produce a first-click effect too, but symmetrically:

- **Label noise with persistent vowels.** If vowels persist (test 1) and a coda's hand label is
  sometimes wrong, then most observed "changes" contain a mislabelled coda. When the current coda
  is the mislabelled one, its first click (true vowel) mismatches its label; when the previous coda
  is, its **last** click mismatches its label, equally often.
- **A slow state that switches mid-coda** gives a last click of the previous coda already in the new
  state as often as a first click of the new coda still in the old one.

So the same rows, scored on the previous coda's last click against the previous coda's label,
give a mirror. Bidirectional coarticulation (carryover plus anticipation of equal size) would also
be symmetric, so a symmetric result says the effect is not specific to carryover; it is not proof
of an artefact.

## 3. Data, units, statistics

Rows: the authors' filters exactly (0 < deltasec < 10, the four whales), `type` defined. First-click
mismatch mf = the authors' `match`; last-click mismatch ml = the same rule applied to
`prevhandvcat` and `prevnumpks`. Primary set P: rows with both mf and ml defined. Deployment =
whale + `tagondt`. Integrity counts (rows dropped by each filter; rows where `coart` differs from
`prevhandvcat` + `handvcat`) are printed, never repaired; `type` follows `coart`, as in the R code.

- Delta_first = mean mf over change rows minus mean mf over no-change rows (in P).
- Delta_last = the same for ml.
- Asymmetry A = Delta_first - Delta_last (= the same difference computed on d = mf - ml).

Null: the change / no-change labels are permuted within each deployment (B = 9999, seed 20261121,
numpy default_rng; one permutation set shared by the three statistics). p_high = (1 + #{null >=
obs}) / (B + 1), p_low likewise. Descriptive only: Delta_first and Delta_last in the halves of P
split at the median `deltasec`, and mismatch rates on all rows.

## 4. Calibration (R = 200 worlds per setting, B = 999, built on the real rows)

- W0, symmetric: in every pair, mf and ml are swapped with probability 1/2. Reports the size of the
  A test (share with p_high <= .05), its reversed rejection rate (p_low <= .05), and how often the
  published-style first-click test (Delta_first, p_high <= .05) fires.
- W1_full and W1_half, carryover planted: W0, then among change rows whose first click matches,
  set a mismatch with probability k = delta / (share of change rows with a matching first click),
  delta = max(observed Delta_first, 0) and half of it. Reports the power of the A test.

## 5. Verdict (applied exactly as coded in vowel3_test.py)

INSUFFICIENT_DATA if P has fewer than 10 change rows (or none of either type); else NOT_REPRODUCED
if Delta_first <= 0 or its p_high > .05; else CALIBRATION_FAILED if W0 size > .10; else
CARRYOVER_SPECIFIC if A p_high <= .05; else REVERSED_ASYMMETRY if A p_low <= .05; else
SYMMETRIC_WITH_POWER if W1_full power >= .80; else UNDERPOWERED. Flag LAST_CLICK_ALSO_MISMATCHES if
Delta_last > 0 with p_high <= .05.

## 6. Predictions (priors) and Brier score

P1 Delta_first > 0 with p_high <= .05 (.75). P2 Delta_last > 0 with p_high <= .05 (.55). P3 verdict
is not CARRYOVER_SPECIFIC (.65). P4 W0 size <= .10 (.90). P5 the published-style first-click test
fires in >= 50% of W0 worlds (.55). P6 W1_full power >= .80 (.40).

## 7. Readings fixed now

- CARRYOVER_SPECIFIC: the first click of a new coda drifts toward the previous vowel more than the
  last click of the previous coda drifts toward the next; carryover is supported beyond label noise.
- SYMMETRIC_WITH_POWER: the previous coda's last click mismatches its own label at a change about
  as much as the new coda's first click does; the published pattern is not specific to carryover,
  and label noise, mid-coda state change or bidirectional coarticulation each fit it. The
  published model, which scores only first clicks, cannot tell these apart.
- REVERSED_ASYMMETRY: the larger effect sits on the previous coda's last click (anticipation), the
  opposite direction to the claim.
- UNDERPOWERED: the public pairs cannot separate the two; report both deltas and the power.
- NOT_REPRODUCED: with deployments as strata, the first-click effect is not detected in P.
- Nothing here tests the vowel distinction itself, the formant claims, or the duration claims
  (test 2).

## 8. Order of work

This file, vowel3_test.py and test_vowel3_test.py are committed together, with their unit tests
run by the publish lane, before the job runs. The job's first step (gate3.py) computes nothing until
the public copies on main match its own byte for byte (line endings normalised). The data are read
from the authors' repository at commit be751b8 and their md5 is printed. Any later change is an
AMENDMENT file; this file is never edited.
