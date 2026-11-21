# READING-VOWEL: what the graded coda-vowel persistence test says

MV2, Munim, Inc. (mv2@munimtech.com), 2026-11-21. Made with AI agents; no human expert has
checked this yet. Text CC BY 4.0. Written AFTER the result: it applies the readings fixed in
`VOWEL-PREREG.md` section 7 and adds nothing to the verdict. Every number below is copied from
`results/vowel/vowel_results.json` (job vowel-test-v1, 2026-11-21 03:52Z, code pinned at
eff43658502b31ac539877d201592452070a30c0) or from `RESULTS-VOWEL.md`, which the grader
`test_vowel_results.py` (published before the job ran) rendered and checked with no errors
(`check_result []`, `compare_job []`, `missing []`).

## Verdict

**VOWELS_CLUSTER_STRONGLY** (rule 3 of section 7: p_low <= 0.05 and Q <= 0.5).

- 1,134 hand-labelled codas (Begus et al. 2025, OSF a32ke), 13 whales, 19 tag deployments,
  94 bouts at a 60 s gap; 1,040 within-bout neighbouring pairs.
- Within bouts the vowel switched between neighbouring codas **75** times. Shuffling vowels
  within whale x deployment x coda type predicts **352.23** (null mean 352.17, sd 12.78, range
  306 to 397 in 9,999 permutations). Q = S/E = **0.2129**, p_low = **0.0001** (the smallest
  value 9,999 permutations can give).
- In plain words: 7.2% of within-bout neighbours differ in vowel (75 of 1,040), where the vowel
  mix of the same whale, deployment and coda type predicts about 34% (352 of 1,040).
- Calibration on the real timeline passed: independent-coda worlds rejected at 0.055 (11 of
  200; limit 0.10); bout worlds were detected 200 of 200 at eps 0.05, 0.10 and 0.20, and 185 of
  200 at eps 0.30.
- 6 of 7 registered predictions came true (Brier 0.114). The one that failed was Q7 (vowels
  alternate more than chance; prior 0.05): p_high = 1.0000. Q2 (at most half the expected
  switches) had a prior of only 0.40; it came true by a wide margin.

## Reading (section 7, strong clustering)

Neighbouring codas share their vowel far more often than the vowel mix predicts, with about a
fifth of the expected switches. As registered, the vowel label then behaves mostly like **a
state of the moment rather than an independent choice made coda by coda**. The test cannot say
which state that is: recording geometry (tag position, orientation, beam pattern), depth, or a
vocal register that the whale holds through a bout would all produce this. As registered, it is
**a strong constraint on the claim, not proof of an artefact.**

## Side readings (registered as side readings, never verdicts; exploratory)

- **Gap profile.** Persistence is strongest at the shortest gaps and fades with the silence:
  Q 0.158 at 0-10 s (49 switches in 926 pairs, 309.62 expected), 0.610 at 10-60 s (26 in 114),
  0.612 at 60-300 s (5 in 19), 0.909 beyond 300 s (16 in 37). Between bouts Q = 0.8150 (21
  switches in 56 pairs, 25.77 expected). This is the pattern the registration described for a
  slow state: "neighbouring codas will nearly always agree, and changes will gather at long
  silences."
- **Deployments of the same whale.** For the four whales with at least two usable deployments
  (FORK, JOCASTA, LAIUS, TBB; 10 deployments, 492 codas, 47 cells), the vowel mix differs
  between tag deployments of the same whale and coda type: G = 65.899 against a permutation
  null mean of 8.934 (95th percentile 17.127), p_dep = 0.0001. The same whale saying the same
  coda type has a different vowel mix on different days or tags.
- **Single-vowel strata.** Only 20 of the 96 whale x deployment x coda-type strata hold both
  vowels (791 of the 1,134 codas). In the other 76, every coda of that type on that deployment
  has the same vowel.
- **Every whale with switches points the same way.** For each of the 7 whales with more than 5
  expected switches, observed switches are below expected (ATWOOD 12 vs 142.54, FORK 26 vs
  100.91, PINCHY 18 vs 50.85, TBB 8 vs 33.21, LAIUS 2 vs 10.62, FRUIT 5 vs 5.80, SAM 3 vs 5.69);
  so is TWEAK (1 vs 2.60). FRUIT (Q 0.862) is the one whale near chance. Five whales (JOCASTA,
  LADYO, NALGENE, SOPH, SOURSOP) have no stratum holding both vowels, so no switch was possible.
- **Matched bout world.** Among simulated worlds with one vowel per bout and each coda flipped
  independently with probability eps, the observed Q (0.2129) is closest to eps = 0.05 (mean Q
  0.2663; R = 20 per eps, exploratory). The data look like "one vowel per bout, with roughly 1
  coda in 20 showing the other one".

## What this does and does not mean

- It does **not** show the vowels are artefacts. A whale could hold a vowel through a bout the
  way a speaker holds a register, and Begus et al. 2026 report coarticulation-like effects at
  coda edges that are compatible with that.
- It **does** mean that any test treating codas as independent draws of a vowel overstates how
  much evidence the data hold. The effective sample is closer to the number of bouts and
  deployments than to the number of codas. Claims about how vowels pair with coda types,
  durations or whales need tests that respect bouts and deployments.
- The deployment effect (the same whale and coda type, different vowel mix on different tags) is
  the observation most directly worth checking against tag position, depth and orientation
  records. Those records are not in the public files we used.

## Limits

- The labels are the authors' hand labels, made per whale with LPC settings tuned per whale.
  Persistence could come from the whale, the recording or the labelling. That includes any
  tendency of an annotator labelling a sequence to carry a judgement forward. We cannot separate
  these.
- Only focal-whale codas are labelled, so we cannot test whether two whales recorded on one tag
  share a vowel at the same moment. That would be the sharpest geometry test.
- The 60 s bout gap, the strata and the statistic were fixed before the data were read. The gap
  profile, per-whale table, deployment test and matching are side readings.
- 1,316 of 1,375 codamd rows matched a unique recording time in the public DSWP dialogue table
  (2 ambiguous, 53 unmatched); 1,134 of these were labelled, timed codas with a whale and
  deployment.
- The DSWP tables carry no licence, so they are read inside the job and not redistributed.

Credit: the data are from Project CETI and the Dominica Sperm Whale Project (Begus, Sprouse,
Leban, Silva & Gero 2025, Open Mind; Sharma et al. 2024, Nature Communications).
