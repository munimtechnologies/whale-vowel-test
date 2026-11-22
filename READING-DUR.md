# READING-DUR: what the within-bout duration test found

Written 2026-11-22, after the result, by AI agents working in MV2's name (MV2, Munim, Inc.,
mv2@munimtech.com). A post-hoc reading of `RESULTS-DUR.md` and `results/vowel2/vowel2_results.json`,
written by job `vowel2-test-v1` with the code and rules registered in `VOWEL2-PREREG.md`. Not yet
checked by a human expert. Text CC BY 4.0.

## The registered verdict

**CALIBRATION_FAILED_WITHIN_BOUTS** (5 of 8 predictions true, Brier 0.313). The primary test
(vowel labels permuted within bouts) rejected in 0.190 of the 200 worlds in which the effect had
been removed and the labels rotated within bouts (runs kept), above the registered 0.10. By the
registered rule the within-bout p value is not interpreted as a test.

## What the numbers still show (descriptive, post hoc)

* **The published contrast reproduces.** a-codas are longer than i-codas within each whale:
  D = +0.1399 s on 628 codas of the published subset (p_high 0.0001 under the paper's
  independence assumption).
* **That test is not calibrated for bouts.** In worlds where vowels come in bouts and have no
  link to duration, the published-style test said "a longer" in 0.355 of worlds and gave a
  significant result in either direction in 0.550. The within-bout test said "a longer" in 0.045.
* **Most of the difference survives inside bouts.** In the 20 bouts that hold both vowels
  (105 minority-vowel codas), D = +0.1136 s, 81% of the within-whale value; within tag
  deployments D = +0.1349 s. The run-keeping rotation test at the bout level also gave p 0.0001.
  Because the size check failed, we report these as estimates, not as a calibrated test.
* **"Long i" and "short i" are states of the bout.** Splitting each whale's i-codas at its
  two-means threshold, neighbouring i-codas in a bout switched between short and long 22 times
  where 113.85 switches were expected (Q 0.193, p_low 0.0001). Dip tests found two modes for
  ATWOOD (p 0.014), FORK (p < 0.001) and TBB (p 0.016), not PINCHY (p 0.991). The mix did not
  differ clearly between FORK's three deployments (p 0.094).

## Reading

The length-vowel dependency is not just a between-bout artefact: a-codas are about 0.11 s longer
than i-codas even inside the same bout. But the published p values, which count every coda as
independent, would also have been "significant" in about a third of worlds with no vowel effect.
The short/long i contrast behaves like the vowels themselves: it holds for long stretches of a
bout and changes rarely. Like our first test (VOWELS_CLUSTER_STRONGLY), this does not show that
the vowels are artefacts; it shows that the evidence comes in bout-sized pieces, so the number
of independent observations is the number of bouts, not codas.

Why calibration failed (our reading): coda durations drift slowly within a bout ("rubato"), and
a label permutation breaks the runs of one vowel that sit on these drifting stretches. A
run-keeping null, such as the rotation p that was also computed, is the natural primary test for
a future registered amendment.

## Limits

* Hand labels of the authors; focal-whale codas only; four whales, eight deployments.
* The paper's mixed model was replaced by a permutation stand-in with the same independence
  assumption.
* Carried out with AI agents working in MV2's name; no human expert has checked it yet.
