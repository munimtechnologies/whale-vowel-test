# VOWEL-PREREG: are sperm whale "coda vowels" a property of the coda or of the moment?

Pre-registration, MV2 of Munim, Inc. (mv2@munimtech.com), 2026-11-20. Made with AI agents; no
human expert has reviewed this design yet. Text CC BY 4.0, code Apache-2.0.

Registered before we computed any statistic of the vowel labels by group, time, bout,
deployment or whale. One label-blind job has run (`vowel-describe-v1`, `describe_vowels.py`).
It joined the labels to recording times and counted codas per whale, deployment, file and bout,
but it never read the label values (section 3). Code: `vowel_test.py` (tests
`test_vowel_test.py`). A grader will be published before the analysis job (`vowel-test-v1`) is
filed.

## 1. The claim
* Begus, Sprouse, Leban, Silva and Gero 2025, Open Mind 9:1849-1874 (doi 10.1162/opmi.a.252;
  data OSF a32ke): codas of Eastern Caribbean sperm whales come in two spectral "vowel"
  qualities, a (one spectral peak below 10 kHz) and i (two peaks). The qualities are discrete,
  recur across whales and coda types, and are not movement artefacts.
* Begus, Dabkowski, Sprouse, Gruber and Gero 2026, Proc R Soc B 293:20252994 (doi
  10.1098/rspb.2025.2994): the vowels pattern like human vowels. Durations differ by vowel, the
  qualities are distributed unevenly across coda types, and there is coarticulation-like
  mismatch at coda edges.
* Critics (Rendell in Science News; the "Sperm Whale Redux" essay on goflaw.substack) suggest
  the spectral peaks may reflect recording geometry: tag placement, the whale's orientation
  (beam pattern) and depth. The 2025 paper reports a correlation of about 0.59 between depth
  and the spectral peak.

## 2. What is new here
If the vowel is a choice made for each coda, as human vowels are, two neighbouring codas of one
whale, seconds apart in one bout, should differ in vowel about as often as the mix of vowels
in that deployment and coda type predicts. If the vowel instead reflects a slowly changing
state, such as tag position, orientation, depth, or a vocal "register" held through a bout,
neighbouring codas will nearly always agree, and changes will gather at long silences. Nobody
has measured this. Neither paper models time, bout or tag deployment, and a prior-art search
on 2026-11-20 found no test of vowel persistence within bouts or deployments. The measurement
below says how much of the vowel signal changes from coda to coda, with power measured in
synthetic worlds built on the real timeline.

## 3. Data and gates
* `codamd.csv` (OSF a32ke, file 8jmp7; md5 be50098e0e806d6df7cd2144b80d900d): the paper's hand
  vowel labels (`handv`), whale, coda type and duration for 1,375 codas.
* `DominicaCodas.csv` (md5 46c2ff249bc6fa327d5bbe596f06be63) and `sperm-whale-dialogues.csv`
  (md5 eeeeb20cda64d88320b6ccee1185379a) from github.com/pratyushasharma/sw-combinatoriality
  (Sharma et al. 2024, Dominica Sperm Whale Project). They are joined exactly as in
  `describe_vowels.py`: codamd `codanum` = `codaNUM2018` with equal duration, then a unique
  exact match on click count, duration and inter-click intervals gives the DTAG recording
  (`REC`), whose prefix is the tag deployment and file, and the time `TsTo`. That repository
  has no licence file, so these tables are read inside the job and never redistributed. Only
  aggregate counts are published.
* What the label-blind description found: 1,142 labelled codas (a or i) of named whales,
  1,134 of them with a deployment and time. There are 13 whales and 19 whale-deployments, and
  4 whales have 2 or 3 deployments (FORK 3, TBB 3, JOCASTA 2, LAIUS 2). With 60-s gaps, the
  codas form 94 bouts.
* G1: all three md5 match, or the job stops with DATA_MISMATCH and computes nothing.
* G2: at least 200 within-bout pairs (section 4) and a positive expected switch count, or the
  verdict is INSUFFICIENT_DATA.

## 4. Units and statistic
* Units: codas with `handv` equal to `a` or `i`, a whale name, a unique timing match (the
  `dialogue` join), a time and a deployment. Label y = 1 for a, 0 for i. Coda type is codamd's
  `codatype` (as given, including the `-NOISE` types).
* Order: within each whale, deployment and file (the `REC` prefix before `_`), by time, then
  coda number. Consecutive codas in this order form a pair. A pair is "within-bout" if the gap
  is at most 60 s and "between-bout" otherwise. There are no pairs across files, deployments
  or whales, which makes the analysis safe whether `TsTo` counts from the file or from the
  deployment.
* S = the number of within-bout pairs whose two labels differ (switches).
* E = the expected S when labels are shuffled within (whale, deployment, coda type) strata,
  computed exactly: 2k(n-k)/(n(n-1)) for a pair in one stratum, and pa(1-pb)+(1-pa)pb for a
  pair across strata.
* Q = S / E. Q = 1 means neighbours switch as often as composition predicts, and Q = 0 means
  vowels never change within a bout.

