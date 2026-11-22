# VOWEL3-AMENDMENT-1: an exact symmetry test after the registered asymmetry test failed calibration

Amendment by MV2, Munim, Inc. (mv2@munimtech.com), 2026-11-22, to VOWEL3-PREREG.md (unchanged).
Made with AI agents working in MV2's name; no human expert has checked it yet. Text CC BY 4.0, code
Apache-2.0.

## 1. What happened

Job vowel3-coart-v1 ran the registered test on 2026-11-22 (results/coart/vowel3_results.json,
RESULTS-COART.md). Its verdict is **CALIBRATION_FAILED**: in world W0, where the first-click and
last-click scores of every pair are swapped at random, so that no pair can carry an asymmetry,
the asymmetry test fired in 41 of 200 worlds (0.205) at a nominal 0.05, and fired in the reverse
direction in 30 (0.150). The registered rule stops there, and that verdict stands.

The registered first-click and last-click tests are not affected. Each compares a 0/1 score
between change and no-change pairs, and under their null (the labels are exchangeable within a
tag deployment) the label permutation is exact. Delta_first = 0.1578 (p_high 0.0035) reproduces
the published direction. Delta_last = 0.1040 (p_high 0.0433) raises the flag
LAST_CLICK_ALSO_MISMATCHES.

## 2. Why the asymmetry test failed (our reading, written before amendment 1 ran)

The asymmetry statistic is a difference in means of d = mf - ml, which takes the values -1, 0 or
+1. The label permutation treats every pair's d as exchangeable between change and no-change
rows. But at a vowel change both clicks mismatch far more often (11/44 and 9/44, against 66/716
and 72/716), so d is non-zero much more often in change rows. In W0, which is symmetric by
construction, the spread of A comes from the signs of those many non-zero change-row d values.
A permutation that spreads them over all 760 rows understates that spread: its null sd was
0.0525. If about 20 change pairs are discordant, the W0 sd of A is about sqrt(20)/44 = 0.10.
That would give a one-sided size of about P(Z > 1.645 x 0.0525 / 0.10) = 0.20, close to the 0.205
observed. This is the Behrens-Fisher problem: equal means do not imply equal spread for a
three-valued score. Amendment 1 prints the discordance counts, so this reading can be checked.

## 3. The amended test

Symmetry, the null hypothesis that W0 builds, means the two clicks of a pair are exchangeable.
So every discordant pair (first click only, or last click only, mismatched) has a sign that is a
fair coin. With b and c the first-only and last-only counts in each group:

- A = (b_C - c_C) / n_C - (b_N - c_N) / n_N (identical to the registered A);
- null: S_C = 2X - k_C and S_N = 2Y - k_N, with X ~ Bin(k_C, 1/2) and Y ~ Bin(k_N, 1/2)
  independent, k = b + c. The exact distribution is computed by enumeration, with no random
  numbers. p_high = P(A* >= A) and p_low = P(A* <= A), with ties counted on both sides. a_crit is
  the smallest A that would reach p_high <= 0.05;
- secondary: the exact sign test within change rows alone, P(Bin(b_C + c_C, 1/2) >= b_C).

Calibration uses the registered worlds, on the same pairs: W0 (swap with probability 1/2), and
W1_full and W1_half (W0, then registered carryover planting at max(Delta_first, 0) and half of
it). R = 1000 worlds each, Python random.Random(20261122). By construction the size in W0 is at
most 0.05 up to Monte Carlo error. Running W0 checks the code, not the method.

Verdict, in order: INSUFFICIENT_DATA (fewer than 10 change pairs or no no-change pair);
REPRO_FAILED if the pair counts differ from vowel3-coart-v1 (44 change, 716 no-change pairs;
first-click mismatches 11 and 66; last-click mismatches 9 and 72); CALIBRATION_FAILED if the W0
size > 0.10; CARRYOVER_SPECIFIC if p_high <= 0.05; REVERSED_ASYMMETRY if p_low <= 0.05;
SYMMETRIC_WITH_POWER if the W1_full power >= 0.80; else UNDERPOWERED. The readings in
VOWEL3-PREREG.md section 7 apply unchanged.

## 4. What we already know (disclosed)

This amendment was written after reading the v1 output. The observed A is therefore already known
(0.0538). So are b_C - c_C = 11 - 9 = 2 and b_N - c_N = 66 - 72 = -6, because the pairs where both
clicks mismatch cancel. Not yet known: the discordant counts k_C and k_N (how many pairs have both
clicks mismatched), and therefore the exact p values, a_crit and the power. A within-change sign
test with b_C - c_C = 2 cannot reach p_high <= 0.05 for any k_C. A CARRYOVER_SPECIFIC verdict is
therefore practically excluded before the run, and the open question is whether the public pairs
have the power to call the pattern symmetric.

## 5. Predictions (priors) and Brier score

Q1 the verdict is UNDERPOWERED (0.70). Q2 W1_full power >= 0.50 (0.50). Q3 at least 16 change
pairs are discordant, i.e. at most 2 change pairs have both clicks mismatched (0.60). Q4 W0 size
<= 0.06 (0.95). Brier score = mean of (prior - outcome)^2.

## 6. Limits fixed now

The sign-flip null treats pairs as independent. Consecutive pairs share codas: a mislabelled coda
gives one change pair with a first-click mismatch and the next with a last-click mismatch. Under
label noise, those two signs are opposite rather than independent, which makes this test
conservative, not liberal. The test also assumes symmetry in the no-change pairs. The observed
no-change imbalance (66 vs 72) is small, and A subtracts it.

## 7. Order of work

This file, vowel3b_test.py and test_vowel3b_test.py are committed together, and the publish lane
runs their unit tests before the job does. The job's first step (gate3b.py) computes nothing until
the public copies match its own. The data are the authors' file at commit be751b8, and its md5 is
printed.
