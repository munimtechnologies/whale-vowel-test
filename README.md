# whale-vowel-test

An open, pre-registered test of whether sperm whale "coda vowels" are a property of each coda
or a state of the moment that persists through bouts and tag deployments.

MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents; no human expert has reviewed it
yet. Code Apache-2.0, text CC BY 4.0.

## Result (graded 2026-11-21)
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

## Reproduce
```
pip install numpy==2.1.3
python -m unittest -v test_vowel_test
python -m unittest -v test_vowel_results
python vowel_test.py --selftest --out-dir ./out
python vowel_test.py --data-dir ./data --out-dir ./out
python test_vowel_results.py --render ./out/vowel_results.json ./out/RESULTS-VOWEL.md
```
The data download from OSF (project a32ke, file 8jmp7) and from
github.com/pratyushasharma/sw-combinatoriality, and they are checked by md5. That repository
has no licence file, so its tables are not redistributed here. Only aggregate counts are
published.

## Credit
Claim and hand labels: Begus, Sprouse, Leban, Silva and Gero (2025, doi 10.1162/opmi.a.252);
Begus, Dabkowski, Sprouse, Gruber and Gero (2026, doi 10.1098/rspb.2025.2994); Project CETI.
Recording tables: Sharma et al. (2024) and the Dominica Sperm Whale Project.
