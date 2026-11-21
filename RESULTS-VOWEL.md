# RESULTS-VOWEL: do sperm whale coda vowels persist through bouts?

Graded by `test_vowel_results.py` (published before the result was read) from `results/vowel/vowel_results.json`, the output of `vowel_test.py` registered in `VOWEL-PREREG.md`. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents; not yet checked by a human expert. Text CC BY 4.0.

## Verdict

Verdict: **`VOWELS_CLUSTER_STRONGLY`**

6 of 7 graded predictions true

Brier score **0.114**

## Data

Code version `whale-vowel-test-1`; data files md5 match: codamd.csv yes, DominicaCodas.csv yes, sperm-whale-dialogues.csv yes

Join: 1,316 of 1,375 codamd rows matched to a unique DSWP recording time (2 ambiguous, 53 unmatched, 0 not found by coda number)

Units: **1,134** labelled, timed codas of 13 whales in 19 whale-deployments, 38 files and 94 bouts (gap <= 60 s); share of a 0.650

Strata (whale x deployment x coda type): 96; 20 hold both vowels, with 791 codas

Neighbouring pairs: 1,096 (1,040 within bouts, 56 between bouts)

## Primary test: switches between neighbouring codas within bouts

Within-bout switches S = **75**; expected under shuffling E = 352.23; Q = S/E = **0.2129**

Primary test (B = 9,999 permutations within whale x deployment x coda type): p_low = **0.0001**, p_high = 1.0000; null mean 352.17, sd 12.78, range 306 to 397

Between-bout switches 21 of 56 pairs; expected 25.77; Q = 0.8150

## Gap profile (exploratory)

| gap | pairs | switches | expected | Q |
|---|---|---|---|---|
| 0-10 s | 926 | 49 | 309.62 | 0.158 |
| 10-60 s | 114 | 26 | 42.60 | 0.610 |
| 60-300 s | 19 | 5 | 8.17 | 0.612 |
| 300+ s | 37 | 16 | 17.59 | 0.909 |

## Per whale (exploratory)

| whale | codas | within-bout pairs | switches | expected | Q |
|---|---|---|---|---|---|
| ATWOOD | 356 | 335 | 12 | 142.54 | 0.084 |
| FORK | 291 | 271 | 26 | 100.91 | 0.258 |
| FRUIT | 32 | 28 | 5 | 5.80 | 0.862 |
| JOCASTA | 55 | 46 | 0 | 0.00 | n/a |
| LADYO | 7 | 6 | 0 | 0.00 | n/a |
| LAIUS | 29 | 25 | 2 | 10.62 | 0.188 |
| NALGENE | 4 | 2 | 0 | 0.00 | n/a |
| PINCHY | 138 | 126 | 18 | 50.85 | 0.354 |
| SAM | 52 | 48 | 3 | 5.69 | 0.527 |
| SOPH | 28 | 25 | 0 | 0.00 | n/a |
| SOURSOP | 10 | 8 | 0 | 0.00 | n/a |
| TBB | 117 | 107 | 8 | 33.21 | 0.241 |
| TWEAK | 15 | 13 | 1 | 2.60 | 0.385 |

## Deployment test (secondary)

Deployment test (whales FORK, JOCASTA, LAIUS, TBB; 10 deployments, 492 codas, 47 whale x coda type x deployment cells): G = 65.899 (null mean 8.934, 95th percentile 17.127), p_dep = **0.0001** (B = 9,999)

## Calibration on the real timeline

Coda world (independent codas, R = 200, B = 999): size **0.055** (11 of 200 rejected; calibration fails above 0.10)

| eps (bout world) | rejected | power |
|---|---|---|
| 0.05 | 200 of 200 | 1.000 |
| 0.10 | 200 of 200 | 1.000 |
| 0.20 | 200 of 200 | 1.000 |
| 0.30 | 185 of 200 | 0.925 |

Power at eps = 0.20: **1.000** (0.80 or more needed for NO_CLUSTERING_WITH_POWER)

## Matching (exploratory)

| eps | mean Q |
|---|---|
| 0.00 | 0.0000 |
| 0.05 | 0.2663 |
| 0.10 | 0.4875 |
| 0.15 | 0.6202 |
| 0.20 | 0.7618 |
| 0.25 | 0.8246 |
| 0.30 | 0.8892 |
| 0.35 | 0.9526 |
| 0.40 | 0.9773 |
| 0.45 | 0.9782 |
| 0.50 | 0.9856 |

Matched eps (exploratory): **0.05** (observed Q 0.2129)

## Predictions (priors fixed in VOWEL-PREREG.md)

| id | prediction | prior | came true |
|---|---|---|---|
| Q1 | primary within-bout test detects clustering, p_low <= 0.05 | 0.70 | **true** |
| Q2 | Q = S/E <= 0.5 (at most half the expected switches) | 0.40 | **true** |
| Q3 | vowels differ between tag deployments of the same whale, p_dep <= 0.05 | 0.55 | **true** |
| Q4 | power at eps = 0.20 >= 0.80 | 0.85 | **true** |
| Q5 | coda-world size <= 0.10 | 0.97 | **true** |
| Q6 | between-bout switch share exceeds the within-bout share | 0.65 | **true** |
| Q7 | p_high <= 0.05 (vowels alternate more than chance) | 0.05 | **false** |
