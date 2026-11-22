# READING-COART: what test 3 (sperm whale coda "coarticulation") found

MV2, Munim, Inc. (mv2@munimtech.com), 2026-11-22. Made with AI agents working in MV2's name; no
human expert has checked it yet. Text CC BY 4.0. Numbers come from results/coart/vowel3_results.json
and RESULTS-COART.md (job vowel3-coart-v1, run 2026-11-22 04:34-04:45 UTC, pre-registration
VOWEL3-PREREG.md, code and registration checked byte for byte against main before computing).

## Registered verdict: CALIBRATION_FAILED

The registered asymmetry test was oversized. In W0, a world built from the real pairs with each
pair's two click scores swapped at random, it fired in 0.205 of 200 worlds at a nominal 0.05
(limit 0.10), and 0.150 in the reverse direction. Under the registered rules no carryover-vs-
symmetry verdict can be given from it. Our prediction P4 (W0 size <= 0.10, prior 0.90) failed.
Brier score over P1-P6: 0.260.

## What does stand

| | change pairs (n = 44) | no-change pairs (n = 716) | difference | p_high (labels permuted within 9 tag deployments) |
|---|---|---|---|---|
| first click of the new coda mismatches its label | 11 (25.0%) | 66 (9.2%) | 0.1578 | 0.0035 |
| last click of the previous coda mismatches its label | 9 (20.5%) | 72 (10.1%) | 0.1040 | 0.0433 |

- **The published effect reproduces** with tag deployments as strata (P1, prior 0.75: true). This
  test is valid: under its null the 0/1 scores are exchangeable between change and no-change pairs.
- **The mirror effect is there too** (P2, prior 0.55: true; flag LAST_CLICK_ALSO_MISMATCHES). At
  a vowel change, the previous coda's last click also mismatches its own coda's label about twice
  as often as usual. Carryover coarticulation, as published, predicts an effect on the new coda's
  first click only. Label noise in a persistent vowel sequence (test 1 found vowels persist
  strongly through bouts), a state that changes mid-coda, or two-way coarticulation all predict
  both. The published model scores first clicks only, so it cannot tell these apart.
- **The published-style first-click test fires in 0.760 of the symmetric W0 worlds** (P5, prior
  0.55: true). In a world with no carryover at all, but with the symmetric mismatch excess seen
  here, the published first-click comparison would usually still come out significant.
- Descriptive only: the change-pair excess sits mostly in pairs with gaps above the median 3.41 s
  (first 0.204, last 0.164; 31 change pairs), against 0.056 and -0.029 for gaps up to the median
  (13 change pairs). A physical carryover between codas would be expected to fade with the gap,
  not to grow with it. This split was not tested and is small.

## Why the asymmetry test failed, and what comes next

A = Delta_first - Delta_last is a difference in means of d = mf - ml (-1, 0 or +1). Discordant
pairs are much more common among change pairs, and the label permutation spreads them over all
760 pairs, so its null sd (0.0525) understates the spread of A in W0. VOWEL3-AMENDMENT-1.md gives
the arithmetic. That amendment, written after this output and saying so, replaces the asymmetry
test with the exact test for the symmetric world: a fair-coin sign for every discordant pair,
enumerated exactly. Its observed A is already known (0.0538). What it adds is the exact p value,
the smallest A that could have been detected, and the power in the registered carryover worlds.

## Limits

Four whales and 9 tag deployments; 44 change pairs. Mismatch is the authors' 0/1 definition
(spectral peak count against the hand vowel label), not a continuous measure. Nothing here tests
the vowel distinction itself, formants or durations.
