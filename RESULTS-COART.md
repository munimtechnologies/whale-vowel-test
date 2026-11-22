# RESULTS-COART: is sperm whale coda 'coarticulation' carryover or symmetric?

Rendered by vowel3_test.py from vowel3_results.json (pre-registration VOWEL3-PREREG.md).
Made with AI agents working in MV2's name (MV2, Munim, Inc.); not yet checked by a human expert.
Data: Project CETI coda-vowel-phonology, focal-coarticulation-metadata.csv at be751b8.

## Verdict

**CALIBRATION_FAILED**

| quantity | value |
|---|---|
| rows after the authors' filters | 760 |
| pairs with both clicks scored | 760 |
| change pairs, no-change pairs | 44, 716 |
| whales, tag deployments | 4, 9 |

## Mismatch rates

| click | rows | change: mismatches / n | no change: mismatches / n |
|---|---|---|---|
| first click of coda | all | 11 / 44 (0.250) | 66 / 716 (0.092) |
| last click of previous coda | all | 9 / 44 (0.205) | 72 / 716 (0.101) |
| first click of coda | paired | 11 / 44 (0.250) | 66 / 716 (0.092) |
| last click of previous coda | paired | 9 / 44 (0.205) | 72 / 716 (0.101) |

## Tests (change labels permuted within tag deployments, B = 9999)

| statistic | observed | null mean | p_high | p_low |
|---|---|---|---|---|
| first-click mismatch, change minus no change | 0.1578 | 0.0056 | 0.0035 | 0.9995 |
| last-click mismatch, change minus no change | 0.1040 | 0.0065 | 0.0433 | 0.9841 |
| asymmetry A = first minus last | 0.0538 | -0.0009 | 0.1999 | 0.9005 |

Flag LAST_CLICK_ALSO_MISMATCHES: True

Descriptive, by inter-coda gap (median 3.413 s):

| gap | pairs | change pairs | first delta | last delta |
|---|---|---|---|---|
| gap le median | 380 | 13 | 0.0558 | -0.0293 |
| gap gt median | 380 | 31 | 0.2044 | 0.1635 |

## Calibration (R = 200 worlds, B = 999; planted delta 0.1578)

| world | A test fires (p_high) | A reversed (p_low) | published-style first-click test fires |
|---|---|---|---|
| W0 | 0.205 | 0.150 | 0.760 |
| W1_full | 0.735 | 0.005 | 0.995 |
| W1_half | 0.390 | 0.015 | 0.985 |

## Predictions

| id | prior | outcome |
|---|---|---|
| P1 | 0.75 | True |
| P2 | 0.55 | True |
| P3 | 0.65 | True |
| P4 | 0.90 | False |
| P5 | 0.55 | True |
| P6 | 0.40 | False |

Brier score 0.260.