## 5. Tests
* PRIMARY: permute labels within (whale, deployment, coda type) strata, B = 9,999, seed
  20261201. p_low = (1 + #{S_null <= S}) / (B + 1), one-sided toward clustering. p_high (the
  same with >=) is reported as a side reading on alternation.
* SECONDARY, deployment: for whales with at least 2 deployments of 10 or more units each, G =
  the sum over (whale, coda type) strata of the likelihood-ratio G statistic of label by
  deployment. Labels are permuted within (whale, coda type) across deployments, B = 9,999,
  seed 20261202, and p_dep = (1 + #{G_null >= G - tol}) / (B + 1). A small p_dep means
  vowels differ between tag deployments of the same whale beyond their coda-type mix.
* Between-bout switches and their expectation are computed the same way.
* Gap profile (exploratory): switches and expectation for pairs with gaps of 0-10 s, 10-60 s,
  60-300 s and over 300 s.
* Per-whale S and E (exploratory).

## 6. Calibration on the real timeline (same units, strata, pairs)
* Coda world (null): each unit's label is drawn independently with its stratum's observed
  share of a. R = 200 sets, B = 999, seed 20261203. size = share with p_low <= 0.05.
* Bout world (alternative): bouts = runs within whale, deployment and file split at gaps over
  60 s. Each bout draws one base label with its (whale, deployment) share of a, and each coda
  flips it independently with probability eps. eps = 0.05, 0.10, 0.20, 0.30. R = 200 sets per
  eps, B = 999, seeds 20261204 + index. power(eps) = share with p_low <= 0.05.
* Matching (exploratory): eps = 0.00, 0.05, ..., 0.50, with 20 sets each (seed 20261205 +
  index). Mean Q is computed with each set's own exact E, and the matched eps is the one whose
  mean Q is closest to the observed Q (ties go to the smaller eps). This reads as "the observed
  persistence is like a bout state that flips on a fraction eps of codas".

## 7. Decision rules (coded in verdict_of, applied in order)
1. Fewer than 200 within-bout pairs, or E <= 0: INSUFFICIENT_DATA.
2. size > 0.10 or undefined: CALIBRATION_FAILED.
3. p_low <= 0.05 and Q <= 0.5: VOWELS_CLUSTER_STRONGLY.
4. p_low <= 0.05 and Q > 0.5: VOWELS_CLUSTER_WEAKLY.
5. power(0.20) >= 0.80: NO_CLUSTERING_WITH_POWER.
6. Otherwise: UNDERPOWERED.

Readings fixed now:
* CLUSTER_STRONGLY: within one bout, neighbouring codas seconds apart share a vowel much more
  often than the deployment's vowel mix predicts, with at most half of the expected switches.
  The "vowel" then behaves mostly like a state of the moment (recording geometry, depth, or a
  register held through a bout), not like a free choice per coda. This test cannot say which
  kind of state it is. It would be stated as a strong constraint on the claim, not as proof
  of an artefact.
* CLUSTER_WEAKLY: vowels persist somewhat but still change often within bouts. Both coda-level
  and state-level sources contribute.
* NO_CLUSTERING_WITH_POWER: vowels change between neighbouring codas as freely as composition
  predicts, and a bout state with 20% flips would very likely have been detected. That is
  evidence against slow recording artefacts and supports a coda-level vowel, as the authors
  propose.
* UNDERPOWERED: these data cannot tell the two apart.
* Side readings, never verdicts: p_dep (do vowels differ between tag deployments of the same
  whale?), p_high <= 0.05 (vowels alternate more than chance), the gap profile (do switches
  gather at long silences?), and the matched eps.

## 8. Predictions (priors, Brier-scored)
Q1 p_low <= 0.05: 0.70. Q2 Q <= 0.5: 0.40. Q3 p_dep <= 0.05: 0.55. Q4 power(0.20) >= 0.80:
0.85. Q5 size <= 0.10: 0.97. Q6 the between-bout switch share (S_between / between-bout pairs)
exceeds the within-bout share (S / within-bout pairs): 0.65. Q7 p_high <= 0.05: 0.05.

## 9. Limits known now
* The labels are the authors' hand labels, made per whale with LPC settings tuned per whale.
  Persistence could come from the whale, the recording or the labelling. A strong clustering
  result therefore constrains the claim but does not identify the source.
* Only focal-whale codas are labelled, so we cannot test whether two whales recorded on the
  same tag at the same moment share a vowel.
* Within-stratum permutation treats coda types as fixed. If coda types themselves come in runs,
  that is conditioned on, not tested.
* The join depends on exact timing matches in a second public dataset (1,316 of 1,375 codas
  matched uniquely).
* Credit: data and claim by Begus, Sprouse, Leban, Silva, Gero, Dabkowski and Gruber (Project
  CETI) and the Dominica Sperm Whale Project. Timing tables by Sharma et al. 2024.

## 10. Order of work
Pre-registration (this file), code with tests, then a grader published before the analysis
job is filed, then RESULTS-VOWEL.md. This file is never edited after publication. Changes go
into an AMENDMENT section of a new file.
