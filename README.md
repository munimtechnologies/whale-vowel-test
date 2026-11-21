# whale-vowel-test

An open, pre-registered test of whether sperm whale "coda vowels" are a property of each coda
or a state of the moment that persists through bouts and tag deployments; (second test,
registered 2026-11-21) whether the reported "long and short vowels" hold within a bout; and
(third test, registered 2026-11-21) whether the reported "coarticulation" between codas is
carryover or the symmetric pattern that label noise also produces.

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents; no human expert has reviewed it
yet. Code Apache-2.0, text CC BY 4.0.

## Result 1 (graded 2026-11-21)
**VOWELS_CLUSTER_STRONGLY.** Within bouts, neighbouring codas of one whale switched vowel 75
times, where shuffling within whale x deployment x coda type predicts 352.23 (Q = 0.2129,
p_low = 0.0001, 9,999 permutations; 1,134 codas, 13 whales, 19 deployments, 1,040 within-bout
pairs). Calibration on the real timeline passed (size 0.055; power 1.000 at eps 0.20). The same
whale's vowel mix also differs between tag deployments (p_dep = 0.0001, side test). Six of 7
registered predictions came true (Brier 0.114). As registered, this is a strong constraint on
the "vowel" claim, not proof of an artefact: the label behaves like a state held through a bout
(recording geometry, depth or a vocal register), not an independent choice per coda.
See `RESULTS-VOWEL.md` (rendered and checked by the grader) and `READING-VOWEL.md` (the
registered readings applied, written after the result).

## Test 2 (registered 2026-11-21, job waiting): long and short vowels within a bout
Begus et al. (2026, Proc R Soc B) report that a-codas are longer than i-codas and that i-codas
come in a short and a long form. Their public R code compares durations across all 1+1+3 codas of
four whales with only a whale effect. Because vowels persist through bouts (result 1), that
contrast may compare bouts and recording days rather than vowels. `VOWEL2-PREREG.md` registers
a test of the duration difference between a- and i-codas of the same bout (or, if bouts are too
few, the same tag deployment), calibrated for size and power on the real timeline, plus the
false-alarm rate of the published-style test when vowels come in bouts and have no effect at
all, and whether the short/long split of i-codas is itself clustered in time. The grader
`test_vowel2_results.py` is published with the registration, before any result.

## Test 3 (registered 2026-11-21, job waiting): coarticulation, carryover or symmetric?
The same paper reports that when the vowel changes between two codas, the first click of the new
coda more often mismatches its own coda's label. Carryover predicts that only that first click is
affected. If labels are sometimes wrong while vowels persist, or the state switches mid-coda, the
last click of the previous coda should mismatch its own label just as often at a change.
`VOWEL3-PREREG.md` registers the mirror test on the authors' own pair file
(`focal-coarticulation-metadata.csv`, commit be751b8): first-click and last-click mismatch
contrasts on the same pairs, their difference, a within-deployment permutation null, and size and
power from symmetric and carryover worlds built on the real pairs. Its independent grader
`test_vowel3_results.py` was published on 2026-11-21 while the job was still waiting, before any
result existed.

## Why
Begus and colleagues (2025, Open Mind; 2026, Proc R Soc B) report that sperm whale codas come
in two vowel-like qualities, a and i, that pattern like human vowels. Critics suggest the
spectral peaks behind the labels could reflect recording geometry: tag placement,
orientation or depth. If the vowel is chosen for each coda, two neighbouring codas of one
whale, seconds apart, should differ about as often as the whale's vowel mix predicts. If it
is a state, neighbours will nearly always agree. Neither paper models time, bout or tag
deployment. This repo measures it with the authors' public hand labels, joined to recording
times from the Dominica Sperm Whale Project tables.

## Files
* `VOWEL-PREREG.md`: design, decision rules and predictions, registered 2026-11-20 before any
  statistic of the vowel labels by time, bout, deployment or whale was computed.
* `vowel_test.py` + `test_vowel_test.py`: the analysis. It counts within-bout vowel switches
  against their exact expectation under shuffling within (whale, deployment, coda type), runs
  a 9,999-permutation test and a secondary test across tag deployments, and calibrates both
  in synthetic "coda" and "bout" worlds laid on the real timeline. `--selftest` runs
  everything on a synthetic timeline only (`results/vowel/vowel_selftest.json`).
* `describe_vowels.py`: the label-blind join and structure description (job
  `vowel-describe-v1`).
* `test_vowel_results.py`: the grader, published 2026-11-20 before the analysis job had
  produced any result. It is standalone (stdlib only) and re-derives the verdict, Q, every p
  value's place on its permutation lattice, size and power, the matched eps, the predictions and
  the Brier score from the raw output, and it fixes the exact lines of `RESULTS-VOWEL.md`.
* `fetch_code.py`: the first step of job `vowel-test-v1`. It pins the analysis at the
  registration commit `eff4365` and stops unless the grader is public and identical.
* `results/vowel/vowel_results.json`: the raw output of job `vowel-test-v1` (2026-11-21),
  committed unchanged.
* `VOWEL2-PREREG.md`, `vowel2_test.py`, `test_vowel2_test.py`, `test_vowel2_results.py`,
  `gate.py`: test 2 (registration, analysis, unit tests, grader and renderer of
  `RESULTS-DUR.md`, and the job's first step, which stops unless these files are public and
  identical to the job's copies).
* `VOWEL3-PREREG.md`, `vowel3_test.py`, `test_vowel3_test.py`, `gate3.py`: test 3
  (registration; analysis, which also renders `RESULTS-COART.md`; unit tests; the job's first
  step).
* `test_vowel3_results.py`: the grader for test 3 (stdlib only; it imports `vowel3_test.py`
  only for an optional byte-for-byte comparison of `RESULTS-COART.md`). From the raw output
  `results/coart/vowel3_results.json` it re-derives the filter arithmetic, that pair, whale and
  deployment counts add up, every mismatch rate, Delta_first, Delta_last and their difference,
  every p value's place on its permutation lattice, the calibration rates as whole counts of
  200 worlds, the verdict, the LAST_CLICK flag, predictions P1-P6 and the Brier score, and checks
  them against the job's own grading. Until the result is committed its result tests are
  skipped; its toy tests always run.

## Reproduce
```
pip install numpy==2.1.3 diptest==0.12.0
python -m unittest -v test_vowel_test test_vowel2_test test_vowel3_test
python -m unittest -v test_vowel_results test_vowel2_results test_vowel3_results
python vowel_test.py --data-dir ./data --out-dir ./out
python test_vowel_results.py --render ./out/vowel_results.json ./out/RESULTS-VOWEL.md
python vowel2_test.py --data-dir ./data --out-dir ./out
python test_vowel2_results.py --render ./out/vowel2_results.json ./out/RESULTS-DUR.md
python vowel3_test.py --data-dir ./data --out-dir ./out
```
The data download from OSF (project a32ke, file 8jmp7), from
github.com/pratyushasharma/sw-combinatoriality and from github.com/Project-CETI/
coda-vowel-phonology, and they are checked by md5. Those repositories have no licence file, so
their tables are not redistributed here. Only aggregate counts are published.

## Credit
Claim and hand labels: Begus, Sprouse, Leban, Silva and Gero (2025, doi 10.1162/opmi.a.252);
Begus, Dabkowski, Sprouse, Gruber and Gero (2026, doi 10.1098/rspb.2025.2994); Project CETI
(github.com/Project-CETI/coda-vowel-phonology). Recording tables: Sharma et al. (2024) and the
Dominica Sperm Whale Project.
