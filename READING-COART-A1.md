# READING-COART-A1: the exact symmetry test for sperm whale coda "coarticulation"

MV2, Munim, Inc. (mv2@munimtech.com), 2026-11-25. Made with AI agents working in MV2's name; no
human expert has checked it yet. Text CC BY 4.0. Numbers come from
[results/coart-a1/vowel3b_results.json](results/coart-a1/vowel3b_results.json) and
[results/coart-a1/RESULTS-COART-A1.md](results/coart-a1/RESULTS-COART-A1.md), written unchanged
by job vowel3-coart-a1-v1 (run 2026-11-25 20:54-21:01 UTC; unit tests passed; gate3b.py checked
the amendment and code against GitHub main first). Plan: [VOWEL3-AMENDMENT-1.md](VOWEL3-AMENDMENT-1.md).

## Registered verdict: UNDERPOWERED

Same 760 pairs as job vowel3-coart-v1 (44 vowel-change pairs, 716 no-change pairs): reproduction
check passed.

| group | pairs | first click only mismatches | last click only | both | neither |
|---|---|---|---|---|---|
| vowel change | 44 | 9 | 7 | 2 | 26 |
| no change | 716 | 31 | 37 | 35 | 613 |

- A = Delta_first - Delta_last = 0.1578 - 0.1040 = 0.0538; exact p_high 0.2747, p_low 0.7382.
- The smallest A this test could call significant at 0.05 is 0.1483, almost the whole observed
  first-click effect (0.1578).
- Within the change pairs alone: 9 first-only against 7 last-only mismatches (p_high 0.4018).
- Calibration (1,000 worlds each): the test fired in 5.3% of symmetric worlds (W0), so it is
  correctly sized. In worlds with a planted carryover as large as the observed first-click effect
  (W1_full) it fired in 45.7%; at half that size, 20.2%.

**Reading.** The public pairs cannot tell carryover coarticulation (an effect on the new coda's
first click only) from a symmetric mismatch at vowel changes (both clicks), the reading that label
noise or a mid-coda state change would give. The data lean symmetric (9 against 7 discordant
change pairs), but a full-size carryover would have been detected less than half the time. This
does not change the ledger row: sperm whale coarticulation stays UNDECIDED. The registered
CALIBRATION_FAILED verdict of the original asymmetry test (READING-COART.md) stands unchanged.

## Predictions (VOWEL3-AMENDMENT-1.md section 5)

| id | prediction | prior | outcome |
|---|---|---|---|
| Q1 | verdict UNDERPOWERED | 0.70 | true |
| Q2 | W1_full power >= 0.50 | 0.50 | false (0.457) |
| Q3 | at least 16 change pairs discordant | 0.60 | true (16) |
| Q4 | W0 size <= 0.06 | 0.95 | true (0.053) |

Brier score 0.126.

## Limits

Four whales, 9 tag deployments, 44 change pairs. The sign-flip null treats pairs as independent
(consecutive pairs share codas; under label noise this makes the test conservative). Mismatch is
the authors' 0/1 definition. This work was done with AI agents working in MV2's name and has not
been checked by a human expert.
