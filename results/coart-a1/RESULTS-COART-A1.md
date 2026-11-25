# RESULTS-COART-A1: exact symmetry test for sperm whale coda 'coarticulation'

Rendered by vowel3b_test.py (VOWEL3-AMENDMENT-1.md) from vowel3b_results.json.
Made with AI agents working in MV2's name (MV2, Munim, Inc.); not yet checked by a human expert.
Data: Project CETI coda-vowel-phonology, focal-coarticulation-metadata.csv at be751b8.

## Verdict

**UNDERPOWERED**

Same pairs as job vowel3-coart-v1: True

| group | pairs | first click only | last click only | both | neither |
|---|---|---|---|---|---|
| vowel change | 44 | 9 | 7 | 2 | 26 |
| no change | 716 | 31 | 37 | 35 | 613 |

## Tests (exact; each discordant pair's sign a fair coin)

| quantity | value |
|---|---|
| Delta_first | 0.1578 |
| Delta_last | 0.1040 |
| A = Delta_first - Delta_last | 0.0538 |
| exact p_high, p_low | 0.2747, 0.7382 |
| smallest A significant at 0.05 | 0.1483 |
| change rows: first only vs last only | 9 vs 7 (p_high 0.4018) |

## Calibration (R = 1000 worlds; planted delta 0.1578)

| world | A test fires | A reversed | change-row sign test fires |
|---|---|---|---|
| W0 | 0.053 | 0.040 | 0.046 |
| W1_full | 0.457 | 0.000 | 0.389 |
| W1_half | 0.202 | 0.007 | 0.156 |

## Predictions

| id | prior | outcome |
|---|---|---|
| Q1 | 0.70 | True |
| Q2 | 0.50 | False |
| Q3 | 0.60 | True |
| Q4 | 0.95 | True |

Brier score 0.126.
