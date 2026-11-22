# RESULTS-DUR: do sperm whale 'long and short vowels' hold within bouts?

Graded by `test_vowel2_results.py` (published with the registration, before the result existed) from `results/vowel2/vowel2_results.json`, the output of `vowel2_test.py` registered in `VOWEL2-PREREG.md`. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents; not yet checked by a human expert. Text CC BY 4.0.

## Verdict

Verdict: **`CALIBRATION_FAILED_WITHIN_BOUTS`**

5 of 8 graded predictions true

Brier score **0.313**

## Data

Code version `whale-vowel2-test-1`; data files md5 match: codamd.csv yes, DominicaCodas.csv yes, sperm-whale-dialogues.csv yes

codamd.csv in Project-CETI/coda-vowel-phonology (commit be751b8) is identical to the OSF copy

Published subset (1+1+3 codas of ATWOOD, FORK, PINCHY and TBB with a vowel and a duration): **628** codas (338 a, 290 i); timed: **623** of them in 46 bouts and 8 whale-deployments

## Published-style durations by whale (all codas of the subset)

| whale | a codas | i codas | mean a (s) | mean i (s) | a - i (s) |
|---|---|---|---|---|---|
| ATWOOD | 132 | 128 | 1.1013 | 0.9530 | +0.1482 |
| FORK | 120 | 92 | 1.2141 | 1.0555 | +0.1586 |
| PINCHY | 51 | 55 | 1.2660 | 1.1943 | +0.0717 |
| TBB | 35 | 15 | 1.2917 | 1.1239 | +0.1678 |

## Duration contrast at each level (D = weighted mean of a minus i)

| comparison | D = a - i (s) | groups with both vowels | minority-vowel codas | p_high | p_low |
|---|---|---|---|---|---|
| published-style: within whale, all codas of the published subset | +0.1399 | 4 | 286 | 0.0001 | 1.0000 |
| within whale, timed codas only | +0.1399 | 4 | 284 | 0.0001 | 1.0000 |
| within tag deployment | +0.1349 | 7 | 271 | 0.0001 | 1.0000 |
| within bout | +0.1136 | 20 | 105 | 0.0001 | 1.0000 |

Level tested: **bout** (the first of bout, deployment with at least 5 groups holding both vowels and 15 minority-vowel codas)

Rotation p_high at that level (labels turned within groups, runs kept, B = 9,999): 0.0001

## Calibration

Size in rotation worlds (effect removed, R = 200, B = 999): **0.190** (calibration fails above 0.10)

| effect added to a-codas | delta (s) | power |
|---|---|---|
| 1.0 x published-style D | 0.1399 | 1.000 |
| 0.5 x published-style D | 0.0700 | 1.000 |

Bout-clustered worlds with no vowel effect (one vowel per bout, 5% flipped, real durations, R = 200): published-style test says 'a longer' in **0.355**, either direction (p <= 0.025 each side) in 0.550; within-bout test says 'a longer' in 0.045

## i-vowel durations: short and long modes (secondary)

| whale | i codas | split (s) | long | mean short (s) | mean long (s) | dip | dip p |
|---|---|---|---|---|---|---|---|
| ATWOOD | 128 | 0.9427 | 66 | 0.8438 | 1.0556 | 0.0513 | 0.0140 |
| FORK | 92 | 1.0529 | 43 | 0.8792 | 1.2564 | 0.0821 | 0.0000 |
| PINCHY | 55 | 1.1410 | 43 | 1.0463 | 1.2356 | 0.0293 | 0.9909 |
| TBB | 15 | 1.1208 | 7 | 0.9968 | 1.2691 | 0.1317 | 0.0160 |

Short/long persistence within bouts: 22 switches in 257 neighbouring i-coda pairs, expected 113.85, Q = **0.1932**, p_low = 0.0001 (B = 9,999, shuffled within whale x deployment)

Short/long mix by deployment (whales FORK; 3 deployments, 92 i-codas): G = 5.018 (null mean 2.072), p = **0.0941**

## By deployment (exploratory)

| whale | deployment | first date | bouts | a | i | mean a (s) | mean i (s) | long i |
|---|---|---|---|---|---|---|---|---|
| ATWOOD | sw061b | 02-03-2015 | 18 | 131 | 128 | 1.1019 | 0.9530 | 66 |
| FORK | sw078a | 19-03-2015 | 3 | 24 | 28 | 1.0473 | 1.1299 | 18 |
| FORK | sw085a | 26/03/2015 | 8 | 90 | 54 | 1.2598 | 1.0165 | 21 |
| FORK | sw090b | 31-03-2015 | 2 | 4 | 10 | 1.1581 | 1.0575 | 4 |
| PINCHY | sw090a | 31/03/2015 | 9 | 49 | 55 | 1.2648 | 1.1943 | 43 |
| TBB | sw091a | 01-04-2015 | 2 | 5 | 8 | 1.2583 | 0.9968 | 0 |
| TBB | sw097a | 07-04-2015 | 1 | 2 | 0 | 0.7278 | n/a | 0 |
| TBB | sw119b | 29-04-2014 | 3 | 28 | 7 | 1.3380 | 1.2691 | 7 |

## Predictions (priors fixed in VOWEL2-PREREG.md)

| id | prediction | prior | came true |
|---|---|---|---|
| P1 | published-style contrast reproduced: a longer than i, p_high <= 0.05 | 0.80 | **true** |
| P2 | a longer than i within the level tested, p_high <= 0.05 | 0.35 | **true** |
| P3 | power at the published-style effect size >= 0.80 | 0.50 | **true** |
| P4 | rotation-world size <= 0.10 | 0.90 | **false** |
| P5 | published-style false-alarm rate in bout-clustered worlds > 0.10 | 0.75 | **true** |
| P6 | within-level contrast below half the within-whale contrast on the same codas | 0.60 | **false** |
| P7 | i-vowel short/long modes persist within bouts (p_low <= 0.05 and Q <= 0.5) | 0.55 | **true** |
| P8 | i-vowel short/long mix differs between deployments of a whale, p <= 0.05 | 0.60 | **false** |
